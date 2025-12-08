"""
Gaussian Splatting Import Module

Load 3D and 4D Gaussian Splatting PLY files into Blender scenes.
Supports:
- 3DGS: Single PLY file with Gaussian splat attributes
- 4DGS: Sequence of PLY files for frame-by-frame animation

Gaussian Splat PLY files typically contain:
- Position (x, y, z)
- Color (f_dc_0, f_dc_1, f_dc_2) - spherical harmonics DC term
- Opacity (opacity)
- Scale (scale_0, scale_1, scale_2)
- Rotation (rot_0, rot_1, rot_2, rot_3) - quaternion

Usage:
    from vibephysics.setup import gsplat
    
    # Load single 3DGS PLY
    obj = gsplat.load_3dgs('model.ply')
    
    # Load 4DGS sequence (folder with frame_0000.ply, frame_0001.ply, ...)
    collection = gsplat.load_4dgs_sequence('frames/', prefix='frame_')
    
    # Setup frame-by-frame visibility animation
    gsplat.setup_sequence_animation(collection, start_frame=1)
"""
import bpy
import os
import glob
import re
from typing import Optional, List, Tuple, Union


# =============================================================================
# 3D Gaussian Splatting (Single PLY)
# =============================================================================

def load_3dgs(
    filepath: str,
    name: Optional[str] = None,
    collection_name: Optional[str] = None,
    transform: Optional[dict] = None
) -> Optional[bpy.types.Object]:
    """
    Load a 3D Gaussian Splatting PLY file.
    
    Args:
        filepath: Path to the .ply file
        name: Optional name for the imported object
        collection_name: Optional collection to place the object in
        transform: Optional dict with 'location', 'rotation', 'scale' keys
    
    Returns:
        The imported object, or None if import failed
    
    Example:
        obj = load_3dgs('scene.ply', name='MyGaussianSplat')
    """
    if not os.path.exists(filepath):
        print(f"⚠️ Gaussian splat file not found: {filepath}")
        return None
    
    ext = os.path.splitext(filepath)[1].lower()
    if ext != '.ply':
        print(f"⚠️ Expected .ply file, got: {ext}")
        return None
    
    # Track existing objects
    existing_objects = set(bpy.data.objects)
    
    # Import PLY
    try:
        bpy.ops.wm.ply_import(filepath=filepath)
    except Exception as e:
        try:
            bpy.ops.import_mesh.ply(filepath=filepath)
        except Exception as e2:
            print(f"⚠️ Failed to import PLY: {e2}")
            return None
    
    # Get newly imported object
    new_objects = [obj for obj in bpy.data.objects if obj not in existing_objects]
    if not new_objects:
        print(f"⚠️ No objects imported from {filepath}")
        return None
    
    obj = new_objects[0]
    
    # Rename if specified
    if name:
        obj.name = name
    
    # Move to collection if specified
    if collection_name:
        _move_to_collection(obj, collection_name)
    
    # Apply transform if specified
    if transform:
        _apply_transform(obj, transform)
    
    print(f"✅ Loaded 3DGS: {obj.name} ({_get_point_count(obj)} points)")
    return obj


# =============================================================================
# 4D Gaussian Splatting (Sequence)
# =============================================================================

