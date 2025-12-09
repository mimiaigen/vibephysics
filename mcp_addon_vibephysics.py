# VibePhysics MCP Addon - Connect Blender to Claude via MCP
#
# INSTALLATION:
#   1. Install this addon in Blender (Edit > Preferences > Add-ons > Install)
#   2. In the VibePhysicsMCP panel, set the path to your vibephysics folder
#   3. Click "Set Path & Reload" to load vibephysics

import bpy
import mathutils
import json
import threading
import socket
import time
import traceback
import io
import sys
from bpy.props import IntProperty, StringProperty, BoolProperty
from contextlib import redirect_stdout

bl_info = {
    "name": "VibePhysics MCP",
    "author": "VibePhysics",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > VibePhysicsMCP",
    "description": "Connect Blender to Claude via MCP with VibePhysics integration",
    "category": "Interface",
}

# =============================================================================
# VibePhysics Import
# =============================================================================
import os

_vibephysics_imported = False
_vibephysics_error = None
_vibephysics_path = ""

def setup_vibephysics_path(user_path):
    """Add vibephysics source path to Python path.
    
    Args:
        user_path: Path to vibephysics folder (containing 'src' subfolder)
    """
    global _vibephysics_path
    
    if not user_path or not os.path.exists(user_path):
        return False
    
    # Check if it's the vibephysics folder (has src/vibephysics)
    src_path = os.path.join(user_path, "src")
    if os.path.exists(src_path) and src_path not in sys.path:
        sys.path.insert(0, src_path)
        _vibephysics_path = src_path
        print(f"Added vibephysics path: {src_path}")
        return True
    
    # Maybe user selected the src folder directly
    if os.path.exists(os.path.join(user_path, "vibephysics")) and user_path not in sys.path:
        sys.path.insert(0, user_path)
        _vibephysics_path = user_path
        print(f"Added vibephysics path: {user_path}")
        return True
    
    return False

def ensure_vibephysics():
    """Ensure vibephysics is imported. Returns True if successful."""
    global _vibephysics_imported, _vibephysics_error
    
    # Always try to import (don't cache failures)
    try:
        import vibephysics
        if not _vibephysics_imported:
            print("✓ VibePhysics loaded successfully")
        _vibephysics_imported = True
        _vibephysics_error = None
        return True
    except ImportError as e:
        _vibephysics_imported = False
        _vibephysics_error = str(e)
        print(f"✗ Could not import vibephysics: {e}")
        print("  Install with: pip install vibephysics")
        return False

# Try to import on load
ensure_vibephysics()


