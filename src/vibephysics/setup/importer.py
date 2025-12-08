"""
Asset Import Module

Load 3D assets into Blender scenes.
Supports: GLB, GLTF, FBX, PLY, OBJ, BLEND files, and Gaussian Splats.
"""
import bpy
import os
import math


# =============================================================================
# Main Import Function
# =============================================================================

def load_asset(filepath, collection_name=None, transform=None):
    """
    Load a 3D asset file into the scene.
    
    Supports: .glb, .gltf, .fbx, .ply, .obj, .blend
    
    Args:
        filepath: Path to the asset file
        collection_name: Optional collection to place imported objects in
        transform: Optional dict with 'location', 'rotation', 'scale' keys
    
    Returns:
        List of imported objects
    
    Example:
        objects = load_asset('robot.glb', transform={'scale': 0.5})
        objects = load_asset('mesh.ply', collection_name='PointClouds')
    """
    if not os.path.exists(filepath):
        print(f"⚠️ Asset file not found: {filepath}")
        return []
    
    ext = os.path.splitext(filepath)[1].lower()
    
    # Track existing objects to identify new ones
    existing_objects = set(bpy.data.objects)
    
    # Import based on file type
    success = False
    if ext in ('.glb', '.gltf'):
        success = _load_gltf(filepath)
    elif ext == '.fbx':
        success = _load_fbx(filepath)
    elif ext == '.ply':
        success = _load_ply(filepath)
    elif ext == '.obj':
        success = _load_obj(filepath)
    elif ext == '.blend':
        success = _load_blend(filepath)
    elif ext == '.stl':
        success = _load_stl(filepath)
    elif ext == '.dae':
        success = _load_collada(filepath)
    elif ext in ('.usd', '.usda', '.usdc', '.usdz'):
        success = _load_usd(filepath)
    else:
        print(f"⚠️ Unsupported file format: {ext}")
        return []
    
    if not success:
        return []
    
    # Get newly imported objects
    new_objects = [obj for obj in bpy.data.objects if obj not in existing_objects]
    
    # Move to collection if specified
    if collection_name and new_objects:
        move_to_collection(new_objects, collection_name)
    
    # Apply transform if specified
    if transform and new_objects:
        apply_transform(new_objects, transform)
    
    print(f"✅ Loaded {len(new_objects)} objects from {os.path.basename(filepath)}")
    return new_objects


# =============================================================================
# Format-Specific Loaders
# =============================================================================

def _load_gltf(filepath):
    """Load GLTF/GLB file."""
    try:
        bpy.ops.import_scene.gltf(filepath=filepath)
        return True
    except Exception as e:
        print(f"⚠️ Failed to load GLTF: {e}")
        return False


def _load_fbx(filepath):
    """Load FBX file."""
    try:
        bpy.ops.import_scene.fbx(filepath=filepath)
        return True
    except Exception as e:
        print(f"⚠️ Failed to load FBX: {e}")
        return False


def _load_ply(filepath):
    """Load PLY file (point cloud or mesh)."""
    try:
        bpy.ops.wm.ply_import(filepath=filepath)
        return True
    except Exception as e:
        # Try legacy import
        try:
            bpy.ops.import_mesh.ply(filepath=filepath)
            return True
        except Exception as e2:
            print(f"⚠️ Failed to load PLY: {e2}")
            return False


def _load_obj(filepath):
    """Load OBJ file."""
    try:
        bpy.ops.wm.obj_import(filepath=filepath)
        return True
    except Exception as e:
        # Try legacy import
        try:
            bpy.ops.import_scene.obj(filepath=filepath)
            return True
        except Exception as e2:
            print(f"⚠️ Failed to load OBJ: {e2}")
            return False


def _load_blend(filepath, link=False):
    """
    Load objects from a .blend file.
    
    Args:
        filepath: Path to .blend file
        link: If True, link objects; if False, append (copy) them
    """
    try:
        with bpy.data.libraries.load(filepath, link=link) as (data_from, data_to):
            data_to.objects = data_from.objects
        
        # Link objects to scene
        for obj in data_to.objects:
            if obj is not None:
                bpy.context.scene.collection.objects.link(obj)
        
        return True
    except Exception as e:
        print(f"⚠️ Failed to load blend file: {e}")
        return False


def _load_stl(filepath):
    """Load STL file."""
    try:
        bpy.ops.wm.stl_import(filepath=filepath)
        return True
    except Exception as e:
        try:
            bpy.ops.import_mesh.stl(filepath=filepath)
            return True
        except Exception as e2:
            print(f"⚠️ Failed to load STL: {e2}")
            return False


def _load_collada(filepath):
    """Load Collada DAE file."""
    try:
        bpy.ops.wm.collada_import(filepath=filepath)
        return True
    except Exception as e:
        print(f"⚠️ Failed to load Collada: {e}")
        return False


def _load_usd(filepath):
    """Load USD/USDA/USDC/USDZ file."""
    try:
        bpy.ops.wm.usd_import(filepath=filepath)
        return True
    except Exception as e:
        print(f"⚠️ Failed to load USD: {e}")
        return False