def load_4dgs_sequence(
    folder_path: str,
    prefix: str = "",
    suffix: str = ".ply",
    collection_name: str = "4DGS_Sequence",
    frame_start: int = 1,
    setup_animation: bool = True
) -> Optional[bpy.types.Collection]:
    """
    Load a sequence of 3DGS PLY files for frame-by-frame animation.
    
    Expects files named like: frame_0000.ply, frame_0001.ply, ...
    or: 0000.ply, 0001.ply, ...
    
    Args:
        folder_path: Directory containing the PLY sequence
        prefix: File name prefix (e.g., "frame_")
        suffix: File extension (default ".ply")
        collection_name: Name for the collection holding all frames
        frame_start: Blender frame number for first PLY file
        setup_animation: If True, automatically set up visibility animation
    
    Returns:
        Collection containing all frame objects
    
    Example:
        # Load sequence from folder
        collection = load_4dgs_sequence('output/frames/', prefix='frame_')
        
        # Files: frame_0000.ply, frame_0001.ply, ... -> animated sequence
    """
    if not os.path.isdir(folder_path):
        print(f"⚠️ Folder not found: {folder_path}")
        return None
    
    # Find all PLY files matching pattern
    pattern = os.path.join(folder_path, f"{prefix}*{suffix}")
    ply_files = sorted(glob.glob(pattern))
    
    if not ply_files:
        print(f"⚠️ No PLY files found matching: {pattern}")
        return None
    
    print(f"📁 Found {len(ply_files)} frames in sequence")
    
    # Create collection
    if collection_name in bpy.data.collections:
        collection = bpy.data.collections[collection_name]
    else:
        collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(collection)
    
    # Load each frame
    frame_objects = []
    for i, ply_file in enumerate(ply_files):
        frame_name = f"{collection_name}_frame_{i:04d}"
        obj = load_3dgs(ply_file, name=frame_name, collection_name=collection_name)
        if obj:
            frame_objects.append(obj)
            # Store frame index as custom property
            obj["frame_index"] = i
    
    if not frame_objects:
        print(f"⚠️ Failed to load any frames")
        return None
    
    # Setup visibility animation if requested
    if setup_animation:
        setup_sequence_animation(
            collection,
            frame_objects=frame_objects,
            frame_start=frame_start
        )
    
    print(f"✅ Loaded 4DGS sequence: {len(frame_objects)} frames")
    return collection


def load_4dgs_from_files(
    ply_files: List[str],
    collection_name: str = "4DGS_Sequence",
    frame_start: int = 1,
    setup_animation: bool = True
) -> Optional[bpy.types.Collection]:
    """
    Load a 4DGS sequence from an explicit list of PLY files.
    
    Args:
        ply_files: List of paths to PLY files (in order)
        collection_name: Name for the collection
        frame_start: Blender frame number for first PLY
        setup_animation: If True, set up visibility animation
    
    Returns:
        Collection containing all frame objects
    
    Example:
        files = ['frame_00.ply', 'frame_01.ply', 'frame_02.ply']
        collection = load_4dgs_from_files(files)
    """
    if not ply_files:
        print("⚠️ No PLY files provided")
        return None
    
    # Create collection
    if collection_name in bpy.data.collections:
        collection = bpy.data.collections[collection_name]
    else:
        collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(collection)
    
    # Load each frame
    frame_objects = []
    for i, ply_file in enumerate(ply_files):
        frame_name = f"{collection_name}_frame_{i:04d}"
        obj = load_3dgs(ply_file, name=frame_name, collection_name=collection_name)
        if obj:
            frame_objects.append(obj)
            obj["frame_index"] = i
    
    if setup_animation and frame_objects:
        setup_sequence_animation(
            collection,
            frame_objects=frame_objects,
            frame_start=frame_start
        )
    
    print(f"✅ Loaded 4DGS sequence: {len(frame_objects)} frames")
    return collection


# =============================================================================
# Animation Setup
# =============================================================================