class BlenderMCPServer:
    def __init__(self, host='localhost', port=9876):
        self.host = host
        self.port = port
        self.running = False
        self.socket = None
        self.server_thread = None

    def start(self):
        if self.running:
            print("Server is already running")
            return

        self.running = True

        try:
            # Create socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)

            # Start server thread
            self.server_thread = threading.Thread(target=self._server_loop)
            self.server_thread.daemon = True
            self.server_thread.start()

            print(f"VibePhysics MCP server started on {self.host}:{self.port}")
        except Exception as e:
            print(f"Failed to start server: {str(e)}")
            self.stop()

    def stop(self):
        self.running = False

        # Close socket
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None

        # Wait for thread to finish
        if self.server_thread:
            try:
                if self.server_thread.is_alive():
                    self.server_thread.join(timeout=1.0)
            except:
                pass
            self.server_thread = None

        print("VibePhysics MCP server stopped")

    def _server_loop(self):
        """Main server loop in a separate thread"""
        print("Server thread started")
        self.socket.settimeout(1.0)

        while self.running:
            try:
                try:
                    client, address = self.socket.accept()
                    print(f"Connected to client: {address}")

                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client,)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Error accepting connection: {str(e)}")
                    time.sleep(0.5)
            except Exception as e:
                print(f"Error in server loop: {str(e)}")
                if not self.running:
                    break
                time.sleep(0.5)

        print("Server thread stopped")

    def _handle_client(self, client):
        """Handle connected client"""
        print("Client handler started")
        client.settimeout(None)
        buffer = b''

        try:
            while self.running:
                try:
                    data = client.recv(8192)
                    if not data:
                        print("Client disconnected")
                        break

                    buffer += data
                    try:
                        command = json.loads(buffer.decode('utf-8'))
                        buffer = b''

                        def execute_wrapper():
                            try:
                                response = self.execute_command(command)
                                response_json = json.dumps(response)
                                try:
                                    client.sendall(response_json.encode('utf-8'))
                                except:
                                    print("Failed to send response - client disconnected")
                            except Exception as e:
                                print(f"Error executing command: {str(e)}")
                                traceback.print_exc()
                                try:
                                    error_response = {
                                        "status": "error",
                                        "message": str(e)
                                    }
                                    client.sendall(json.dumps(error_response).encode('utf-8'))
                                except:
                                    pass
                            return None

                        bpy.app.timers.register(execute_wrapper, first_interval=0.0)
                    except json.JSONDecodeError:
                        pass
                except Exception as e:
                    print(f"Error receiving data: {str(e)}")
                    break
        except Exception as e:
            print(f"Error in client handler: {str(e)}")
        finally:
            try:
                client.close()
            except:
                pass
            print("Client handler stopped")

    def execute_command(self, command):
        """Execute a command in the main Blender thread"""
        try:
            return self._execute_command_internal(command)
        except Exception as e:
            print(f"Error executing command: {str(e)}")
            traceback.print_exc()
            return {"status": "error", "message": str(e)}

    def _execute_command_internal(self, command):
        """Internal command execution with proper context"""
        cmd_type = command.get("type")
        params = command.get("params", {})

        # Build handlers dictionary
        handlers = self._get_handlers()

        handler = handlers.get(cmd_type)
        if handler:
            try:
                print(f"Executing handler for {cmd_type}")
                result = handler(**params)
                print(f"Handler execution complete")
                return {"status": "success", "result": result}
            except Exception as e:
                print(f"Error in handler: {str(e)}")
                traceback.print_exc()
                return {"status": "error", "message": str(e)}
        else:
            return {"status": "error", "message": f"Unknown command type: {cmd_type}"}

    def _get_handlers(self):
        """Build and return all available handlers."""
        # Core Blender handlers (always available)
        handlers = {
            # Core
            "get_scene_info": self.get_scene_info,
            "get_object_info": self.get_object_info,
            "get_viewport_screenshot": self.get_viewport_screenshot,
            "execute_code": self.execute_code,
            "list_available_commands": self.list_available_commands,
            
            # =================================================================
            # VIBEPHYSICS SETUP MODULE
            # =================================================================
            # Scene
            "vp_init_simulation": self.vp_init_simulation,
            "vp_init_gsplat_scene": self.vp_init_gsplat_scene,
            "vp_clear_scene": self.vp_clear_scene,
            "vp_configure_physics_cache": self.vp_configure_physics_cache,
            "vp_set_frame_range": self.vp_set_frame_range,
            "vp_get_frame_range": self.vp_get_frame_range,
            "vp_set_current_frame": self.vp_set_current_frame,
            "vp_get_current_frame": self.vp_get_current_frame,
            "vp_reset_viewport": self.vp_reset_viewport,
            "vp_set_render_resolution": self.vp_set_render_resolution,
            "vp_set_render_engine": self.vp_set_render_engine,
            "vp_set_output_path": self.vp_set_output_path,
            
            # Import/Export
            "vp_load_asset": self.vp_load_asset,
            "vp_save_blend": self.vp_save_blend,
            "vp_export_selected": self.vp_export_selected,
            "vp_ensure_collection": self.vp_ensure_collection,
            "vp_move_to_collection": self.vp_move_to_collection,
            
            # Gaussian Splatting
            "vp_load_gsplat": self.vp_load_gsplat,
            "vp_load_3dgs": self.vp_load_3dgs,
            "vp_load_4dgs_sequence": self.vp_load_4dgs_sequence,
            "vp_setup_gsplat_display": self.vp_setup_gsplat_display,
            "vp_get_gsplat_info": self.vp_get_gsplat_info,
            
            # Viewport
            "vp_setup_dual_viewport": self.vp_setup_dual_viewport,
            "vp_reset_viewport_single": self.vp_reset_viewport_single,
            "vp_configure_viewport_shading": self.vp_configure_viewport_shading,
            
            # =================================================================
            # VIBEPHYSICS FOUNDATION MODULE
            # =================================================================
            # Physics
            "vp_setup_rigid_body_world": self.vp_setup_rigid_body_world,
            "vp_create_buoyancy_field": self.vp_create_buoyancy_field,
            "vp_create_underwater_currents": self.vp_create_underwater_currents,
            "vp_setup_ground_physics": self.vp_setup_ground_physics,
            "vp_bake_all": self.vp_bake_all,
            
            # Water
            "vp_create_visual_water": self.vp_create_visual_water,
            "vp_create_flat_surface": self.vp_create_flat_surface,
            "vp_setup_dynamic_paint_interaction": self.vp_setup_dynamic_paint_interaction,
            "vp_create_puddle_water": self.vp_create_puddle_water,
            
            # Ground
            "vp_create_seabed": self.vp_create_seabed,
            "vp_create_uneven_ground": self.vp_create_uneven_ground,
            "vp_create_bucket_container": self.vp_create_bucket_container,
            "vp_create_ground_cutter": self.vp_create_ground_cutter,
            
            # Objects
            "vp_make_object_floatable": self.vp_make_object_floatable,
            "vp_create_floating_sphere": self.vp_create_floating_sphere,
            "vp_generate_scattered_positions": self.vp_generate_scattered_positions,
            "vp_create_falling_spheres": self.vp_create_falling_spheres,
            "vp_create_falling_cubes": self.vp_create_falling_cubes,
            "vp_create_waypoint_markers": self.vp_create_waypoint_markers,
            
            # Lighting
            "vp_setup_lighting": self.vp_setup_lighting,
            "vp_create_caustics_light": self.vp_create_caustics_light,
            "vp_create_underwater_volume": self.vp_create_underwater_volume,
            
            # Trajectory
            "vp_create_circular_path": self.vp_create_circular_path,
            "vp_create_waypoint_path": self.vp_create_waypoint_path,
            "vp_create_waypoint_pattern": self.vp_create_waypoint_pattern,
            
            # Robot
            "vp_load_rigged_robot": self.vp_load_rigged_robot,
            "vp_setup_collision_meshes": self.vp_setup_collision_meshes,
            "vp_animate_walking": self.vp_animate_walking,
            
            # =================================================================
            # VIBEPHYSICS ANNOTATION MODULE
            # =================================================================
            "vp_create_bbox_annotation": self.vp_create_bbox_annotation,
            "vp_create_motion_trail": self.vp_create_motion_trail,
            "vp_create_motion_trails": self.vp_create_motion_trails,
            "vp_setup_point_tracking": self.vp_setup_point_tracking,
            "vp_quick_annotate": self.vp_quick_annotate,
            
            # =================================================================
            # VIBEPHYSICS CAMERA MODULE
            # =================================================================
            "vp_create_center_cameras": self.vp_create_center_cameras,
            "vp_create_following_camera": self.vp_create_following_camera,
            "vp_create_mounted_cameras": self.vp_create_mounted_cameras,
        }
        
        return handlers

    # =========================================================================
    # CORE BLENDER HANDLERS
    # =========================================================================
    
    def list_available_commands(self):
        """List all available commands grouped by category."""
        handlers = self._get_handlers()
        
        # Group by prefix
        core = []
        setup = []
        foundation = []
        annotation = []
        camera = []
        
        for name in sorted(handlers.keys()):
            if name.startswith("vp_"):
                # Categorize by function
                if any(x in name for x in ["init_", "clear_", "frame", "viewport", "render", "output", "load_asset", "save_", "export", "collection", "gsplat"]):
                    setup.append(name)
                elif any(x in name for x in ["rigid", "buoyancy", "current", "ground", "physics", "bake", "water", "seabed", "bucket", "cutter", "float", "sphere", "cube", "scatter", "marker", "lighting", "caustic", "volume", "path", "waypoint", "robot", "collision", "walking"]):
                    foundation.append(name)
                elif any(x in name for x in ["bbox", "trail", "tracking", "annotate"]):
                    annotation.append(name)
                elif any(x in name for x in ["camera"]):
                    camera.append(name)
                else:
                    foundation.append(name)  # Default to foundation
            else:
                core.append(name)
        
        return {
            "core": core,
            "setup": setup,
            "foundation": foundation,
            "annotation": annotation,
            "camera": camera,
            "total_commands": len(handlers)
        }

    def get_scene_info(self):
        """Get information about the current Blender scene"""
        try:
            scene_info = {
                "name": bpy.context.scene.name,
                "object_count": len(bpy.context.scene.objects),
                "objects": [],
                "materials_count": len(bpy.data.materials),
                "frame_start": bpy.context.scene.frame_start,
                "frame_end": bpy.context.scene.frame_end,
                "frame_current": bpy.context.scene.frame_current,
            }

            for i, obj in enumerate(bpy.context.scene.objects):
                if i >= 20:
                    break

                obj_info = {
                    "name": obj.name,
                    "type": obj.type,
                    "location": [round(float(obj.location.x), 2),
                                round(float(obj.location.y), 2),
                                round(float(obj.location.z), 2)],
                }
                scene_info["objects"].append(obj_info)

            return scene_info
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def _get_aabb(obj):
        """Returns the world-space AABB of an object."""
        if obj.type != 'MESH':
            raise TypeError("Object must be a mesh")

        local_bbox_corners = [mathutils.Vector(corner) for corner in obj.bound_box]
        world_bbox_corners = [obj.matrix_world @ corner for corner in local_bbox_corners]
        min_corner = mathutils.Vector(map(min, zip(*world_bbox_corners)))
        max_corner = mathutils.Vector(map(max, zip(*world_bbox_corners)))

        return [[*min_corner], [*max_corner]]

    def get_object_info(self, name):
        """Get detailed information about a specific object"""
        obj = bpy.data.objects.get(name)
        if not obj:
            raise ValueError(f"Object not found: {name}")

        obj_info = {
            "name": obj.name,
            "type": obj.type,
            "location": [obj.location.x, obj.location.y, obj.location.z],
            "rotation": [obj.rotation_euler.x, obj.rotation_euler.y, obj.rotation_euler.z],
            "scale": [obj.scale.x, obj.scale.y, obj.scale.z],
            "visible": obj.visible_get(),
            "materials": [],
        }

        if obj.type == "MESH":
            bounding_box = self._get_aabb(obj)
            obj_info["world_bounding_box"] = bounding_box

        for slot in obj.material_slots:
            if slot.material:
                obj_info["materials"].append(slot.material.name)

        if obj.type == 'MESH' and obj.data:
            mesh = obj.data
            obj_info["mesh"] = {
                "vertices": len(mesh.vertices),
                "edges": len(mesh.edges),
                "polygons": len(mesh.polygons),
            }

        return obj_info

    def get_viewport_screenshot(self, max_size=800, filepath=None, format="png"):
        """Capture a screenshot of the current 3D viewport"""
        try:
            if not filepath:
                return {"error": "No filepath provided"}

            area = None
            for a in bpy.context.screen.areas:
                if a.type == 'VIEW_3D':
                    area = a
                    break

            if not area:
                return {"error": "No 3D viewport found"}

            with bpy.context.temp_override(area=area):
                bpy.ops.screen.screenshot_area(filepath=filepath)

            img = bpy.data.images.load(filepath)
            width, height = img.size

            if max(width, height) > max_size:
                scale = max_size / max(width, height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                img.scale(new_width, new_height)
                img.file_format = format.upper()
                img.save()
                width, height = new_width, new_height

            bpy.data.images.remove(img)

            return {
                "success": True,
                "width": width,
                "height": height,
                "filepath": filepath
            }
        except Exception as e:
            return {"error": str(e)}

    def execute_code(self, code):
        """Execute arbitrary Blender Python code"""
        try:
            namespace = {"bpy": bpy}
            
            # Auto-import vibephysics if needed
            if "vibephysics" in code or "vp." in code:
                ensure_vibephysics()
                import vibephysics
                namespace["vibephysics"] = vibephysics
                namespace["vp"] = vibephysics

            capture_buffer = io.StringIO()
            with redirect_stdout(capture_buffer):
                exec(code, namespace)

            captured_output = capture_buffer.getvalue()
            return {"executed": True, "result": captured_output}
        except Exception as e:
            raise Exception(f"Code execution error: {str(e)}")

    # =========================================================================
    # VIBEPHYSICS SETUP HANDLERS
    # =========================================================================
    
    def vp_init_simulation(self, start_frame=1, end_frame=250, physics_config=None, clear=True):
        """Initialize simulation scene."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics import setup
        setup.init_simulation(start_frame, end_frame, physics_config, clear)
        return {"success": True, "frame_range": [start_frame, end_frame]}

    def vp_init_gsplat_scene(self, gsplat_path, start_frame=1, collection_name="GaussianSplat", clear=True):
        """Initialize scene for Gaussian Splatting."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics import setup
        result = setup.init_gsplat_scene(gsplat_path, start_frame, collection_name, clear)
        return {"success": True, "result_type": type(result).__name__ if result else None}

    def vp_clear_scene(self):
        """Clear the scene."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics import setup
        setup.clear_scene()
        return {"success": True}

    def vp_configure_physics_cache(self, start_frame, end_frame, substeps=20, solver_iters=20, cache_buffer=50):
        """Configure physics cache settings."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics import setup
        setup.configure_physics_cache(start_frame, end_frame, substeps, solver_iters, cache_buffer)
        return {"success": True}

    def vp_set_frame_range(self, start_frame, end_frame):
        """Set animation frame range."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics import setup
        setup.set_frame_range(start_frame, end_frame)
        return {"success": True}

    def vp_get_frame_range(self):
        """Get current frame range."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics import setup
        start, end = setup.get_frame_range()
        return {"start_frame": start, "end_frame": end}

    def vp_set_current_frame(self, frame):
        """Set current frame."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics import setup
        setup.set_current_frame(frame)
        return {"success": True, "frame": frame}

    def vp_get_current_frame(self):
        """Get current frame."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics import setup
        return {"frame": setup.get_current_frame()}

    def vp_reset_viewport(self):
        """Reset viewport to single view."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics import setup
        setup.reset_viewport()
        return {"success": True}

    def vp_set_render_resolution(self, width, height, percentage=100):
        """Set render resolution."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics import setup
        setup.set_render_resolution(width, height, percentage)
        return {"success": True}

    def vp_set_render_engine(self, engine='CYCLES'):
        """Set render engine."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics import setup
        setup.set_render_engine(engine)
        return {"success": True, "engine": engine}

    def vp_set_output_path(self, path):
        """Set render output path."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics import setup
        setup.set_output_path(path)
        return {"success": True, "path": path}

    def vp_load_asset(self, filepath, transform=None, collection_name=None):
        """Load a 3D asset (auto-detects format)."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics import setup
        result = setup.load_asset(filepath, transform, collection_name)
        if result:
            return {"success": True, "object_name": result.name if hasattr(result, 'name') else str(result)}
        return {"success": False, "error": "Failed to load asset"}

    def vp_save_blend(self, filepath=None):
        """Save the blend file."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics import setup
        setup.save_blend(filepath)
        return {"success": True, "filepath": filepath}

    def vp_export_selected(self, filepath, export_type=None):
        """Export selected objects."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics import setup
        setup.export_selected(filepath, export_type)
        return {"success": True, "filepath": filepath}

    def vp_ensure_collection(self, name, parent=None):
        """Ensure a collection exists."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics import setup
        collection = setup.ensure_collection(name, parent)
        return {"success": True, "collection_name": collection.name}

    def vp_move_to_collection(self, object_name, collection_name):
        """Move an object to a collection."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics import setup
        obj = bpy.data.objects.get(object_name)
        if not obj:
            return {"error": f"Object not found: {object_name}"}
        setup.move_to_collection(obj, collection_name)
        return {"success": True}

    def vp_load_gsplat(self, path, collection_name="GaussianSplat", frame_start=1, setup_animation=True):
        """Load Gaussian splat (3DGS or 4DGS)."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics import setup
        result = setup.load_gsplat(path, collection_name, frame_start, setup_animation)
        return {"success": True, "result_type": type(result).__name__ if result else None}

    def vp_load_3dgs(self, filepath, name=None):
        """Load a single 3DGS PLY file."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics import setup
        obj = setup.load_3dgs(filepath, name)
        return {"success": True, "object_name": obj.name if obj else None}

    def vp_load_4dgs_sequence(self, folder_path, prefix="", suffix=".ply", collection_name="GaussianSplat"):
        """Load a 4DGS sequence from a folder."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics import setup
        collection = setup.load_4dgs_sequence(folder_path, prefix, suffix, collection_name)
        return {"success": True, "collection_name": collection.name if collection else None}

    def vp_setup_gsplat_display(self, object_name, point_size=0.01, use_vertex_colors=True):
        """Setup Gaussian splat display."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics import setup
        obj = bpy.data.objects.get(object_name)
        if not obj:
            return {"error": f"Object not found: {object_name}"}
        setup.setup_gsplat_display(obj, point_size, use_vertex_colors)
        return {"success": True}

    def vp_get_gsplat_info(self, object_name):
        """Get information about a Gaussian splat."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics import setup
        obj = bpy.data.objects.get(object_name)
        if not obj:
            return {"error": f"Object not found: {object_name}"}
        return setup.get_gsplat_info(obj)

    def vp_setup_dual_viewport(self, annotation_objects=None):
        """Setup dual viewport with local view for annotations."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics import setup
        objs = None
        if annotation_objects:
            objs = [bpy.data.objects.get(name) for name in annotation_objects if bpy.data.objects.get(name)]
        setup.setup_dual_viewport(objs)
        return {"success": True}

    def vp_reset_viewport_single(self):
        """Reset to single viewport."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics import setup
        setup.reset_viewport_single()
        return {"success": True}

    def vp_configure_viewport_shading(self, shading_type='SOLID', use_scene_lights=True):
        """Configure viewport shading."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics.setup import viewport
        viewport.configure_viewport_shading(shading_type=shading_type, use_scene_lights=use_scene_lights)
        return {"success": True}

    # =========================================================================
    # VIBEPHYSICS FOUNDATION HANDLERS
    # =========================================================================

    def vp_setup_rigid_body_world(self, substeps=60, solver_iters=60):
        """Setup rigid body physics world."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics.foundation import physics
        physics.setup_rigid_body_world(substeps, solver_iters)
        return {"success": True}

    def vp_create_buoyancy_field(self, z_bottom, z_surface, strength, flow=0.5, spawn_radius=2.0, hide=True):
        """Create buoyancy force field."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics.foundation import physics
        physics.create_buoyancy_field(z_bottom, z_surface, strength, flow, spawn_radius, hide)
        return {"success": True}

    def vp_create_underwater_currents(self, z_bottom, z_surface, strength, turbulence_scale, spawn_radius=2.0, hide=True):
        """Create underwater currents."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics.foundation import physics
        physics.create_underwater_currents(z_bottom, z_surface, strength, turbulence_scale, spawn_radius, hide)
        return {"success": True}

    def vp_setup_ground_physics(self, ground_object_name, friction=0.9, restitution=0.1):
        """Setup ground physics."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics.foundation import physics
        obj = bpy.data.objects.get(ground_object_name)
        if not obj:
            return {"error": f"Object not found: {ground_object_name}"}
        physics.setup_ground_physics(obj, friction, restitution)
        return {"success": True}

    def vp_bake_all(self):
        """Bake all physics."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics.foundation import physics
        physics.bake_all()
        return {"success": True}

    def vp_create_visual_water(self, scale, wave_scale, radius=None, time=None, start_frame=1, end_frame=250):
        """Create visual water surface."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics.foundation import water
        result = water.create_visual_water(scale, wave_scale, radius, time, start_frame, end_frame)
        return {"success": True, "object_name": result.name if result else None}

    def vp_create_flat_surface(self, size, z_level, subdivisions=200, name="Water_Visual"):
        """Create a flat water surface."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics.foundation import water
        result = water.create_flat_surface(size, z_level, subdivisions, name)
        return {"success": True, "object_name": result.name if result else None}

    def vp_setup_dynamic_paint_interaction(self, water_object_name, brush_object_names, ripple_strength):
        """Setup dynamic paint water interaction."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics.foundation import water
        water_obj = bpy.data.objects.get(water_object_name)
        if not water_obj:
            return {"error": f"Water object not found: {water_object_name}"}
        brush_objs = [bpy.data.objects.get(name) for name in brush_object_names if bpy.data.objects.get(name)]
        water.setup_dynamic_paint_interaction(water_obj, brush_objs, ripple_strength)
        return {"success": True}

    def vp_create_puddle_water(self, z_level, size, ground_cutter_name=None, color=None):
        """Create puddle water."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics.foundation import water
        cutter = bpy.data.objects.get(ground_cutter_name) if ground_cutter_name else None
        result = water.create_puddle_water(z_level, size, cutter, color)
        return {"success": True, "object_name": result.name if result else None}

    def vp_create_seabed(self, z_bottom, size=100):
        """Create seabed."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics.foundation import ground
        result = ground.create_seabed(z_bottom, size)
        return {"success": True, "object_name": result.name if result else None}

    def vp_create_uneven_ground(self, z_base, size, noise_scale=10.0, strength=2.0):
        """Create uneven ground terrain."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics.foundation import ground
        result = ground.create_uneven_ground(z_base, size, noise_scale, strength)
        return {"success": True, "object_name": result.name if result else None}

    def vp_create_bucket_container(self, z_bottom, z_surface, radius, wall_thickness=0.2):
        """Create bucket container."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics.foundation import ground
        result = ground.create_bucket_container(z_bottom, z_surface, radius, wall_thickness)
        return {"success": True, "object_name": result.name if result else None}

    def vp_create_ground_cutter(self, terrain_object_name, thickness=10.0, offset=-1.0):
        """Create ground cutter for boolean operations."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics.foundation import ground
        terrain = bpy.data.objects.get(terrain_object_name)
        if not terrain:
            return {"error": f"Terrain object not found: {terrain_object_name}"}
        result = ground.create_ground_cutter(terrain, thickness, offset)
        return {"success": True, "object_name": result.name if result else None}

    def vp_make_object_floatable(self, object_name, mass, z_surface=0.0, collision_shape='CONVEX_HULL'):
        """Make an object floatable."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics.foundation import objects
        obj = bpy.data.objects.get(object_name)
        if not obj:
            return {"error": f"Object not found: {object_name}"}
        objects.make_object_floatable(obj, mass, z_surface, collision_shape)
        return {"success": True}

    def vp_create_floating_sphere(self, index, mass, location, total_count, z_surface=0.0):
        """Create a floating sphere."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics.foundation import objects
        result = objects.create_floating_sphere(index, mass, location, total_count, z_surface)
        return {"success": True, "object_name": result.name if result else None}

    def vp_generate_scattered_positions(self, num_points, spawn_radius, min_dist, z_pos, z_range=0.0):
        """Generate scattered positions."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics.foundation import objects
        positions = objects.generate_scattered_positions(num_points, spawn_radius, min_dist, z_pos, z_range)
        return {"positions": positions, "count": len(positions)}

    def vp_create_falling_spheres(self, positions, radius_range=(0.15, 0.3), physics=None, num_total=None):
        """Create falling spheres."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics.foundation import objects
        spheres = objects.create_falling_spheres(positions, tuple(radius_range), physics, num_total)
        return {"success": True, "object_names": [s.name for s in spheres]}

    def vp_create_falling_cubes(self, positions, size_range=(0.2, 0.4), physics=None, num_total=None):
        """Create falling cubes."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics.foundation import objects
        cubes = objects.create_falling_cubes(positions, tuple(size_range), physics, num_total)
        return {"success": True, "object_names": [c.name for c in cubes]}

    def vp_create_waypoint_markers(self, waypoints, z_height=0.5, size=0.3):
        """Create waypoint markers."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics.foundation import objects
        markers = objects.create_waypoint_markers(waypoints, z_height, size)
        return {"success": True, "object_names": [m.name for m in markers]}

    def vp_setup_lighting(self, resolution_x, resolution_y, start_frame, end_frame,
                          enable_caustics=False, enable_volumetric=False,
                          z_surface=0.0, z_bottom=-5.0, volumetric_density=0.1,
                          caustic_scale=10.0, caustic_strength=8000.0):
        """Setup scene lighting."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics.foundation import lighting
        lighting.setup_lighting(resolution_x, resolution_y, start_frame, end_frame,
                               enable_caustics, enable_volumetric,
                               z_surface, z_bottom, volumetric_density,
                               caustic_scale, caustic_strength)
        return {"success": True}

    def vp_create_caustics_light(self, scale, energy=20.0):
        """Create caustics light."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics.foundation import lighting
        lighting.create_caustics_light(scale, energy)
        return {"success": True}

    def vp_create_underwater_volume(self, z_surface, z_bottom, density):
        """Create underwater volume."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics.foundation import lighting
        lighting.create_underwater_volume(z_surface, z_bottom, density)
        return {"success": True}

    def vp_create_circular_path(self, radius=10.0, scale_y=0.5, z_location=0.0, name="Path"):
        """Create circular path."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics.foundation import trajectory
        result = trajectory.create_circular_path(radius, scale_y, z_location, name)
        return {"success": True, "object_name": result.name if result else None}

    def vp_create_waypoint_path(self, waypoints, closed=False, z_location=None, name="WaypointPath"):
        """Create waypoint path."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics.foundation import trajectory
        result = trajectory.create_waypoint_path(waypoints, closed, z_location, name)
        return {"success": True, "object_name": result.name if result else None}

    def vp_create_waypoint_pattern(self, pattern, scale=8.0):
        """Create waypoint pattern."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics.foundation import trajectory
        waypoints = trajectory.create_waypoint_pattern(pattern, scale)
        return {"waypoints": waypoints, "pattern": pattern}

    def vp_load_rigged_robot(self, filepath, transform=None):
        """Load a rigged robot."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics.foundation import robot
        armature, parts = robot.load_rigged_robot(filepath, transform)
        return {
            "success": True,
            "armature_name": armature.name if armature else None,
            "part_names": [p.name for p in parts]
        }

    def vp_setup_collision_meshes(self, part_object_names, kinematic=True, friction=0.8, restitution=0.1):
        """Setup collision meshes for robot parts."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics.foundation import robot
        parts = [bpy.data.objects.get(name) for name in part_object_names if bpy.data.objects.get(name)]
        count = robot.setup_collision_meshes(parts, kinematic, friction, restitution)
        return {"success": True, "collision_count": count}

    def vp_animate_walking(self, armature_name, path_curve_name, ground_object_name,
                           start_frame=1, end_frame=250, speed=1.0, **kwargs):
        """Animate robot walking."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics.foundation import robot
        armature = bpy.data.objects.get(armature_name)
        path_curve = bpy.data.objects.get(path_curve_name)
        ground_obj = bpy.data.objects.get(ground_object_name)
        
        if not armature:
            return {"error": f"Armature not found: {armature_name}"}
        if not path_curve:
            return {"error": f"Path curve not found: {path_curve_name}"}
        if not ground_obj:
            return {"error": f"Ground object not found: {ground_object_name}"}
        
        robot.animate_walking(armature, path_curve, ground_obj, start_frame, end_frame, speed, **kwargs)
        return {"success": True}

    # =========================================================================
    # VIBEPHYSICS ANNOTATION HANDLERS
    # =========================================================================

    def vp_create_bbox_annotation(self, object_name, color=None, line_width=2.0):
        """Create bounding box annotation."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics import annotation
        obj = bpy.data.objects.get(object_name)
        if not obj:
            return {"error": f"Object not found: {object_name}"}
        result = annotation.create_bbox_annotation(obj, color, line_width)
        return {"success": True, "bbox_name": result.name if result else None}

    def vp_create_motion_trail(self, object_name, start_frame=None, end_frame=None, trail_length=50, color=None):
        """Create motion trail for an object."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics import annotation
        obj = bpy.data.objects.get(object_name)
        if not obj:
            return {"error": f"Object not found: {object_name}"}
        result = annotation.create_motion_trail(obj, start_frame, end_frame, trail_length, color)
        return {"success": True, "trail_name": result.name if result else None}

    def vp_create_motion_trails(self, object_names, start_frame=None, end_frame=None, trail_length=50):
        """Create motion trails for multiple objects."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics import annotation
        objs = [bpy.data.objects.get(name) for name in object_names if bpy.data.objects.get(name)]
        results = annotation.create_motion_trails(objs, start_frame, end_frame, trail_length)
        return {"success": True, "trail_names": [r.name for r in results if r]}

    def vp_setup_point_tracking(self, object_names, num_points=100, point_size=0.02):
        """Setup point tracking visualization."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics import annotation
        objs = [bpy.data.objects.get(name) for name in object_names if bpy.data.objects.get(name)]
        annotation.setup_point_tracking_visualization(objs, num_points, point_size)
        return {"success": True}

    def vp_quick_annotate(self, object_names, bbox=False, trail=False, points=False, **kwargs):
        """Quick annotation for objects."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics import annotation
        objs = [bpy.data.objects.get(name) for name in object_names if bpy.data.objects.get(name)]
        annotation.quick_annotate(objs, bbox=bbox, trail=trail, points=points, **kwargs)
        return {"success": True}

    # =========================================================================
    # VIBEPHYSICS CAMERA HANDLERS
    # =========================================================================

    def vp_create_center_cameras(self, num_cameras=6, radius=15.0, height=8.0, target_object_name=None):
        """Create center-pointing camera rig."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics.camera import CenterPointingCameraRig
        target = bpy.data.objects.get(target_object_name) if target_object_name else None
        rig = CenterPointingCameraRig(num_cameras=num_cameras, radius=radius, height=height)
        cameras = rig.create(target_object=target)
        return {"success": True, "camera_names": [c.name for c in cameras]}

    def vp_create_following_camera(self, height=10.0, look_angle=45.0, target_object_name=None):
        """Create following camera."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics.camera import FollowingCamera
        target = bpy.data.objects.get(target_object_name) if target_object_name else None
        cam = FollowingCamera(height=height, look_angle=look_angle)
        result = cam.create(target=target)
        return {"success": True, "camera_name": result.name if result else None}

    def vp_create_mounted_cameras(self, num_cameras=4, parent_object_name=None):
        """Create object-mounted cameras."""
        if not ensure_vibephysics():
            return {"error": "vibephysics not available"}
        from vibephysics.camera import ObjectMountedCameraRig
        parent = bpy.data.objects.get(parent_object_name) if parent_object_name else None
        rig = ObjectMountedCameraRig(num_cameras=num_cameras)
        cameras = rig.create(parent_object=parent)
        return {"success": True, "camera_names": [c.name for c in cameras]}


# =============================================================================
# Blender UI Panel
# =============================================================================

class VIBEPHYSICSMCP_PT_Panel(bpy.types.Panel):
    bl_label = "VibePhysics MCP"
    bl_idname = "VIBEPHYSICSMCP_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'VibePhysicsMCP'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, "vibephysicsmcp_port")

        if not scene.vibephysicsmcp_server_running:
            layout.operator("vibephysicsmcp.start_server", text="Connect to MCP server")
        else:
            layout.operator("vibephysicsmcp.stop_server", text="Disconnect from MCP server")
            layout.label(text=f"Running on port {scene.vibephysicsmcp_port}")
        
        # VibePhysics Path
        layout.separator()
        box = layout.box()
        box.label(text="VibePhysics Path:", icon='FILE_FOLDER')
        box.prop(scene, "vibephysicsmcp_path", text="")
        box.operator("vibephysicsmcp.set_path", text="Set Path & Reload", icon='FILE_REFRESH')
        
        # Status
        if _vibephysics_imported:
            box.label(text="✓ Loaded", icon='CHECKMARK')
        else:
            box.label(text="✗ Not loaded", icon='ERROR')


class VIBEPHYSICSMCP_OT_StartServer(bpy.types.Operator):
    bl_idname = "vibephysicsmcp.start_server"
    bl_label = "Connect to Claude"
    bl_description = "Start the VibePhysics MCP server"

    def execute(self, context):
        scene = context.scene

        if not hasattr(bpy.types, "vibephysicsmcp_server") or not bpy.types.vibephysicsmcp_server:
            bpy.types.vibephysicsmcp_server = BlenderMCPServer(port=scene.vibephysicsmcp_port)

        bpy.types.vibephysicsmcp_server.start()
        scene.vibephysicsmcp_server_running = True

        return {'FINISHED'}


class VIBEPHYSICSMCP_OT_StopServer(bpy.types.Operator):
    bl_idname = "vibephysicsmcp.stop_server"
    bl_label = "Stop the connection to Claude"
    bl_description = "Stop the VibePhysics MCP server"

    def execute(self, context):
        scene = context.scene

        if hasattr(bpy.types, "vibephysicsmcp_server") and bpy.types.vibephysicsmcp_server:
            bpy.types.vibephysicsmcp_server.stop()
            del bpy.types.vibephysicsmcp_server

        scene.vibephysicsmcp_server_running = False

        return {'FINISHED'}


class VIBEPHYSICSMCP_OT_SetPath(bpy.types.Operator):
    bl_idname = "vibephysicsmcp.set_path"
    bl_label = "Set VibePhysics Path"
    bl_description = "Set vibephysics path and reload"

    def execute(self, context):
        global _vibephysics_imported, _vibephysics_error
        
        scene = context.scene
        user_path = scene.vibephysicsmcp_path
        
        if not user_path:
            self.report({'ERROR'}, "Please select the vibephysics folder")
            return {'CANCELLED'}
        
        if not os.path.exists(user_path):
            self.report({'ERROR'}, f"Path not found: {user_path}")
            return {'CANCELLED'}
        
        # Setup the path
        if setup_vibephysics_path(user_path):
            # Remove old modules if any
            if 'vibephysics' in sys.modules:
                modules_to_remove = [key for key in sys.modules.keys() if key.startswith('vibephysics')]
                for mod in modules_to_remove:
                    del sys.modules[mod]
            
            # Import
            if ensure_vibephysics():
                self.report({'INFO'}, "VibePhysics loaded successfully")
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, f"Import failed: {_vibephysics_error}")
                return {'CANCELLED'}
        else:
            self.report({'ERROR'}, "Invalid path - select the vibephysics folder")
            return {'CANCELLED'}