# =============================================================================
# Convenience Functions
# =============================================================================

def load_glb(filepath, **kwargs):
    """Load GLB/GLTF file."""
    return load_asset(filepath, **kwargs)


def load_fbx(filepath, **kwargs):
    """Load FBX file."""
    return load_asset(filepath, **kwargs)


def load_ply(filepath, **kwargs):
    """Load PLY file (point cloud or mesh)."""
    return load_asset(filepath, **kwargs)


def load_obj(filepath, **kwargs):
    """Load OBJ file."""
    return load_asset(filepath, **kwargs)


def load_blend(filepath, **kwargs):
    """Load objects from blend file."""
    return load_asset(filepath, **kwargs)


def load_stl(filepath, **kwargs):
    """Load STL file."""
    return load_asset(filepath, **kwargs)


def load_usd(filepath, **kwargs):
    """Load USD file."""
    return load_asset(filepath, **kwargs)


# =============================================================================
# Transform Utilities
# =============================================================================

def move_to_collection(objects, collection_name):
    """
    Move objects to a specific collection.
    
    Args:
        objects: List of Blender objects
        collection_name: Name of target collection (created if doesn't exist)
    """
    # Get or create collection
    if collection_name not in bpy.data.collections:
        collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(collection)
    else:
        collection = bpy.data.collections[collection_name]
    
    for obj in objects:
        # Unlink from current collections
        for coll in obj.users_collection:
            coll.objects.unlink(obj)
        # Link to target collection
        collection.objects.link(obj)


def apply_transform(objects, transform):
    """
    Apply transform to objects.
    
    Args:
        objects: List of objects
        transform: Dict with optional keys:
            - 'location': (x, y, z) tuple
            - 'rotation': (rx, ry, rz) tuple in radians or degrees
            - 'scale': float (uniform) or (sx, sy, sz) tuple
    """
    location = transform.get('location')
    rotation = transform.get('rotation')
    scale = transform.get('scale')
    
    for obj in objects:
        if location:
            obj.location = location
        
        if rotation:
            # Check if rotation values are likely degrees (> 2*pi)
            rx, ry, rz = rotation
            if max(abs(rx), abs(ry), abs(rz)) > 6.28:
                # Likely degrees, convert to radians
                rx, ry, rz = math.radians(rx), math.radians(ry), math.radians(rz)
            obj.rotation_euler = (rx, ry, rz)
        
        if scale is not None:
            if isinstance(scale, (int, float)):
                obj.scale = (scale, scale, scale)
            else:
                obj.scale = scale


def ensure_collection(name):
    """
    Get or create a collection.
    
    Args:
        name: Collection name
        
    Returns:
        bpy.types.Collection
    """
    if name not in bpy.data.collections:
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
    else:
        collection = bpy.data.collections[name]
    return collection


# =============================================================================
# Gaussian Splatting Support
# =============================================================================

def load_gsplat(path, collection_name="GaussianSplat", frame_start=1, setup_animation=True):
    """
    Load Gaussian Splatting data (3DGS or 4DGS).
    
    - If path is a .ply file -> loads as 3DGS (single frame)
    - If path is a folder -> loads as 4DGS sequence (animated)
    
    Args:
        path: Path to PLY file or folder with PLY sequence
        collection_name: Collection name for the splat(s)
        frame_start: Starting frame for 4DGS animation
        setup_animation: Auto-setup visibility animation for sequences
    
    Returns:
        Object (3DGS) or Collection (4DGS sequence)
    
    Example:
        # Single Gaussian splat
        obj = load_gsplat('scene.ply')
        
        # Animated sequence
        collection = load_gsplat('frames/')
    """
    from . import gsplat
    return gsplat.load_gsplat(path, collection_name, frame_start, setup_animation)


def load_3dgs(filepath, name=None, collection_name=None, transform=None):
    """
    Load a 3D Gaussian Splatting PLY file.
    
    Args:
        filepath: Path to .ply file
        name: Optional object name
        collection_name: Optional collection
        transform: Optional transform dict
    
    Returns:
        Imported object
    """
    from . import gsplat
    return gsplat.load_3dgs(filepath, name, collection_name, transform)


def load_4dgs_sequence(folder_path, prefix="", suffix=".ply", collection_name="4DGS_Sequence",
                       frame_start=1, setup_animation=True):
    """
    Load a 4D Gaussian Splatting sequence from a folder.
    
    Args:
        folder_path: Folder containing PLY files
        prefix: File name prefix (e.g., "frame_")
        suffix: File extension (default ".ply")
        collection_name: Collection name
        frame_start: Animation start frame
        setup_animation: Auto-setup visibility animation
    
    Returns:
        Collection containing all frames
    """
    from . import gsplat
    return gsplat.load_4dgs_sequence(folder_path, prefix, suffix, collection_name,
                                      frame_start, setup_animation)