def setup_sequence_animation(
    collection: bpy.types.Collection,
    frame_objects: Optional[List[bpy.types.Object]] = None,
    frame_start: int = 1,
    loop: bool = False
) -> None:
    """
    Set up frame-by-frame visibility animation for a Gaussian splat sequence.
    
    Each PLY object is visible only on its corresponding frame.
    
    Args:
        collection: Collection containing the frame objects
        frame_objects: Optional explicit list of objects (if None, uses all in collection)
        frame_start: Blender frame for first object
        loop: If True, loop the animation
    """
    if frame_objects is None:
        # Get objects sorted by name or frame_index
        frame_objects = sorted(
            [obj for obj in collection.objects],
            key=lambda o: o.get("frame_index", 0)
        )
    
    if not frame_objects:
        print("⚠️ No objects to animate")
        return
    
    num_frames = len(frame_objects)
    
    # Set scene frame range
    scene = bpy.context.scene
    scene.frame_start = frame_start
    scene.frame_end = frame_start + num_frames - 1
    
    # Animate visibility for each object
    for i, obj in enumerate(frame_objects):
        frame_number = frame_start + i
        
        # Hide on all frames except its own
        # Frame before: hide
        if frame_number > frame_start:
            obj.hide_viewport = True
            obj.hide_render = True
            obj.keyframe_insert(data_path="hide_viewport", frame=frame_number - 1)
            obj.keyframe_insert(data_path="hide_render", frame=frame_number - 1)
        else:
            # First frame - hide at frame 0
            obj.hide_viewport = True
            obj.hide_render = True
            obj.keyframe_insert(data_path="hide_viewport", frame=frame_start - 1)
            obj.keyframe_insert(data_path="hide_render", frame=frame_start - 1)
        
        # Show on this frame
        obj.hide_viewport = False
        obj.hide_render = False
        obj.keyframe_insert(data_path="hide_viewport", frame=frame_number)
        obj.keyframe_insert(data_path="hide_render", frame=frame_number)
        
        # Hide on next frame
        obj.hide_viewport = True
        obj.hide_render = True
        obj.keyframe_insert(data_path="hide_viewport", frame=frame_number + 1)
        obj.keyframe_insert(data_path="hide_render", frame=frame_number + 1)
        
        # Set keyframe interpolation to constant (step)
        if obj.animation_data and obj.animation_data.action:
            for fcurve in obj.animation_data.action.fcurves:
                for keyframe in fcurve.keyframe_points:
                    keyframe.interpolation = 'CONSTANT'
    
    # Optionally loop
    if loop and num_frames > 1:
        for i, obj in enumerate(frame_objects):
            # Make visible again at the start if looping
            pass  # Would need additional keyframes for looping
    
    print(f"✅ Animation setup: frames {frame_start} to {scene.frame_end}")


def clear_sequence_animation(collection: bpy.types.Collection) -> None:
    """
    Remove visibility animation from all objects in a collection.
    
    Args:
        collection: Collection containing animated objects
    """
    for obj in collection.objects:
        obj.hide_viewport = False
        obj.hide_render = False
        if obj.animation_data:
            obj.animation_data_clear()
    
    print(f"✅ Cleared animation from {len(collection.objects)} objects")


# =============================================================================
# Geometry Nodes Support
# =============================================================================

def apply_geometry_nodes_from_blend(
    target_object: bpy.types.Object,
    blend_filepath: str,
    node_group_name: str
) -> bool:
    """
    Apply a Geometry Nodes modifier from an external .blend file.
    
    This is useful for applying Gaussian splatting render node groups
    (like UGRS) that provide viewport rendering of splats.
    
    Args:
        target_object: Object to add the modifier to
        blend_filepath: Path to .blend file containing the node group
        node_group_name: Name of the node group to use
    
    Returns:
        True if successful
    
    Example:
        # Apply UGRS rendering node group
        apply_geometry_nodes_from_blend(
            obj, 
            'ugrs_nodes.blend',
            'UGRS_MainNodeTree_v1.0'
        )
    """
    if not os.path.exists(blend_filepath):
        print(f"⚠️ Blend file not found: {blend_filepath}")
        return False
    
    # Import node group from blend file
    try:
        with bpy.data.libraries.load(blend_filepath, link=False) as (data_from, data_to):
            if node_group_name in data_from.node_groups:
                data_to.node_groups = [node_group_name]
            else:
                print(f"⚠️ Node group '{node_group_name}' not found in {blend_filepath}")
                print(f"   Available: {data_from.node_groups}")
                return False
    except Exception as e:
        print(f"⚠️ Failed to load node group: {e}")
        return False
    
    # Get the imported node group
    if node_group_name not in bpy.data.node_groups:
        print(f"⚠️ Node group not imported correctly")
        return False
    
    node_group = bpy.data.node_groups[node_group_name]
    
    # Add Geometry Nodes modifier
    modifier = target_object.modifiers.new(name="GaussianSplat", type='NODES')
    modifier.node_group = node_group
    
    print(f"✅ Applied geometry nodes '{node_group_name}' to {target_object.name}")
    return True


