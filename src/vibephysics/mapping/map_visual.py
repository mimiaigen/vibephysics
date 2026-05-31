import bpy
import pycolmap
import numpy as np
import math
import mathutils
from pathlib import Path

from vibephysics.feedforward.common import VIDEO_EXTRACT_FPS_FILE
from vibephysics.feedforward.visual import (
    CAMERA_TRAJECTORY_RADIUS,
    _AnimationTiming,
    _apply_build_animation,
    _apply_camera_viewport_display,
    _configure_scene_timeline,
    _configure_viewports_material_preview,
    _create_playback_camera,
    _frame_viewports_on_point_cloud,
    _keyframe_camera_visibility,
    create_point_cloud_object,
)

def _resolve_video_fps(frames_dir: str | Path | None, video_fps: float | None) -> float:
    if video_fps is not None:
        return float(video_fps)
    if frames_dir is not None:
        fps_file = Path(frames_dir) / VIDEO_EXTRACT_FPS_FILE
        if fps_file.exists():
            return float(fps_file.read_text().strip())
    return 2.0


def _ordered_images(recon: pycolmap.Reconstruction) -> list[tuple[int, object]]:
    return sorted(recon.images.items(), key=lambda item: item[1].name)


def _colmap_points_for_animation(
    points3D: dict,
    image_index: dict[int, int],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    xyz, rgb, conf, frame_ids = [], [], [], []
    for point in points3D.values():
        track_ids = [element.image_id for element in point.track.elements if element.image_id in image_index]
        if not track_ids:
            continue
        xyz.append(point.xyz)
        rgb.append(point.color / 255.0)
        conf.append(10.0)
        frame_ids.append(min(image_index[iid] for iid in track_ids))
    if not xyz:
        return (
            np.empty((0, 3), dtype=np.float64),
            np.empty((0, 4), dtype=np.float32),
            np.empty((0,), dtype=np.float32),
            np.empty((0,), dtype=np.int32),
        )
    colors = np.hstack(
        (np.asarray(rgb, dtype=np.float32), np.ones((len(rgb), 1), dtype=np.float32))
    )
    return (
        np.asarray(xyz, dtype=np.float64),
        colors,
        np.asarray(conf, dtype=np.float32),
        np.asarray(frame_ids, dtype=np.int32),
    )


def _create_camera_trajectory(
    camera_objects: list[bpy.types.Object],
    collection: bpy.types.Collection,
    timing: _AnimationTiming | None,
    animate: bool,
) -> bpy.types.Object | None:
    if len(camera_objects) < 2:
        return None
    radius = CAMERA_TRAJECTORY_RADIUS
    points = [obj.matrix_world.translation for obj in camera_objects]
    curve_data = bpy.data.curves.new(name="CameraTrajectory", type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.fill_mode = "FULL"
    curve_data.bevel_depth = radius
    curve_data.bevel_resolution = 2
    spline = curve_data.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for i, co in enumerate(points):
        spline.points[i].co = (float(co[0]), float(co[1]), float(co[2]), 1.0)
    traj_obj = bpy.data.objects.new("CameraTrajectory", curve_data)
    mat = bpy.data.materials.new(name="CameraTrajectoryMaterial")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is not None:
        bsdf.inputs["Base Color"].default_value = (0.2, 0.8, 1.0, 1.0)
    curve_data.materials.append(mat)
    collection.objects.link(traj_obj)
    if animate and timing is not None:
        _apply_build_animation(traj_obj, timing)
    return traj_obj


def create_camera_object(image, camera, collection, scale=0.1):
    """
    Create a Blender camera object from a Colmap image and camera.
    """
    name = image.name
    
    # 1. Pose: World-to-Camera (SfM) -> Camera-to-World (Blender)
    if hasattr(image, "cam_from_world") and callable(image.cam_from_world):
        pose = image.cam_from_world()
        rot_mat = pose.rotation.matrix()
        tvec = pose.translation
    else:
        # Fallback for older pycolmap (World-to-Camera)
        qvec = getattr(image, "qvec", np.array([1, 0, 0, 0]))
        tvec = getattr(image, "tvec", np.zeros(3))
        w, x, y, z = qvec
        rot_mat = np.array([
            [1 - 2*y**2 - 2*z**2, 2*x*y - 2*z*w, 2*x*z + 2*y*w],
            [2*x*y + 2*z*w, 1 - 2*x**2 - 2*z**2, 2*y*z - 2*x*w],
            [2*x*z - 2*y*w, 2*y*z + 2*x*w, 1 - 2*x**2 - 2*y**2]
        ])
    
    # Camera-to-World matrix in OpenCV frame (X-right, Y-down, Z-forward)
    rot_mat_inv = rot_mat.T
    tvec_inv = -rot_mat_inv @ tvec
    
    # Construct 4x4 matrix in mathutils
    mat_world_cv = mathutils.Matrix.Identity(4)
    for i in range(3):
        for j in range(3):
            mat_world_cv[i][j] = rot_mat_inv[i, j]
        mat_world_cv[i][3] = tvec_inv[i]
    
    # Convert from OpenCV (X-right, Y-down, Z-forward) 
    # to Blender (X-right, Y-up, Z-back / points -Z)
    # This is a 180-degree rotation around the X-axis
    flip_mat = mathutils.Matrix.Rotation(math.pi, 4, 'X')
    final_matrix = mat_world_cv @ flip_mat
    
    # 2. Create Camera Data and Object
    # We use the native bpy camera object
    cam_data = bpy.data.cameras.new(name=f"CamData_{name}")
    cam_obj = bpy.data.objects.new(name=name, object_data=cam_data)
    collection.objects.link(cam_obj)
    
    cam_obj.matrix_world = final_matrix
    
    # 3. Intrinsics: Focal length and Principal Point (Image x, y)
    width = camera.width
    height = camera.height
    params = camera.params
    model = camera.model_name if hasattr(camera, "model_name") else "PINHOLE"
    
    # Standard Blender sensor width (36mm)
    cam_data.sensor_fit = 'HORIZONTAL'
    cam_data.sensor_width = 36.0
    cam_data.sensor_height = 36.0 * height / width
    
    # Extract params based on model
    if model == "SIMPLE_PINHOLE":
        f, cx, cy = params
        fx = fy = f
    elif model == "PINHOLE":
        fx, fy, cx, cy = params
    elif model in ["SIMPLE_RADIAL", "RADIAL"]:
        f, cx, cy = params[:3]
        fx = fy = f
    elif model in ["OPENCV", "FULL_OPENCV"]:
        fx, fy, cx, cy = params[:4]
    else:
        # Fallback
        fx = fy = params[0] if len(params) > 0 else 1000.0
        cx = width / 2.0
        cy = height / 2.0
        
    # Focal length: f_mm = f_px * sensor_width / width_px
    cam_data.lens = fx * cam_data.sensor_width / width
    
    # Principal Point Shift (consider image x and y offsets)
    # shift_x/y are ratios of the larger dimension (if fit is AUTO) or the fit dimension
    # Since we use 'HORIZONTAL', both are relative to width.
    cam_data.shift_x = (cx / width) - 0.5
    cam_data.shift_y = (height / 2.0 - cy) / width
    
    _apply_camera_viewport_display(cam_data)
    
    return cam_obj

def create_point_cloud(points3D, collection, name="PointCloud", point_size=0.03):
    """
    Create a point cloud visualization using a mesh with vertices and colors.
    Uses Geometry Nodes to make points visible as spheres.
    """
    mesh = bpy.data.meshes.new(name=name)
    obj = bpy.data.objects.new(name=name, object_data=mesh)
    collection.objects.link(obj)
    
    # Extract points and colors
    xyz = []
    rgb = []
    
    for p_id, p in points3D.items():
        xyz.append(p.xyz)
        rgb.append(p.color / 255.0) # Normalize to 0-1
        
    if not xyz:
        print("No points found in reconstruction.")
        return obj
        
    # Create mesh
    mesh.from_pydata(xyz, [], [])
    mesh.update()
    
    # Add colors as a generic attribute
    if rgb:
        # Check Blender version for attribute creation
        if hasattr(mesh.attributes, "new"):
            color_attr = mesh.attributes.new(name="Color", type='FLOAT_COLOR', domain='POINT')
            color_attr.data.foreach_set("color", [c for color in rgb for c in (*color, 1.0)]) # RGBA
    
    # Simple Geometry Nodes setup to render points as spheres
    modifier = obj.modifiers.new(name="PointVisualizer", type='NODES')
    
    # Setup node tree
    node_tree = bpy.data.node_groups.new(name="PointVisualizerTree", type='GeometryNodeTree')
    
    # In Blender 4.0+, we use interface to add sockets
    if hasattr(node_tree, "interface"):
        if not any(item.name == "Geometry" for item in node_tree.interface.items_tree if item.item_type == 'SOCKET'):
             node_tree.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
             node_tree.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    else:
        # Older Blender fallback
        if "Geometry" not in node_tree.inputs:
            node_tree.inputs.new('NodeSocketGeometry', "Geometry")
        if "Geometry" not in node_tree.outputs:
            node_tree.outputs.new('NodeSocketGeometry', "Geometry")
    
    links = node_tree.links
    nodes = node_tree.nodes
    
    # Clear default nodes
    nodes.clear()
    
    # Input/Output
    node_in = nodes.new('NodeGroupInput')
    node_out = nodes.new('NodeGroupOutput')
    
    # Point to Volume / Instances
    node_m2p = nodes.new('GeometryNodeMeshToPoints')
    node_inst = nodes.new('GeometryNodeInstanceOnPoints')
    node_sph = nodes.new('GeometryNodeMeshIcoSphere')
    node_sph.inputs['Radius'].default_value = point_size
    node_sph.inputs['Subdivisions'].default_value = 1
    
    # Realize Instances to propagate attributes (like Color)
    node_realize = nodes.new('GeometryNodeRealizeInstances')
    
    # Material
    node_mat = nodes.new('GeometryNodeSetMaterial')
    
    # Material setup
    mat_name = "PointCloudMaterial"
    if mat_name not in bpy.data.materials:
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        nodes_mat = mat.node_tree.nodes
        links_mat = mat.node_tree.links
        nodes_mat.clear()
        
        node_out_mat = nodes_mat.new('ShaderNodeOutputMaterial')
        node_principled = nodes_mat.new('ShaderNodeBsdfPrincipled')
        # Use Attribute node to get the vertex color
        node_attr = nodes_mat.new('ShaderNodeAttribute')
        node_attr.attribute_name = "Color"
        node_attr.attribute_type = 'GEOMETRY'
        
        links_mat.new(node_attr.outputs['Color'], node_principled.inputs['Base Color'])
        links_mat.new(node_principled.outputs['BSDF'], node_out_mat.inputs['Surface'])
    else:
        mat = bpy.data.materials[mat_name]
        
    # Assign material to object slots (important for some Blender versions to see attributes)
    if mat.name not in obj.data.materials:
        obj.data.materials.append(mat)
        
    node_mat.inputs['Material'].default_value = mat
    
    # Link nodes
    links.new(node_in.outputs[0], node_m2p.inputs['Mesh'])
    links.new(node_m2p.outputs['Points'], node_inst.inputs['Points'])
    links.new(node_sph.outputs['Mesh'], node_inst.inputs['Instance'])
    links.new(node_inst.outputs['Instances'], node_realize.inputs['Geometry'])
    links.new(node_realize.outputs['Geometry'], node_mat.inputs['Geometry'])
    links.new(node_mat.outputs['Geometry'], node_out.inputs[0])
    
    modifier.node_group = node_tree
    
    # Attempt to set viewport shading to MATERIAL for better UX
    if bpy.context.screen:
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.shading.type = 'MATERIAL'
    
    return obj

def load_colmap_reconstruction(
    input_path: str,
    collection_name: str = "Reconstruction",
    import_cameras: bool = True,
    import_points: bool = True,
    import_trajectory: bool = True,
    camera_scale: float = 0.1,
    point_size: float = 0.03,
    rotation: tuple[float, float, float] = (-90, 0, 0),
    animate: bool = True,
    animation_fps: int = 24,
    video_fps: float | None = None,
    frames_dir: str | Path | None = None,
):
    """
    Load Colmap reconstruction output (sparse folder) into Blender.
    """
    input_dir = Path(input_path)
    if not input_dir.exists():
        print(f"Error: Path {input_dir} does not exist.")
        return None

    print(f"Loading Colmap reconstruction from {input_dir}...")
    recon = pycolmap.Reconstruction(input_dir)
    ordered_images = _ordered_images(recon)
    image_index = {image_id: idx for idx, (image_id, _) in enumerate(ordered_images)}

    timing = None
    if animate and len(ordered_images) > 1:
        timing = _AnimationTiming(
            num_frames=len(ordered_images),
            animation_fps=animation_fps,
            video_fps=_resolve_video_fps(frames_dir, video_fps),
        )
        _configure_scene_timeline(timing)
        print(
            f"[vibephysics] Animation: {timing.duration_seconds:.1f}s "
            f"(frames {timing.preview_frame}=full preview, "
            f"{timing.timeline_start}-{timing.timeline_end} progressive @ "
            f"{int(round(timing.animation_fps))} fps, source {timing.video_fps:g} fps)"
        )

    if collection_name in bpy.data.collections:
        col = bpy.data.collections[collection_name]
    else:
        col = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(col)

    root_name = f"{collection_name}_Root"
    root_obj = bpy.data.objects.get(root_name)
    if root_obj is None:
        root_obj = bpy.data.objects.new(root_name, None)
        col.objects.link(root_obj)
    elif not root_obj.users_collection:
        col.objects.link(root_obj)
    root_obj.rotation_mode = "XYZ"
    root_obj.rotation_euler = [math.radians(a) for a in rotation]

    if import_cameras and recon.cameras:
        first_cam = next(iter(recon.cameras.values()))
        bpy.context.scene.render.resolution_x = first_cam.width
        bpy.context.scene.render.resolution_y = first_cam.height
        bpy.context.scene.render.pixel_aspect_x = 1.0
        bpy.context.scene.render.pixel_aspect_y = 1.0

    point_obj = None
    camera_objects: list[bpy.types.Object] = []

    if import_cameras and ordered_images:
        print(f"Importing {len(ordered_images)} cameras...")
        cameras_col = bpy.data.collections.new("Cameras")
        col.children.link(cameras_col)
        for _, image in ordered_images:
            if image.camera_id not in recon.cameras:
                continue
            cam_obj = create_camera_object(
                image,
                recon.cameras[image.camera_id],
                cameras_col,
                scale=camera_scale,
            )
            camera_objects.append(cam_obj)
        for idx, cam_obj in enumerate(camera_objects):
            cam_obj.parent = root_obj
            if timing is not None:
                _keyframe_camera_visibility(cam_obj, timing, idx)
        if timing is not None:
            playback = _create_playback_camera(camera_objects, cameras_col, timing)
            if playback is not None:
                playback.parent = root_obj
        elif camera_objects:
            bpy.context.scene.camera = camera_objects[0]

    if import_points and recon.points3D:
        print(f"Importing {len(recon.points3D)} points...")
        if timing is not None:
            points, colors, conf, frame_ids = _colmap_points_for_animation(recon.points3D, image_index)
            if len(points) > 0:
                point_obj = create_point_cloud_object(
                    "Points",
                    points,
                    colors,
                    conf,
                    collection=col,
                    scale=point_size,
                    min_confidence=0.0,
                    frame_ids=frame_ids,
                    recon_time_scale=timing.recon_time_scale,
                )
                point_obj.parent = root_obj
        else:
            point_obj = create_point_cloud(recon.points3D, col, point_size=point_size)
            point_obj.parent = root_obj

    if import_trajectory and timing is not None and len(camera_objects) >= 2:
        traj = _create_camera_trajectory(
            camera_objects,
            col,
            timing,
            animate=True,
        )
        if traj is not None:
            traj.parent = root_obj

    _configure_viewports_material_preview()
    if point_obj is not None:
        _frame_viewports_on_point_cloud(point_obj, fill=0.9)

    print("Done.")
    return point_obj


def save_reconstruction_blend(
    sparse_path: str | Path,
    blend_path: str | Path,
    point_size: float = 0.03,
    rotation: tuple[float, float, float] = (-90, 0, 0),
    collection_name: str = "GLOMAP_Result",
    animate: bool = True,
    animation_fps: int = 24,
    video_fps: float | None = None,
    frames_dir: str | Path | None = None,
    verbose: bool = True,
) -> int:
    """Load a sparse reconstruction and save a .blend file."""
    sparse_path = Path(sparse_path)
    blend_path = Path(blend_path)
    has_bin = (sparse_path / "cameras.bin").exists()
    has_txt = (sparse_path / "cameras.txt").exists()
    if not sparse_path.exists() or not (has_bin or has_txt):
        print(f"[ERROR] No reconstruction found at {sparse_path}")
        return 1

    if verbose:
        print(f"--- [vibephysics] Saving Blender visualization to {blend_path} ---")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    load_colmap_reconstruction(
        str(sparse_path),
        collection_name=collection_name,
        point_size=point_size,
        rotation=rotation,
        animate=animate,
        animation_fps=animation_fps,
        video_fps=video_fps,
        frames_dir=frames_dir,
    )
    blend_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    if verbose:
        print(f"Saved .blend to {blend_path}")
    return 0

