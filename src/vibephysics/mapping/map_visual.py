import bpy
import pycolmap
import numpy as np
from pathlib import Path
import math

def create_camera_object(image, camera, collection, scale=0.1):
    """
    Create a Blender camera object from a Colmap image and camera.
    """
    name = image.name
    
    # Colmap pose is World-to-Camera (R, t)
    # pycolmap 3.x uses image.cam_from_world() method
    if hasattr(image, "cam_from_world") and callable(image.cam_from_world):
        pose = image.cam_from_world()
        rot_mat = pose.rotation.matrix()
        tvec = pose.translation
    else:
        # Fallback for older pycolmap
        qvec = getattr(image, "qvec", np.array([1, 0, 0, 0]))
        tvec = getattr(image, "tvec", np.zeros(3))
        # Manual qvec to rotmat if function is missing
        if hasattr(pycolmap, "qvec_to_rotmat"):
            rot_mat = pycolmap.qvec_to_rotmat(qvec)
        else:
            # Standard Hamilton quaternion to rotation matrix
            w, x, y, z = qvec
            rot_mat = np.array([
                [1 - 2*y**2 - 2*z**2, 2*x*y - 2*z*w, 2*x*z + 2*y*w],
                [2*x*y + 2*z*w, 1 - 2*x**2 - 2*z**2, 2*y*z - 2*x*w],
                [2*x*z - 2*y*w, 2*y*z + 2*x*w, 1 - 2*x**2 - 2*y**2]
            ])
    
    # Inverse rotation and translation to get Camera-to-World
    rot_mat_inv = rot_mat.T
    tvec_inv = -rot_mat_inv @ tvec
    
    # Create Camera Data
    cam_data = bpy.data.cameras.new(name=f"CamData_{name}")
    cam_obj = bpy.data.objects.new(name=name, object_data=cam_data)
    collection.objects.link(cam_obj)
    
    # Construct 4x4 matrix in OpenCV frame (X-right, Y-down, Z-forward)
    mat_world_cv = np.eye(4)
    mat_world_cv[:3, :3] = rot_mat_inv
    mat_world_cv[:3, 3] = tvec_inv
    
    # Convert from OpenCV to Blender coordinate system
    # Blender camera looks down -Z, Y is up.
    # We rotate 180 degrees around X to flip Y and Z.
    transform_matrix = np.array([
        [1, 0, 0, 0],
        [0, -1, 0, 0],
        [0, 0, -1, 0],
        [0, 0, 0, 1]
    ])
    
    final_matrix = mat_world_cv @ transform_matrix
    
    # Assign to object
    import mathutils
    m = mathutils.Matrix(final_matrix.tolist())
    cam_obj.matrix_world = m
    
    # Set camera intrinsics
    # Params mapping depends on camera model
    width = camera.width
    height = camera.height
    cam_data.sensor_width = 36.0 # standard 36mm sensor
    
    # f_mm = f_px * sensor_width / width_px
    f_px = 1000.0 # fallback
    
    # Get camera model name
    if hasattr(camera, "model") and hasattr(camera.model, "name"):
        model = camera.model.name
    else:
        model = getattr(camera, "model_name", "UNKNOWN")
    
    params = camera.params
    
    if model in ["SIMPLE_PINHOLE", "SIMPLE_RADIAL"]:
        # f, cx, cy
        f_px = params[0]
    elif model in ["PINHOLE", "OPENCV", "FULL_OPENCV"]:
        # fx, fy, cx, cy
        f_px = (params[0] + params[1]) / 2.0
    
    cam_data.lens = f_px * cam_data.sensor_width / width
    
    return cam_obj

def create_point_cloud(points3D, collection, name="PointCloud", point_size=0.01):
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
        # For Blender 3.6/4.0+
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
    # Let's use Mesh to Points then Instances
    node_m2p = nodes.new('GeometryNodeMeshToPoints')
    node_inst = nodes.new('GeometryNodeInstanceOnPoints')
    node_sph = nodes.new('GeometryNodeMeshIcoSphere')
    node_sph.inputs['Radius'].default_value = point_size
    node_sph.inputs['Subdivisions'].default_value = 1
    
    # Realize Instances to propagate attributes (like Color)
    node_realize = nodes.new('GeometryNodeRealizeInstances')
    
    # Material
    node_mat = nodes.new('GeometryNodeSetMaterial')
    
    # ... material setup same as before
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
        
        links_mat.new(node_attr.outputs['Color'], node_principled.inputs['Base Color'])
        links_mat.new(node_principled.outputs['BSDF'], node_out_mat.inputs['Surface'])
        
    node_mat.inputs['Material'].default_value = bpy.data.materials[mat_name]
    
    # Link nodes
    links.new(node_in.outputs[0], node_m2p.inputs['Mesh'])
    links.new(node_m2p.outputs['Points'], node_inst.inputs['Points'])
    links.new(node_sph.outputs['Mesh'], node_inst.inputs['Instance'])
    links.new(node_inst.outputs['Instances'], node_realize.inputs['Geometry'])
    links.new(node_realize.outputs['Geometry'], node_mat.inputs['Geometry'])
    links.new(node_mat.outputs['Geometry'], node_out.inputs[0])
    
    modifier.node_group = node_tree
    
    # Attempt to set viewport shading to MATERIAL for better UX
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
    point_size: float = 0.01
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
        
    if import_points:
        print(f"Importing {len(recon.points3D)} points...")
        create_point_cloud(recon.points3D, col, point_size=point_size)
        
    if import_cameras:
        print(f"Importing {len(recon.images)} cameras...")
        for img_id, image in recon.images.items():
            if image.camera_id in recon.cameras:
                cam = recon.cameras[image.camera_id]
                create_camera_object(image, cam, col, scale=camera_scale)
                
    print("Done.")