def setup_gsplat_display(
    obj: bpy.types.Object,
    point_size: float = 0.01,
    use_emission: bool = True,
    use_geometry_nodes: bool = True
) -> bpy.types.Material:
    """
    Setup Gaussian splat display with geometry nodes and material.
    
    This creates:
    1. Geometry nodes to convert mesh to point cloud (required for color display)
    2. Material that uses vertex colors
    
    Note: Geometry nodes are REQUIRED to display vertex colors on point clouds.
    The Mesh to Points conversion is lightweight and works for large point clouds.
    
    Args:
        obj: The Gaussian splat mesh object
        point_size: Size of each point for display
        use_emission: If True, use emission shader for bright unlit colors
        use_geometry_nodes: If True, create geometry nodes (recommended: True)
    
    Returns:
        The created material
    
    Example:
        obj = load_3dgs('scene.ply')
        mat = setup_gsplat_display(obj)
    """
    num_verts = len(obj.data.vertices) if obj.data else 0
    
    # Setup color - convert SH to RGB if needed (MUST happen before geometry nodes)
    color_attr_name = setup_gsplat_color(obj)
    
    # Create and apply material FIRST
    mat = _create_gsplat_material(obj.name + "_Material", use_emission, color_attr_name)
    
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
    
    # Create geometry nodes for point cloud display
    # This is required to display vertex colors on point cloud data
    if use_geometry_nodes:
        if num_verts > 1000000:
            print(f"   ℹ️ Large point cloud ({num_verts:,} points) - using lightweight geometry nodes")
        modifier = _create_gsplat_geometry_nodes_simple(obj, point_size, color_attr_name)
        
        # Set the material in the geometry nodes SetMaterial node
        if modifier and modifier.node_group:
            for node in modifier.node_group.nodes:
                if node.type == 'SET_MATERIAL':
                    node.inputs['Material'].default_value = mat
    
    return mat


def _get_vertex_color_name(obj: bpy.types.Object) -> str:
    """Get the name of the vertex color attribute on the object."""
    if obj.data and obj.data.color_attributes:
        # Return the first color attribute name
        return obj.data.color_attributes[0].name
    # Fallback to common names
    return "Col"


# Spherical Harmonics constant for 0th order (used in 3DGS)
SH_C0 = 0.28209479177387814


