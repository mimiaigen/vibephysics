import bpy
import pycolmap
import numpy as np
import math
import mathutils
from pathlib import Path

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
    
    # Set display size for the camera gizmo in viewport
    cam_data.display_size = scale
    
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
    input_path: str, # Path to sparse/0 folder
    collection_name: str = "Reconstruction",
    import_cameras: bool = True,
    import_points: bool = True,
    camera_scale: float = 0.1,
    point_size: float = 0.03,
    rotation: tuple = (-90, 0, 0) # Global rotation in degrees (Euler XYZ)
):
    """
    Load Colmap reconstruction output (sparse folder) into Blender.
    """
    input_dir = Path(input_path)
    if not input_dir.exists():
        print(f"Error: Path {input_dir} does not exist.")
        return

    print(f"Loading Colmap reconstruction from {input_dir}...")
    recon = pycolmap.Reconstruction(input_dir)
    
    # Create collection
    if collection_name in bpy.data.collections:
        col = bpy.data.collections[collection_name]
    else:
        col = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(col)
        
    # Create a root object for the whole reconstruction to allow global manipulation
    root_name = f"{collection_name}_Root"
    if root_name in bpy.data.objects:
        root_obj = bpy.data.objects[root_name]
    else:
        root_obj = bpy.data.objects.new(root_name, None)
        col.objects.link(root_obj)
    
    # Apply global rotation to the root
    root_obj.rotation_mode = 'XYZ'
    root_obj.rotation_euler = [math.radians(a) for a in rotation]

    # Set scene resolution from the first camera to correctly reflect aspect ratio (e.g. 9:16)
    if import_cameras and recon.cameras:
        first_cam = next(iter(recon.cameras.values()))
        bpy.context.scene.render.resolution_x = first_cam.width
        bpy.context.scene.render.resolution_y = first_cam.height
        bpy.context.scene.render.pixel_aspect_x = 1.0
        bpy.context.scene.render.pixel_aspect_y = 1.0
        
    if import_points:
        print(f"Importing {len(recon.points3D)} points...")
        pc_obj = create_point_cloud(recon.points3D, col, point_size=point_size)
        pc_obj.parent = root_obj
        
    if import_cameras:
        print(f"Importing {len(recon.images)} cameras...")
        first_cam_obj = None
        for img_id, image in recon.images.items():
            if image.camera_id in recon.cameras:
                cam = recon.cameras[image.camera_id]
                cam_obj = create_camera_object(image, cam, col, scale=camera_scale)
                cam_obj.parent = root_obj
                if first_cam_obj is None:
                    first_cam_obj = cam_obj
        
        # Set the first camera as active for the scene
        if first_cam_obj:
            bpy.context.scene.camera = first_cam_obj
                
    print("Done.")

