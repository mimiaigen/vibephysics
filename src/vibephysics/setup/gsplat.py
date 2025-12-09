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
    
    # Advanced: Setup with custom display options
    obj = load_3dgs('model.ply')
    setup_gsplat_display_advanced(
        obj,
        mesh_type='DualIcoSphere',  # 'Cube', 'IcoSphere', 'DualIcoSphere'
        shader_mode='Gaussian',      # 'Gaussian', 'Ring', 'Wireframe', 'Freestyle'
        point_scale='Max',           # 'Fix', 'Auto', 'Max'
        output_channel='Final color' # 'Final color', 'Normal', 'Depth', 'Alpha'
    )
"""
import bpy
import os
import glob
import re
from typing import Optional, List, Tuple, Union
from enum import Enum


# =============================================================================
# Enums for Display Options (based on UGRS/Nunchucks)
# =============================================================================

class MeshType(Enum):
    """
    Mesh type for Gaussian splat point instancing.
    
    Based on UGRS geometry nodes mesh switch:
    - Cube: Simple cube mesh for each point
    - IcoSphere: Icosphere mesh (default, round appearance)
    - DualIcoSphere: Dual mesh of icosphere (hexagonal pattern, better for Gaussians)
    - Circle: Flat circle/disk mesh (best for Gaussian shader with transparency)
    """
    CUBE = 'Cube'
    ICOSPHERE = 'IcoSphere'
    DUAL_ICOSPHERE = 'DualIcoSphere'
    CIRCLE = 'Circle'


class ShaderMode(Enum):
    """
    Shader mode for Gaussian splat rendering.
    
    Based on UGRS shader mode switch - affects how the splats are rendered:
    - Gaussian: Standard Gaussian splatting appearance (smooth falloff)
    - Ring: Ring-shaped splats (hollow center)
    - Wireframe: Wireframe rendering of splats
    - Freestyle: Freestyle/line art rendering
    """
    GAUSSIAN = 'Gaussian'
    RING = 'Ring'
    WIREFRAME = 'Wireframe'
    FREESTYLE = 'Freestyle'


class PointScale(Enum):
    """
    Point scale calculation mode for Gaussian splats.
    
    Based on UGRS point scale switch:
    - FIX: Fixed point size (multiplied by fixed_scale parameter)
    - AUTO: Automatic scaling based on average scale values
    - MAX: Use maximum of scale_0, scale_1, scale_2 (uniform scaling)
    - ANISOTROPIC: Use individual scale_0, scale_1, scale_2 for X, Y, Z (ellipsoid shapes)
    """
    FIX = 'Fix'
    AUTO = 'Auto'
    MAX = 'Max'
    ANISOTROPIC = 'Anisotropic'


class OutputChannel(Enum):
    """
    Output channel for Gaussian splat visualization.
    
    Based on UGRS output channel switch:
    - FINAL_COLOR: Standard rendered color (SH converted to RGB)
    - NORMAL: Surface normal visualization
    - DEPTH: Depth visualization
    - ALPHA: Alpha/opacity channel visualization
    - ALBEDO: Base albedo color
    """
    FINAL_COLOR = 'Final color'
    NORMAL = 'Normal'
    DEPTH = 'Depth'
    ALPHA = 'Alpha'
    ALBEDO = 'Albedo'


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


# =============================================================================
# Gaussian Splatting Constants and Utilities
# =============================================================================

# Spherical Harmonics constant for 0th order (used in 3DGS)
SH_C0 = 0.28209479177387814


def sigmoid(x):
    """Sigmoid function for opacity conversion."""
    import numpy as np
    return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))


def get_gsplat_info(obj: bpy.types.Object) -> dict:
    """
    Get detailed information about a Gaussian Splat mesh object.
    
    Returns:
        Dictionary with PLY attribute info:
        {
            'num_points': int,
            'has_sh': bool,  # f_dc_* attributes
            'has_scale': bool,  # scale_* attributes
            'has_rotation': bool,  # rot_* attributes
            'has_opacity': bool,
            'has_4d': bool,  # t_scale, motion_* attributes
            'attributes': {name: {'dtype': str, 'min': float, 'max': float, 'mean': float}},
            'is_gaussian_splat': bool,
        }
    """
    import numpy as np
    
    info = {
        'num_points': 0,
        'has_sh': False,
        'has_scale': False,
        'has_rotation': False,
        'has_opacity': False,
        'has_4d': False,
        'attributes': {},
        'is_gaussian_splat': False,
    }
    
    mesh = obj.data
    if not mesh:
        return info
    
    info['num_points'] = len(mesh.vertices)
    
    # Analyze attributes
    attr_names = set()
    for attr in mesh.attributes:
        attr_names.add(attr.name)
        
        # Get statistics for float attributes
        try:
            if attr.data_type in ('FLOAT', 'FLOAT_COLOR', 'FLOAT_VECTOR'):
                num_elements = len(attr.data)
                if num_elements > 0:
                    if attr.data_type == 'FLOAT':
                        values = np.zeros(num_elements, dtype=np.float32)
                        attr.data.foreach_get('value', values)
                    elif attr.data_type == 'FLOAT_COLOR':
                        values = np.zeros(num_elements * 4, dtype=np.float32)
                        attr.data.foreach_get('color', values)
                        values = values[::4]  # Just R channel for stats
                    else:
                        values = np.zeros(num_elements * 3, dtype=np.float32)
                        attr.data.foreach_get('vector', values)
                        values = values[::3]  # Just X for stats
                    
                    info['attributes'][attr.name] = {
                        'dtype': attr.data_type,
                        'domain': attr.domain,
                        'min': float(np.nanmin(values)),
                        'max': float(np.nanmax(values)),
                        'mean': float(np.nanmean(values)),
                    }
        except Exception:
            pass
    
    # Check for Gaussian Splat attributes
    info['has_sh'] = all(f"f_dc_{i}" in attr_names for i in range(3))
    info['has_scale'] = all(f"scale_{i}" in attr_names for i in range(3))
    info['has_rotation'] = all(f"rot_{i}" in attr_names for i in range(4))
    info['has_opacity'] = 'opacity' in attr_names
    info['has_4d'] = any(a in attr_names for a in ['t_scale', 'motion_0', 'motion_1', 'motion_2'])
    
    info['is_gaussian_splat'] = (
        info['has_sh'] and 
        info['has_scale'] and 
        info['has_rotation']
    )
    
    return info


def print_gsplat_info(obj: bpy.types.Object) -> dict:
    """
    Print detailed Gaussian Splat info and return the info dict.
    """
    info = get_gsplat_info(obj)
    
    print(f"\n📊 Gaussian Splat Analysis:")
    print(f"   Points: {info['num_points']:,}")
    
    if info['is_gaussian_splat']:
        gs_type = "4D Gaussian Splat" if info['has_4d'] else "3D Gaussian Splat"
        print(f"   Type: {gs_type}")
    else:
        print(f"   Type: Not a standard Gaussian Splat")
    
    print(f"   - Spherical Harmonics (f_dc_*): {'✅' if info['has_sh'] else '❌'}")
    print(f"   - Scale (scale_*): {'✅' if info['has_scale'] else '❌'}")
    print(f"   - Rotation (rot_*): {'✅' if info['has_rotation'] else '❌'}")
    print(f"   - Opacity: {'✅' if info['has_opacity'] else '❌'}")
    
    # Show SH color info
    if info['has_sh']:
        f_dc_0 = info['attributes'].get('f_dc_0', {})
        f_dc_1 = info['attributes'].get('f_dc_1', {})
        f_dc_2 = info['attributes'].get('f_dc_2', {})
        
        if f_dc_0 and f_dc_1 and f_dc_2:
            # Convert mean SH to RGB
            r = SH_C0 * f_dc_0.get('mean', 0) + 0.5
            g = SH_C0 * f_dc_1.get('mean', 0) + 0.5
            b = SH_C0 * f_dc_2.get('mean', 0) + 0.5
            r, g, b = max(0, min(1, r)), max(0, min(1, g)), max(0, min(1, b))
            print(f"   - Mean Color (RGB): ({r:.3f}, {g:.3f}, {b:.3f})")
    
    # Show opacity info
    if info['has_opacity']:
        opacity_attr = info['attributes'].get('opacity', {})
        if opacity_attr:
            mean_logit = opacity_attr.get('mean', 0)
            mean_opacity = sigmoid(mean_logit)
            print(f"   - Mean Opacity: {mean_opacity:.3f} (logit: {mean_logit:.2f})")
    
    return info


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


def _create_instance_mesh(nodes, links, mesh_type: MeshType, point_size: float):
    """
    Create instance mesh based on mesh type (Cube, IcoSphere, DualIcoSphere).
    
    Based on UGRS geometry nodes mesh switch implementation.
    
    Args:
        nodes: Node tree nodes collection
        links: Node tree links collection
        mesh_type: MeshType enum value
        point_size: Base size for the mesh
    
    Returns:
        Output socket of the mesh geometry
    """
    if mesh_type == MeshType.CUBE:
        # Simple cube mesh
        cube = nodes.new('GeometryNodeMeshCube')
        cube.location = (-200, -200)
        cube.inputs['Size'].default_value = (point_size * 2, point_size * 2, point_size * 2)
        return cube.outputs['Mesh']
    
    elif mesh_type == MeshType.ICOSPHERE:
        # Standard icosphere (default)
        ico = nodes.new('GeometryNodeMeshIcoSphere')
        ico.location = (-200, -200)
        ico.inputs['Radius'].default_value = point_size
        ico.inputs['Subdivisions'].default_value = 1
        return ico.outputs['Mesh']
    
    elif mesh_type == MeshType.DUAL_ICOSPHERE:
        # DualIcoSphere: Create cube, apply dual mesh transform
        # This creates a hexagonal pattern that's better for Gaussian representation
        cube = nodes.new('GeometryNodeMeshCube')
        cube.location = (-400, -200)
        cube.inputs['Size'].default_value = (1.0, 1.0, 1.0)
        
        # Dual mesh node creates hexagonal faces from the cube
        dual_mesh = nodes.new('GeometryNodeDualMesh')
        dual_mesh.location = (-200, -200)
        dual_mesh.inputs['Keep Boundaries'].default_value = False
        
        links.new(cube.outputs['Mesh'], dual_mesh.inputs['Mesh'])
        
        # Transform to scale properly (use GeometryNodeTransform, not GeometryNodeTransformGeometry)
        transform = nodes.new('GeometryNodeTransform')
        transform.location = (0, -200)
        transform.inputs['Scale'].default_value = (point_size, point_size, point_size)
        
        links.new(dual_mesh.outputs['Dual Mesh'], transform.inputs['Geometry'])
        
        return transform.outputs['Geometry']
    
    elif mesh_type == MeshType.CIRCLE:
        # Flat circle/disk mesh - best for Gaussian shader with transparency
        # Creates a billboard-like splat appearance
        circle = nodes.new('GeometryNodeMeshCircle')
        circle.location = (-400, -200)
        circle.inputs['Vertices'].default_value = 16  # Smooth enough circle
        circle.inputs['Radius'].default_value = point_size
        circle.fill_type = 'NGON'  # Fill the circle (creates a disk)
        
        return circle.outputs['Mesh']
    
    # Default fallback to icosphere
    ico = nodes.new('GeometryNodeMeshIcoSphere')
    ico.location = (-200, -200)
    ico.inputs['Radius'].default_value = point_size
    ico.inputs['Subdivisions'].default_value = 1
    return ico.outputs['Mesh']


def _calculate_point_scale(nodes, links, scale_mode: PointScale, fixed_scale: float = 0.01):
    """
    Calculate point scale based on scale mode.
    
    Based on UGRS point scale switch:
    - Fix: Fixed multiplier (returns scalar)
    - Auto: Uses average of scale values (returns scalar)
    - Max: Uses maximum(scale_0, scale_1, scale_2) (returns scalar)
    - Anisotropic: Returns vector (exp(scale_0), exp(scale_1), exp(scale_2)) for ellipsoid shapes
    
    Args:
        nodes: Node tree nodes collection
        links: Node tree links collection
        scale_mode: PointScale enum value
        fixed_scale: Fixed scale value for FIX mode
    
    Returns:
        tuple: (output_socket, is_vector) - output socket and whether it's a vector
    """
    # Read scale attributes
    scale_0_attr = nodes.new('GeometryNodeInputNamedAttribute')
    scale_0_attr.location = (-800, -400)
    scale_0_attr.data_type = 'FLOAT'
    scale_0_attr.inputs['Name'].default_value = 'scale_0'
    
    scale_1_attr = nodes.new('GeometryNodeInputNamedAttribute')
    scale_1_attr.location = (-800, -500)
    scale_1_attr.data_type = 'FLOAT'
    scale_1_attr.inputs['Name'].default_value = 'scale_1'
    
    scale_2_attr = nodes.new('GeometryNodeInputNamedAttribute')
    scale_2_attr.location = (-800, -600)
    scale_2_attr.data_type = 'FLOAT'
    scale_2_attr.inputs['Name'].default_value = 'scale_2'
    
    if scale_mode == PointScale.FIX:
        # Fixed scale multiplier
        fixed_value = nodes.new('ShaderNodeValue')
        fixed_value.location = (-600, -400)
        fixed_value.outputs[0].default_value = fixed_scale
        
        return fixed_value.outputs[0], False
    
    elif scale_mode == PointScale.AUTO:
        # Auto: Multiply by fixed scale
        exp_scale = nodes.new('ShaderNodeMath')
        exp_scale.location = (-600, -450)
        exp_scale.operation = 'EXPONENT'
        
        links.new(scale_0_attr.outputs['Attribute'], exp_scale.inputs[0])
        
        multiply = nodes.new('ShaderNodeMath')
        multiply.location = (-400, -450)
        multiply.operation = 'MULTIPLY'
        multiply.inputs[1].default_value = fixed_scale
        
        links.new(exp_scale.outputs[0], multiply.inputs[0])
        
        return multiply.outputs[0], False
    
    elif scale_mode == PointScale.ANISOTROPIC:
        # Anisotropic: exp(scale_0), exp(scale_1), exp(scale_2) as vector
        # This creates ellipsoid shapes that can be thin as needles!
        
        # exp(scale_0) for X
        exp_0 = nodes.new('ShaderNodeMath')
        exp_0.location = (-600, -400)
        exp_0.operation = 'EXPONENT'
        links.new(scale_0_attr.outputs['Attribute'], exp_0.inputs[0])
        
        # exp(scale_1) for Y
        exp_1 = nodes.new('ShaderNodeMath')
        exp_1.location = (-600, -500)
        exp_1.operation = 'EXPONENT'
        links.new(scale_1_attr.outputs['Attribute'], exp_1.inputs[0])
        
        # exp(scale_2) for Z
        exp_2 = nodes.new('ShaderNodeMath')
        exp_2.location = (-600, -600)
        exp_2.operation = 'EXPONENT'
        links.new(scale_2_attr.outputs['Attribute'], exp_2.inputs[0])
        
        # Ensure minimum scale (avoid zero)
        min_val = 0.000001
        
        max_0 = nodes.new('ShaderNodeMath')
        max_0.location = (-450, -400)
        max_0.operation = 'MAXIMUM'
        max_0.inputs[1].default_value = min_val
        links.new(exp_0.outputs[0], max_0.inputs[0])
        
        max_1 = nodes.new('ShaderNodeMath')
        max_1.location = (-450, -500)
        max_1.operation = 'MAXIMUM'
        max_1.inputs[1].default_value = min_val
        links.new(exp_1.outputs[0], max_1.inputs[0])
        
        max_2 = nodes.new('ShaderNodeMath')
        max_2.location = (-450, -600)
        max_2.operation = 'MAXIMUM'
        max_2.inputs[1].default_value = min_val
        links.new(exp_2.outputs[0], max_2.inputs[0])
        
        # Combine into vector
        combine = nodes.new('ShaderNodeCombineXYZ')
        combine.location = (-300, -500)
        links.new(max_0.outputs[0], combine.inputs['X'])
        links.new(max_1.outputs[0], combine.inputs['Y'])
        links.new(max_2.outputs[0], combine.inputs['Z'])
        
        return combine.outputs['Vector'], True
    
    elif scale_mode == PointScale.MAX:
        # Max: Use maximum of scale_0, scale_1, scale_2
        # First exp() to convert from log scale, then max
        exp_0 = nodes.new('ShaderNodeMath')
        exp_0.location = (-600, -400)
        exp_0.operation = 'EXPONENT'
        links.new(scale_0_attr.outputs['Attribute'], exp_0.inputs[0])
        
        exp_1 = nodes.new('ShaderNodeMath')
        exp_1.location = (-600, -500)
        exp_1.operation = 'EXPONENT'
        links.new(scale_1_attr.outputs['Attribute'], exp_1.inputs[0])
        
        exp_2 = nodes.new('ShaderNodeMath')
        exp_2.location = (-600, -600)
        exp_2.operation = 'EXPONENT'
        links.new(scale_2_attr.outputs['Attribute'], exp_2.inputs[0])
        
        # max(scale_0, scale_1)
        max_01 = nodes.new('ShaderNodeMath')
        max_01.location = (-400, -450)
        max_01.operation = 'MAXIMUM'
        links.new(exp_0.outputs[0], max_01.inputs[0])
        links.new(exp_1.outputs[0], max_01.inputs[1])
        
        # max(max_01, scale_2)
        max_012 = nodes.new('ShaderNodeMath')
        max_012.location = (-200, -450)
        max_012.operation = 'MAXIMUM'
        links.new(max_01.outputs[0], max_012.inputs[0])
        links.new(exp_2.outputs[0], max_012.inputs[1])
        
        return max_012.outputs[0], False
    
    # Default
    fixed_value = nodes.new('ShaderNodeValue')
    fixed_value.location = (-600, -400)
    fixed_value.outputs[0].default_value = fixed_scale
    return fixed_value.outputs[0], False


def setup_gsplat_display_advanced(
    obj: bpy.types.Object,
    mesh_type: Union[MeshType, str] = MeshType.ICOSPHERE,
    shader_mode: Union[ShaderMode, str] = ShaderMode.GAUSSIAN,
    point_scale: Union[PointScale, str] = PointScale.MAX,
    output_channel: Union[OutputChannel, str] = OutputChannel.FINAL_COLOR,
    fixed_scale: float = 0.01,
    geo_size: float = 3.0,
    use_emission: bool = True
) -> bpy.types.Material:
    """
    Advanced Gaussian splat display setup with configurable options.
    
    Based on UGRS/Nunchucks geometry nodes implementation.
    
    Args:
        obj: The Gaussian splat mesh object
        mesh_type: Type of mesh for point instancing ('Cube', 'IcoSphere', 'DualIcoSphere', 'Circle')
        shader_mode: Shader rendering mode ('Gaussian', 'Ring', 'Wireframe', 'Freestyle')
        point_scale: Scale calculation mode:
            - 'Fix': Fixed uniform size
            - 'Auto': Automatic based on scale_0
            - 'Max': Use max(scale_0, scale_1, scale_2) - uniform spheres
            - 'Anisotropic': Use (scale_0, scale_1, scale_2) as X,Y,Z - ellipsoid shapes!
                            This creates thin needle-like splats. Includes rotation from quaternion.
        output_channel: Output channel ('Final color', 'Normal', 'Depth', 'Alpha')
        fixed_scale: Fixed scale value for 'Fix' mode
        geo_size: Geometry size multiplier (default 3.0). Controls how large the mesh is
                  relative to the visible Gaussian. Larger = more transparent area around
                  the visible splat center. This is key for the Gaussian appearance!
        use_emission: Use emission shader for bright unlit colors
    
    Returns:
        The created material
    
    Example:
        # Spherical splats (blob-like)
        mat = setup_gsplat_display_advanced(obj, point_scale='Max')
        
        # Ellipsoid splats (can be thin as needles!)
        mat = setup_gsplat_display_advanced(obj, point_scale='Anisotropic')
    """
    # Convert string arguments to enums
    if isinstance(mesh_type, str):
        mesh_type = MeshType(mesh_type)
    if isinstance(shader_mode, str):
        shader_mode = ShaderMode(shader_mode)
    if isinstance(point_scale, str):
        point_scale = PointScale(point_scale)
    if isinstance(output_channel, str):
        output_channel = OutputChannel(output_channel)
    
    # Setup color - convert SH to RGB if needed
    color_attr_name = setup_gsplat_color(obj)
    
    # Create material
    mat = _create_gsplat_material_advanced(
        obj.name + "_Material",
        use_emission,
        color_attr_name,
        shader_mode,
        output_channel
    )
    
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
    
    # Create geometry nodes with advanced options
    modifier = _create_gsplat_geometry_nodes_advanced(
        obj,
        mesh_type,
        point_scale,
        fixed_scale,
        geo_size,
        color_attr_name
    )
    
    # Set material in geometry nodes
    if modifier and modifier.node_group:
        for node in modifier.node_group.nodes:
            if node.type == 'SET_MATERIAL':
                node.inputs['Material'].default_value = mat
    
    print(f"   ✅ Advanced display setup: mesh={mesh_type.value}, scale={point_scale.value}")
    return mat


def _create_gsplat_geometry_nodes_advanced(
    obj: bpy.types.Object,
    mesh_type: MeshType,
    scale_mode: PointScale,
    fixed_scale: float,
    geo_size: float,
    color_attr_name: str
):
    """
    Create advanced geometry nodes for Gaussian splat display.
    
    Implements mesh type selection, point scale calculation, and color transfer.
    
    The geo_size parameter is crucial: it scales the mesh larger than the visible
    Gaussian, so the shader can create the characteristic falloff appearance where
    only the center portion is visible.
    """
    # Remove existing modifier
    for mod in list(obj.modifiers):
        if mod.name == "GSplatDisplay":
            obj.modifiers.remove(mod)
    
    # Create modifier
    modifier = obj.modifiers.new(name="GSplatDisplay", type='NODES')
    
    # Create node tree
    node_group = bpy.data.node_groups.new(
        name="GSplatDisplay_Advanced_" + obj.name,
        type='GeometryNodeTree'
    )
    modifier.node_group = node_group
    
    # Setup interface
    node_group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    node_group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    
    nodes = node_group.nodes
    links = node_group.links
    
    # === Group Input/Output ===
    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-1000, 0)
    
    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (1500, 0)
    
    # === Get Color Attribute ===
    color_attr = nodes.new('GeometryNodeInputNamedAttribute')
    color_attr.location = (-800, -150)
    color_attr.data_type = 'FLOAT_COLOR'
    color_attr.inputs['Name'].default_value = color_attr_name
    
    # === Mesh to Points ===
    mesh_to_points = nodes.new('GeometryNodeMeshToPoints')
    mesh_to_points.location = (-400, 0)
    mesh_to_points.mode = 'VERTICES'
    
    links.new(input_node.outputs['Geometry'], mesh_to_points.inputs['Mesh'])
    
    # === Calculate Point Scale ===
    scale_output, is_vector_scale = _calculate_point_scale(nodes, links, scale_mode, fixed_scale)
    
    # For mesh_to_points radius, use max of scale components if vector
    if is_vector_scale:
        # Extract max component for radius
        separate_for_radius = nodes.new('ShaderNodeSeparateXYZ')
        separate_for_radius.location = (-300, -350)
        links.new(scale_output, separate_for_radius.inputs['Vector'])
        
        max_xy = nodes.new('ShaderNodeMath')
        max_xy.location = (-150, -350)
        max_xy.operation = 'MAXIMUM'
        links.new(separate_for_radius.outputs['X'], max_xy.inputs[0])
        links.new(separate_for_radius.outputs['Y'], max_xy.inputs[1])
        
        max_xyz = nodes.new('ShaderNodeMath')
        max_xyz.location = (0, -350)
        max_xyz.operation = 'MAXIMUM'
        links.new(max_xy.outputs[0], max_xyz.inputs[0])
        links.new(separate_for_radius.outputs['Z'], max_xyz.inputs[1])
        
        links.new(max_xyz.outputs[0], mesh_to_points.inputs['Radius'])
    else:
        links.new(scale_output, mesh_to_points.inputs['Radius'])
    
    # === Create Instance Mesh ===
    mesh_output = _create_instance_mesh(nodes, links, mesh_type, 1.0)
    
    # === Instance on Points ===
    instance_on_points = nodes.new('GeometryNodeInstanceOnPoints')
    instance_on_points.location = (200, 0)
    
    links.new(mesh_to_points.outputs['Points'], instance_on_points.inputs['Points'])
    links.new(mesh_output, instance_on_points.inputs['Instance'])
    
    # === Handle Scale (vector or scalar) ===
    if is_vector_scale:
        # Anisotropic scaling - use vector directly
        geo_size_multiply = nodes.new('ShaderNodeVectorMath')
        geo_size_multiply.location = (100, -300)
        geo_size_multiply.operation = 'SCALE'
        geo_size_multiply.inputs[3].default_value = geo_size
        
        links.new(scale_output, geo_size_multiply.inputs[0])
        links.new(geo_size_multiply.outputs['Vector'], instance_on_points.inputs['Scale'])
        
        # === Add Rotation from Quaternion ===
        # Read quaternion attributes (rot_0, rot_1, rot_2, rot_3)
        rot_0 = nodes.new('GeometryNodeInputNamedAttribute')
        rot_0.location = (-800, -750)
        rot_0.data_type = 'FLOAT'
        rot_0.inputs['Name'].default_value = 'rot_0'
        
        rot_1 = nodes.new('GeometryNodeInputNamedAttribute')
        rot_1.location = (-800, -850)
        rot_1.data_type = 'FLOAT'
        rot_1.inputs['Name'].default_value = 'rot_1'
        
        rot_2 = nodes.new('GeometryNodeInputNamedAttribute')
        rot_2.location = (-800, -950)
        rot_2.data_type = 'FLOAT'
        rot_2.inputs['Name'].default_value = 'rot_2'
        
        rot_3 = nodes.new('GeometryNodeInputNamedAttribute')
        rot_3.location = (-800, -1050)
        rot_3.data_type = 'FLOAT'
        rot_3.inputs['Name'].default_value = 'rot_3'
        
        # Combine quaternion components (w, x, y, z format)
        combine_quat = nodes.new('FunctionNodeCombineColor')
        combine_quat.location = (-600, -900)
        combine_quat.mode = 'RGB'  # Use RGB to combine 4 values
        # Note: Blender quaternion is (w, x, y, z), PLY is typically (rot_0=w, rot_1=x, rot_2=y, rot_3=z)
        links.new(rot_0.outputs['Attribute'], combine_quat.inputs[0])  # R = w
        links.new(rot_1.outputs['Attribute'], combine_quat.inputs[1])  # G = x
        links.new(rot_2.outputs['Attribute'], combine_quat.inputs[2])  # B = y
        
        # Convert quaternion to rotation using Blender's built-in node
        quat_to_rotation = nodes.new('FunctionNodeQuaternionToRotation')
        quat_to_rotation.location = (-400, -900)
        links.new(rot_0.outputs['Attribute'], quat_to_rotation.inputs[0])  # W
        links.new(rot_1.outputs['Attribute'], quat_to_rotation.inputs[1])  # X
        links.new(rot_2.outputs['Attribute'], quat_to_rotation.inputs[2])  # Y
        links.new(rot_3.outputs['Attribute'], quat_to_rotation.inputs[3])  # Z
        
        # Connect rotation to instance on points
        links.new(quat_to_rotation.outputs['Rotation'], instance_on_points.inputs['Rotation'])
    else:
        # Uniform scaling - create vector from scalar
        combine_scale = nodes.new('ShaderNodeCombineXYZ')
        combine_scale.location = (-100, -300)
        links.new(scale_output, combine_scale.inputs['X'])
        links.new(scale_output, combine_scale.inputs['Y'])
        links.new(scale_output, combine_scale.inputs['Z'])
        
        # Apply geo_size multiplier
        geo_size_multiply = nodes.new('ShaderNodeVectorMath')
        geo_size_multiply.location = (100, -300)
        geo_size_multiply.operation = 'SCALE'
        geo_size_multiply.inputs[3].default_value = geo_size
        
        links.new(combine_scale.outputs['Vector'], geo_size_multiply.inputs[0])
        links.new(geo_size_multiply.outputs['Vector'], instance_on_points.inputs['Scale'])
    
    # === Store Color on Instances ===
    store_color = nodes.new('GeometryNodeStoreNamedAttribute')
    store_color.location = (400, 0)
    store_color.data_type = 'FLOAT_COLOR'
    store_color.domain = 'INSTANCE'
    store_color.inputs['Name'].default_value = "inst_color"
    
    links.new(instance_on_points.outputs['Instances'], store_color.inputs['Geometry'])
    links.new(color_attr.outputs['Attribute'], store_color.inputs['Value'])
    
    # === Store Opacity on Instances ===
    # Read opacity and convert with sigmoid
    opacity_attr = nodes.new('GeometryNodeInputNamedAttribute')
    opacity_attr.location = (200, -400)
    opacity_attr.data_type = 'FLOAT'
    opacity_attr.inputs['Name'].default_value = 'opacity'
    
    # Sigmoid: 1 / (1 + exp(-opacity))
    neg_opacity = nodes.new('ShaderNodeMath')
    neg_opacity.location = (350, -400)
    neg_opacity.operation = 'MULTIPLY'
    neg_opacity.inputs[1].default_value = -1.0
    links.new(opacity_attr.outputs['Attribute'], neg_opacity.inputs[0])
    
    exp_opacity = nodes.new('ShaderNodeMath')
    exp_opacity.location = (500, -400)
    exp_opacity.operation = 'EXPONENT'
    links.new(neg_opacity.outputs[0], exp_opacity.inputs[0])
    
    add_one = nodes.new('ShaderNodeMath')
    add_one.location = (650, -400)
    add_one.operation = 'ADD'
    add_one.inputs[1].default_value = 1.0
    links.new(exp_opacity.outputs[0], add_one.inputs[0])
    
    sigmoid_opacity = nodes.new('ShaderNodeMath')
    sigmoid_opacity.location = (800, -400)
    sigmoid_opacity.operation = 'DIVIDE'
    sigmoid_opacity.inputs[0].default_value = 1.0
    links.new(add_one.outputs[0], sigmoid_opacity.inputs[1])
    
    store_opacity = nodes.new('GeometryNodeStoreNamedAttribute')
    store_opacity.location = (500, -200)
    store_opacity.data_type = 'FLOAT'
    store_opacity.domain = 'INSTANCE'
    store_opacity.inputs['Name'].default_value = "inst_opacity"
    
    links.new(store_color.outputs['Geometry'], store_opacity.inputs['Geometry'])
    links.new(sigmoid_opacity.outputs[0], store_opacity.inputs['Value'])
    
    # === Realize Instances ===
    realize = nodes.new('GeometryNodeRealizeInstances')
    realize.location = (700, 0)
    
    links.new(store_opacity.outputs['Geometry'], realize.inputs['Geometry'])
    
    # === Compute Gaussian Alpha on Realized Geometry ===
    # After realization, Position gives local position within each instance
    # For normalized mesh (radius 1), position magnitude = distance from center
    position = nodes.new('GeometryNodeInputPosition')
    position.location = (850, -300)
    
    # Calculate distance² = x² + y² + z²
    dot_product = nodes.new('ShaderNodeVectorMath')
    dot_product.location = (1000, -300)
    dot_product.operation = 'DOT_PRODUCT'
    links.new(position.outputs['Position'], dot_product.inputs[0])
    links.new(position.outputs['Position'], dot_product.inputs[1])
    
    # Gaussian marginal: exp(-distance² * factor)
    # factor controls sharpness (higher = sharper edge)
    # Note: geo_size already scaled the mesh, so we need to account for that
    # Standard Gaussian: exp(-r²/2σ²) = exp(-r² * 0.5/σ²)
    scale_factor = nodes.new('ShaderNodeMath')
    scale_factor.location = (1150, -300)
    scale_factor.operation = 'MULTIPLY'
    scale_factor.inputs[1].default_value = 0.5  # Gaussian parameter
    links.new(dot_product.outputs['Value'], scale_factor.inputs[0])
    
    negate = nodes.new('ShaderNodeMath')
    negate.location = (1300, -300)
    negate.operation = 'MULTIPLY'
    negate.inputs[1].default_value = -1.0
    links.new(scale_factor.outputs[0], negate.inputs[0])
    
    gaussian_marginal = nodes.new('ShaderNodeMath')
    gaussian_marginal.location = (1450, -300)
    gaussian_marginal.operation = 'EXPONENT'
    links.new(negate.outputs[0], gaussian_marginal.inputs[0])
    
    # Get stored opacity
    get_inst_opacity = nodes.new('GeometryNodeInputNamedAttribute')
    get_inst_opacity.location = (1200, -500)
    get_inst_opacity.data_type = 'FLOAT'
    get_inst_opacity.inputs['Name'].default_value = "inst_opacity"
    
    # computeAlpha = opacity * marginal
    compute_alpha = nodes.new('ShaderNodeMath')
    compute_alpha.location = (1600, -400)
    compute_alpha.operation = 'MULTIPLY'
    links.new(get_inst_opacity.outputs['Attribute'], compute_alpha.inputs[0])
    links.new(gaussian_marginal.outputs[0], compute_alpha.inputs[1])
    
    # Store computeAlpha
    store_alpha = nodes.new('GeometryNodeStoreNamedAttribute')
    store_alpha.location = (900, 0)
    store_alpha.data_type = 'FLOAT'
    store_alpha.domain = 'POINT'
    store_alpha.inputs['Name'].default_value = "computeAlpha"
    
    links.new(realize.outputs['Geometry'], store_alpha.inputs['Geometry'])
    links.new(compute_alpha.outputs[0], store_alpha.inputs['Value'])
    
    # === Transfer Color to Realized Vertices ===
    get_inst_color = nodes.new('GeometryNodeInputNamedAttribute')
    get_inst_color.location = (900, -150)
    get_inst_color.data_type = 'FLOAT_COLOR'
    get_inst_color.inputs['Name'].default_value = "inst_color"
    
    store_final_color = nodes.new('GeometryNodeStoreNamedAttribute')
    store_final_color.location = (1100, 0)
    store_final_color.data_type = 'FLOAT_COLOR'
    store_final_color.domain = 'POINT'
    store_final_color.inputs['Name'].default_value = color_attr_name
    
    links.new(store_alpha.outputs['Geometry'], store_final_color.inputs['Geometry'])
    links.new(get_inst_color.outputs['Attribute'], store_final_color.inputs['Value'])
    
    # === Set Material ===
    set_material = nodes.new('GeometryNodeSetMaterial')
    set_material.location = (1300, 0)
    
    links.new(store_final_color.outputs['Geometry'], set_material.inputs['Geometry'])
    links.new(set_material.outputs['Geometry'], output_node.inputs['Geometry'])
    
    return modifier


def _create_gsplat_material_advanced(
    name: str,
    use_emission: bool,
    color_attr_name: str,
    shader_mode: ShaderMode,
    output_channel: OutputChannel
) -> bpy.types.Material:
    """
    Create advanced material for Gaussian splat display.
    
    For Gaussian shader mode, creates a disk-like splat with Gaussian falloff:
    - Center is bright/opaque
    - Edges fade to transparent using exp(-distance²) falloff
    
    Based on UGRS shader implementation.
    """
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    
    # Enable transparency
    mat.blend_method = 'BLEND'  # Use alpha blending
    # mat.shadow_method = 'HASHED'  # Better shadows with transparency
    mat.use_backface_culling = False
    
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    nodes.clear()
    
    # Output
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (1000, 0)
    
    # Color attribute
    attr_node = nodes.new('ShaderNodeAttribute')
    attr_node.location = (-600, 100)
    attr_node.attribute_name = color_attr_name
    attr_node.attribute_type = 'GEOMETRY'
    
    # Handle different output channels
    color_output = attr_node.outputs['Color']
    
    if output_channel == OutputChannel.NORMAL:
        geometry_node = nodes.new('ShaderNodeNewGeometry')
        geometry_node.location = (-400, 100)
        color_output = geometry_node.outputs['Normal']
        
        vector_math = nodes.new('ShaderNodeVectorMath')
        vector_math.location = (-200, 100)
        vector_math.operation = 'SCALE'
        vector_math.inputs[3].default_value = 0.5
        links.new(color_output, vector_math.inputs[0])
        
        add_node = nodes.new('ShaderNodeVectorMath')
        add_node.location = (0, 100)
        add_node.operation = 'ADD'
        add_node.inputs[1].default_value = (0.5, 0.5, 0.5)
        links.new(vector_math.outputs[0], add_node.inputs[0])
        
        color_output = add_node.outputs[0]
        
    elif output_channel == OutputChannel.DEPTH:
        camera_data = nodes.new('ShaderNodeCameraData')
        camera_data.location = (-400, 100)
        
        map_range = nodes.new('ShaderNodeMapRange')
        map_range.location = (-200, 100)
        map_range.inputs['From Min'].default_value = 0.0
        map_range.inputs['From Max'].default_value = 100.0
        links.new(camera_data.outputs['View Z Depth'], map_range.inputs['Value'])
        
        combine = nodes.new('ShaderNodeCombineColor')
        combine.location = (0, 100)
        links.new(map_range.outputs[0], combine.inputs['Red'])
        links.new(map_range.outputs[0], combine.inputs['Green'])
        links.new(map_range.outputs[0], combine.inputs['Blue'])
        
        color_output = combine.outputs['Color']
    
    # === GAUSSIAN SHADER MODE - Use pre-computed alpha from geometry nodes ===
    if shader_mode == ShaderMode.GAUSSIAN:
        # Read pre-computed alpha from geometry nodes
        # This is computed as: sigmoid(opacity) * exp(-distance²/2)
        alpha_attr = nodes.new('ShaderNodeAttribute')
        alpha_attr.location = (-200, -200)
        alpha_attr.attribute_name = 'computeAlpha'
        alpha_attr.attribute_type = 'GEOMETRY'
        
        # Emission shader for the color
        emission = nodes.new('ShaderNodeEmission')
        emission.location = (500, 100)
        emission.inputs['Strength'].default_value = 1.0
        links.new(color_output, emission.inputs['Color'])
        
        # Transparent shader
        transparent = nodes.new('ShaderNodeBsdfTransparent')
        transparent.location = (500, -50)
        
        # Mix based on pre-computed alpha
        mix_shader = nodes.new('ShaderNodeMixShader')
        mix_shader.location = (800, 0)
        links.new(alpha_attr.outputs['Fac'], mix_shader.inputs['Fac'])
        links.new(transparent.outputs['BSDF'], mix_shader.inputs[1])
        links.new(emission.outputs['Emission'], mix_shader.inputs[2])
        
        links.new(mix_shader.outputs['Shader'], output.inputs['Surface'])
        
    elif shader_mode == ShaderMode.RING:
        # Ring shader - hollow center using Generated coordinates
        tex_coord = nodes.new('ShaderNodeTexCoord')
        tex_coord.location = (-600, -200)
        
        # Map Generated coords from [0,1] to [-1,1]
        subtract_half = nodes.new('ShaderNodeVectorMath')
        subtract_half.location = (-400, -200)
        subtract_half.operation = 'SUBTRACT'
        subtract_half.inputs[1].default_value = (0.5, 0.5, 0.5)
        links.new(tex_coord.outputs['Generated'], subtract_half.inputs[0])
        
        scale_coords = nodes.new('ShaderNodeVectorMath')
        scale_coords.location = (-250, -200)
        scale_coords.operation = 'SCALE'
        scale_coords.inputs[3].default_value = 2.0
        links.new(subtract_half.outputs['Vector'], scale_coords.inputs[0])
        
        separate = nodes.new('ShaderNodeSeparateXYZ')
        separate.location = (-100, -200)
        links.new(scale_coords.outputs['Vector'], separate.inputs['Vector'])
        
        # Distance from center (2D for ring)
        x_sq = nodes.new('ShaderNodeMath')
        x_sq.location = (50, -100)
        x_sq.operation = 'POWER'
        x_sq.inputs[1].default_value = 2.0
        links.new(separate.outputs['X'], x_sq.inputs[0])
        
        y_sq = nodes.new('ShaderNodeMath')
        y_sq.location = (50, -250)
        y_sq.operation = 'POWER'
        y_sq.inputs[1].default_value = 2.0
        links.new(separate.outputs['Y'], y_sq.inputs[0])
        
        sum_sq = nodes.new('ShaderNodeMath')
        sum_sq.location = (200, -150)
        sum_sq.operation = 'ADD'
        links.new(x_sq.outputs[0], sum_sq.inputs[0])
        links.new(y_sq.outputs[0], sum_sq.inputs[1])
        
        dist = nodes.new('ShaderNodeMath')
        dist.location = (350, -150)
        dist.operation = 'SQRT'
        links.new(sum_sq.outputs[0], dist.inputs[0])
        
        # Ring effect: visible when distance is in a certain range
        # Inner radius check
        inner = nodes.new('ShaderNodeMath')
        inner.location = (500, -100)
        inner.operation = 'GREATER_THAN'
        inner.inputs[1].default_value = 0.3  # Inner radius
        links.new(dist.outputs[0], inner.inputs[0])
        
        # Outer radius check
        outer = nodes.new('ShaderNodeMath')
        outer.location = (500, -250)
        outer.operation = 'LESS_THAN'
        outer.inputs[1].default_value = 0.7  # Outer radius
        links.new(dist.outputs[0], outer.inputs[0])
        
        # Both conditions (ring mask)
        ring_mask = nodes.new('ShaderNodeMath')
        ring_mask.location = (650, -150)
        ring_mask.operation = 'MULTIPLY'
        links.new(inner.outputs[0], ring_mask.inputs[0])
        links.new(outer.outputs[0], ring_mask.inputs[1])
        
        emission = nodes.new('ShaderNodeEmission')
        emission.location = (500, 100)
        links.new(color_output, emission.inputs['Color'])
        
        transparent = nodes.new('ShaderNodeBsdfTransparent')
        transparent.location = (500, -50)
        
        mix_shader = nodes.new('ShaderNodeMixShader')
        mix_shader.location = (850, 0)
        links.new(ring_mask.outputs[0], mix_shader.inputs['Fac'])
        links.new(transparent.outputs['BSDF'], mix_shader.inputs[1])
        links.new(emission.outputs['Emission'], mix_shader.inputs[2])
        
        links.new(mix_shader.outputs['Shader'], output.inputs['Surface'])
        
    elif shader_mode == ShaderMode.WIREFRAME:
        wireframe = nodes.new('ShaderNodeWireframe')
        wireframe.location = (300, -100)
        wireframe.inputs['Size'].default_value = 0.02
        
        emission = nodes.new('ShaderNodeEmission')
        emission.location = (500, 100)
        links.new(color_output, emission.inputs['Color'])
        
        transparent = nodes.new('ShaderNodeBsdfTransparent')
        transparent.location = (500, -50)
        
        mix_shader = nodes.new('ShaderNodeMixShader')
        mix_shader.location = (800, 0)
        links.new(wireframe.outputs['Fac'], mix_shader.inputs['Fac'])
        links.new(transparent.outputs['BSDF'], mix_shader.inputs[1])
        links.new(emission.outputs['Emission'], mix_shader.inputs[2])
        
        links.new(mix_shader.outputs['Shader'], output.inputs['Surface'])
        
    else:
        # Freestyle / default - solid emission
        emission = nodes.new('ShaderNodeEmission')
        emission.location = (500, 0)
        emission.inputs['Strength'].default_value = 1.0
        links.new(color_output, emission.inputs['Color'])
        links.new(emission.outputs['Emission'], output.inputs['Surface'])
    
    return mat


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