def convert_sh_to_rgb(obj: bpy.types.Object) -> bool:
    """
    Convert spherical harmonics coefficients (f_dc_*) to RGB vertex colors.
    
    Gaussian Splat PLY files store color as spherical harmonics coefficients:
    - f_dc_0, f_dc_1, f_dc_2 (the 0th order SH for R, G, B)
    
    The conversion formula is: RGB = SH_C0 * f_dc + 0.5
    where SH_C0 = 0.28209479177387814
    
    Args:
        obj: The mesh object with Gaussian splat data
    
    Returns:
        True if conversion was successful, False otherwise
    """
    import numpy as np
    
    mesh = obj.data
    if not mesh:
        return False
    
    # Check if we have f_dc_* attributes
    attrs = {a.name: a for a in mesh.attributes}
    
    has_f_dc = all(f"f_dc_{i}" in attrs for i in range(3))
    
    if not has_f_dc:
        print(f"   No f_dc_* attributes found - skipping SH conversion")
        return False
    
    print(f"   Found spherical harmonics attributes (f_dc_0, f_dc_1, f_dc_2)")
    print(f"   Converting to RGB using SH_C0 = {SH_C0}")
    
    num_verts = len(mesh.vertices)
    
    # Read f_dc values
    f_dc = np.zeros((num_verts, 3), dtype=np.float32)
    
    for i in range(3):
        attr = attrs[f"f_dc_{i}"]
        if attr.domain == 'POINT':
            values = np.zeros(num_verts, dtype=np.float32)
            attr.data.foreach_get('value', values)
            f_dc[:, i] = values
    
    # Convert SH to RGB: RGB = SH_C0 * f_dc + 0.5
    rgb = SH_C0 * f_dc + 0.5
    
    # Clamp to [0, 1]
    rgb = np.clip(rgb, 0.0, 1.0)
    
    # Create or get color attribute
    color_attr_name = "GSplatColor"
    
    if color_attr_name in mesh.color_attributes:
        color_attr = mesh.color_attributes[color_attr_name]
    else:
        color_attr = mesh.color_attributes.new(
            name=color_attr_name,
            type='FLOAT_COLOR',
            domain='POINT'
        )
    
    # Set vertex colors (RGBA format)
    rgba = np.ones((num_verts, 4), dtype=np.float32)
    rgba[:, :3] = rgb
    
    # Flatten for foreach_set
    color_attr.data.foreach_set('color', rgba.flatten())
    
    # Set as active color attribute for viewport display
    mesh.color_attributes.active_color = color_attr
    
    # Also set render color index
    color_idx = mesh.color_attributes.find(color_attr_name)
    if color_idx >= 0:
        mesh.color_attributes.render_color_index = color_idx
    
    # Mark mesh as updated
    mesh.update()
    
    print(f"   ✅ Created '{color_attr_name}' vertex color attribute")
    
    return True


def setup_gsplat_color(obj: bpy.types.Object) -> str:
    """
    Setup proper vertex colors for Gaussian splat display.
    
    This handles both:
    - Standard PLY vertex colors (Col, Cd, etc.)
    - Gaussian Splat SH coefficients (f_dc_0, f_dc_1, f_dc_2)
    
    Returns:
        Name of the color attribute to use
    """
    mesh = obj.data
    if not mesh:
        return "Col"
    
    # Check for f_dc_* attributes and convert if present
    attrs = {a.name for a in mesh.attributes}
    
    if all(f"f_dc_{i}" in attrs for i in range(3)):
        # Gaussian Splat format - convert SH to RGB
        if convert_sh_to_rgb(obj):
            return "GSplatColor"
    
    # Otherwise use existing vertex colors
    if mesh.color_attributes:
        return mesh.color_attributes[0].name
    
    return "Col"