# =============================================================================
# Registration
# =============================================================================

def register():
    bpy.types.Scene.vibephysicsmcp_port = IntProperty(
        name="Port",
        description="Port for the VibePhysics MCP server",
        default=9876,
        min=1024,
        max=65535
    )

    bpy.types.Scene.vibephysicsmcp_server_running = BoolProperty(
        name="Server Running",
        default=False
    )
    
    bpy.types.Scene.vibephysicsmcp_path = StringProperty(
        name="VibePhysics Path",
        description="Path to vibephysics folder",
        default="",
        subtype='DIR_PATH'
    )

    bpy.utils.register_class(VIBEPHYSICSMCP_PT_Panel)
    bpy.utils.register_class(VIBEPHYSICSMCP_OT_StartServer)
    bpy.utils.register_class(VIBEPHYSICSMCP_OT_StopServer)
    bpy.utils.register_class(VIBEPHYSICSMCP_OT_SetPath)

    print("VibePhysics MCP addon registered")
    print("Set vibephysics path in the panel to load")


def unregister():
    if hasattr(bpy.types, "vibephysicsmcp_server") and bpy.types.vibephysicsmcp_server:
        bpy.types.vibephysicsmcp_server.stop()
        del bpy.types.vibephysicsmcp_server

    bpy.utils.unregister_class(VIBEPHYSICSMCP_OT_SetPath)
    bpy.utils.unregister_class(VIBEPHYSICSMCP_OT_StopServer)
    bpy.utils.unregister_class(VIBEPHYSICSMCP_OT_StartServer)
    bpy.utils.unregister_class(VIBEPHYSICSMCP_PT_Panel)

    del bpy.types.Scene.vibephysicsmcp_path
    del bpy.types.Scene.vibephysicsmcp_port
    del bpy.types.Scene.vibephysicsmcp_server_running

    print("VibePhysics MCP addon unregistered")


if __name__ == "__main__":
    register()