def _create_gsplat_geometry_nodes_simple(obj: bpy.types.Object, point_size: float = 0.01, color_attr_name: str = "GSplatColor"):
    """
    Create simple geometry nodes for point cloud display with vertex colors.
    
    Uses Mesh to Points to convert mesh to point cloud, which properly displays
    vertex colors in Blender's viewport. This is lightweight and works for 
    large point clouds.
    """
    # Remove existing GSplatDisplay modifier if present
    for mod in list(obj.modifiers):
        if mod.name == "GSplatDisplay":
            obj.modifiers.remove(mod)
    
    # Create modifier
    modifier = obj.modifiers.new(name="GSplatDisplay", type='NODES')
    
    # Create node tree
    node_group = bpy.data.node_groups.new(name="GSplatDisplay_" + obj.name, type='GeometryNodeTree')
    modifier.node_group = node_group
    
    # Setup interface
    node_group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    node_group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    
    nodes = node_group.nodes
    links = node_group.links
    
    # Group input
    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-600, 0)
    
    # Group output
    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (600, 0)
    
    # Get the vertex color attribute
    named_attr = nodes.new('GeometryNodeInputNamedAttribute')
    named_attr.location = (-400, -150)
    named_attr.data_type = 'FLOAT_COLOR'
    named_attr.inputs['Name'].default_value = color_attr_name
    
    # Mesh to Points - converts mesh vertices to point cloud
    mesh_to_points = nodes.new('GeometryNodeMeshToPoints')
    mesh_to_points.location = (-200, 0)
    mesh_to_points.mode = 'VERTICES'
    mesh_to_points.inputs['Radius'].default_value = point_size
    
    links.new(input_node.outputs['Geometry'], mesh_to_points.inputs['Mesh'])
    
    # Store the color on the point cloud
    store_attr = nodes.new('GeometryNodeStoreNamedAttribute')
    store_attr.location = (100, 0)
    store_attr.data_type = 'FLOAT_COLOR'
    store_attr.domain = 'POINT'
    store_attr.inputs['Name'].default_value = color_attr_name
    
    links.new(mesh_to_points.outputs['Points'], store_attr.inputs['Geometry'])
    links.new(named_attr.outputs['Attribute'], store_attr.inputs['Value'])
    
    # Set Material
    set_material = nodes.new('GeometryNodeSetMaterial')
    set_material.location = (350, 0)
    
    links.new(store_attr.outputs['Geometry'], set_material.inputs['Geometry'])
    links.new(set_material.outputs['Geometry'], output_node.inputs['Geometry'])
    
    return modifier


def _create_gsplat_geometry_nodes(obj: bpy.types.Object, point_size: float = 0.01):
    """
    Create geometry nodes modifier for Gaussian splat display.
    
    Instances small icospheres at each vertex and transfers vertex colors.
    """
    # Remove existing GSplatDisplay modifier if present
    for mod in list(obj.modifiers):
        if mod.name == "GSplatDisplay":
            obj.modifiers.remove(mod)
    
    # Create modifier
    modifier = obj.modifiers.new(name="GSplatDisplay", type='NODES')
    
    # Create node tree
    node_group = bpy.data.node_groups.new(name="GSplatDisplay_" + obj.name, type='GeometryNodeTree')
    modifier.node_group = node_group
    
    # Setup interface
    node_group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    node_group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    
    nodes = node_group.nodes
    links = node_group.links
    
    # Group input
    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-600, 0)
    
    # Group output
    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (800, 0)
    
    # Get vertex color attribute
    color_attr = nodes.new('GeometryNodeInputNamedAttribute')
    color_attr.location = (-600, -150)
    color_attr.data_type = 'FLOAT_COLOR'
    color_attr.inputs[0].default_value = "Col"  # Default vertex color name
    
    # Mesh to Points - converts mesh vertices to point cloud
    mesh_to_points = nodes.new('GeometryNodeMeshToPoints')
    mesh_to_points.location = (-200, 0)
    mesh_to_points.mode = 'VERTICES'
    mesh_to_points.inputs['Radius'].default_value = point_size
    
    links.new(input_node.outputs['Geometry'], mesh_to_points.inputs['Mesh'])
    
    # Create icosphere for instancing
    ico = nodes.new('GeometryNodeMeshIcoSphere')
    ico.location = (-200, -200)
    ico.inputs['Radius'].default_value = point_size
    ico.inputs['Subdivisions'].default_value = 1
    
    # Instance on Points
    instance_on_points = nodes.new('GeometryNodeInstanceOnPoints')
    instance_on_points.location = (100, 0)
    
    links.new(mesh_to_points.outputs['Points'], instance_on_points.inputs['Points'])
    links.new(ico.outputs['Mesh'], instance_on_points.inputs['Instance'])
    
    # Store the color as an attribute on the instances
    store_color = nodes.new('GeometryNodeStoreNamedAttribute')
    store_color.location = (300, 0)
    store_color.data_type = 'FLOAT_COLOR'
    store_color.domain = 'INSTANCE'
    store_color.inputs['Name'].default_value = "inst_color"
    
    links.new(instance_on_points.outputs['Instances'], store_color.inputs['Geometry'])
    links.new(color_attr.outputs['Attribute'], store_color.inputs['Value'])
    
    # Realize instances to convert to actual geometry
    realize = nodes.new('GeometryNodeRealizeInstances')
    realize.location = (500, 0)
    
    links.new(store_color.outputs['Geometry'], realize.inputs['Geometry'])
    
    # Store the color on the realized geometry vertices
    store_final_color = nodes.new('GeometryNodeStoreNamedAttribute')
    store_final_color.location = (650, 0)
    store_final_color.data_type = 'FLOAT_COLOR'
    store_final_color.domain = 'POINT'
    store_final_color.inputs['Name'].default_value = "Col"
    
    # Get the instance color to transfer to vertices
    get_inst_color = nodes.new('GeometryNodeInputNamedAttribute')
    get_inst_color.location = (450, -150)
    get_inst_color.data_type = 'FLOAT_COLOR'
    get_inst_color.inputs[0].default_value = "inst_color"
    
    links.new(realize.outputs['Geometry'], store_final_color.inputs['Geometry'])
    links.new(get_inst_color.outputs['Attribute'], store_final_color.inputs['Value'])
    
    links.new(store_final_color.outputs['Geometry'], output_node.inputs['Geometry'])
    
    return modifier


def _create_gsplat_material(name: str, use_emission: bool = True, color_attr_name: str = "GSplatColor") -> bpy.types.Material:
    """
    Create material for Gaussian splat / point cloud display.
    
    Uses vertex colors with emission for bright unlit colors (like original 3DGS).
    """
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    nodes.clear()
    
    # Output
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    # Use Attribute node to read the color attribute by name
    # This works for both vertex colors and point cloud colors
    attr_node = nodes.new('ShaderNodeAttribute')
    attr_node.location = (-200, 0)
    attr_node.attribute_name = color_attr_name
    attr_node.attribute_type = 'GEOMETRY'
    
    if use_emission:
        # Emission shader for bright, unlit colors (like original 3DGS rendering)
        emission = nodes.new('ShaderNodeEmission')
        emission.location = (150, 0)
        emission.inputs['Strength'].default_value = 1.0
        
        links.new(attr_node.outputs['Color'], emission.inputs['Color'])
        links.new(emission.outputs['Emission'], output.inputs['Surface'])
    else:
        # Simple principled shader
        principled = nodes.new('ShaderNodeBsdfPrincipled')
        principled.location = (150, 0)
        principled.inputs['Roughness'].default_value = 1.0
        
        links.new(attr_node.outputs['Color'], principled.inputs['Base Color'])
        links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    mat.use_backface_culling = False
    
    return mat


def create_point_cloud_material(
    name: str = "GaussianSplatMaterial",
    use_vertex_colors: bool = True
) -> bpy.types.Material:
    """
    Create a simple material for displaying Gaussian splats as colored points.
    
    This is a basic material - for proper Gaussian splatting rendering,
    use geometry nodes with proper splat rendering.
    
    Args:
        name: Material name
        use_vertex_colors: If True, use vertex color attribute
    
    Returns:
        The created material
    """
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Create nodes
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.location = (100, 0)
    
    if use_vertex_colors:
        # Use vertex color attribute (common for Gaussian splats)
        attr = nodes.new('ShaderNodeVertexColor')
        attr.location = (-200, 0)
        attr.layer_name = "Col"  # Default vertex color layer name
        
        links.new(attr.outputs['Color'], principled.inputs['Base Color'])
    
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    # Settings for point cloud display
    mat.use_backface_culling = False
    
    return mat


def set_point_display(obj: bpy.types.Object, point_size: float = 2.0) -> None:
    """
    Configure object for point cloud display in viewport.
    
    Args:
        obj: Object to configure
        point_size: Size of points in viewport
    """
    obj.display_type = 'TEXTURED'
    
    # If mesh, convert to point cloud display
    if obj.type == 'MESH':
        obj.data.show_normal_vertex = False


# =============================================================================
# Utility Functions
# =============================================================================

def _move_to_collection(obj: bpy.types.Object, collection_name: str) -> None:
    """Move object to specified collection."""
    # Get or create collection
    if collection_name not in bpy.data.collections:
        collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(collection)
    else:
        collection = bpy.data.collections[collection_name]
    
    # Unlink from current collections
    for coll in obj.users_collection:
        coll.objects.unlink(obj)
    
    # Link to target collection
    collection.objects.link(obj)


def _apply_transform(obj: bpy.types.Object, transform: dict) -> None:
    """Apply transform to object."""
    import math
    
    if 'location' in transform:
        obj.location = transform['location']
    
    if 'rotation' in transform:
        rx, ry, rz = transform['rotation']
        if max(abs(rx), abs(ry), abs(rz)) > 6.28:
            rx, ry, rz = math.radians(rx), math.radians(ry), math.radians(rz)
        obj.rotation_euler = (rx, ry, rz)
    
    if 'scale' in transform:
        scale = transform['scale']
        if isinstance(scale, (int, float)):
            obj.scale = (scale, scale, scale)
        else:
            obj.scale = scale


def _get_point_count(obj: bpy.types.Object) -> int:
    """Get number of points/vertices in object."""
    if obj.type == 'MESH' and obj.data:
        return len(obj.data.vertices)
    return 0


def get_sequence_info(collection: bpy.types.Collection) -> dict:
    """
    Get information about a 4DGS sequence collection.
    
    Args:
        collection: Collection to inspect
    
    Returns:
        Dict with frame count, point counts, etc.
    """
    objects = list(collection.objects)
    
    info = {
        'frame_count': len(objects),
        'collection_name': collection.name,
        'objects': [],
        'total_points': 0,
    }
    
    for obj in sorted(objects, key=lambda o: o.get("frame_index", 0)):
        point_count = _get_point_count(obj)
        info['objects'].append({
            'name': obj.name,
            'frame_index': obj.get("frame_index", -1),
            'points': point_count,
        })
        info['total_points'] += point_count
    
    if objects:
        info['avg_points_per_frame'] = info['total_points'] // len(objects)
    
    return info


# =============================================================================
# Convenience function for quick setup
# =============================================================================

def load_gsplat(
    path: str,
    collection_name: str = "GaussianSplat",
    frame_start: int = 1,
    setup_animation: bool = True
) -> Union[bpy.types.Object, bpy.types.Collection, None]:
    """
    Smart loader for Gaussian splats - auto-detects 3DGS vs 4DGS.
    
    - If path is a single .ply file -> load as 3DGS
    - If path is a folder -> load as 4DGS sequence
    
    Args:
        path: Path to PLY file or folder containing sequence
        collection_name: Collection name for 4DGS sequence
        frame_start: Starting frame for animation
        setup_animation: Setup visibility animation for sequences
    
    Returns:
        Single object (3DGS) or Collection (4DGS)
    
    Example:
        # Load single splat
        obj = load_gsplat('scene.ply')
        
        # Load sequence
        collection = load_gsplat('frames/')
    """
    if os.path.isfile(path):
        # Single file - 3DGS
        return load_3dgs(path, collection_name=collection_name)
    
    elif os.path.isdir(path):
        # Folder - 4DGS sequence
        return load_4dgs_sequence(
            path,
            collection_name=collection_name,
            frame_start=frame_start,
            setup_animation=setup_animation
        )
    
    else:
        print(f"⚠️ Path not found: {path}")
        return None
