"""
Scene Export Module

Save and export Blender scenes and objects.
Supports: BLEND, GLB, GLTF, FBX, OBJ, PLY, STL, USD formats.
"""
import bpy
import os


# =============================================================================
# Save Blend File
# =============================================================================

def save_blend(filepath, compress=False):
    """
    Save the current scene as a .blend file.
    
    Args:
        filepath: Output path (adds .blend extension if missing)
        compress: Whether to compress the file
        
    Returns:
        True if successful, False otherwise
    """
    if not filepath.endswith('.blend'):
        filepath += '.blend'
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    
    try:
        bpy.ops.wm.save_as_mainfile(filepath=filepath, compress=compress)
        print(f"✅ Saved blend file: {filepath}")
        return True
    except Exception as e:
        print(f"⚠️ Failed to save blend file: {e}")
        return False


def save_copy(filepath, compress=False):
    """
    Save a copy without changing the current file path.
    
    Args:
        filepath: Output path
        compress: Whether to compress the file
        
    Returns:
        True if successful, False otherwise
    """
    if not filepath.endswith('.blend'):
        filepath += '.blend'
    
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    
    try:
        bpy.ops.wm.save_as_mainfile(filepath=filepath, compress=compress, copy=True)
        print(f"✅ Saved copy: {filepath}")
        return True
    except Exception as e:
        print(f"⚠️ Failed to save copy: {e}")
        return False


# =============================================================================
# Export Functions
# =============================================================================

def export_glb(filepath, selected_only=False, apply_modifiers=True):
    """
    Export scene or selected objects to GLB format.
    
    Args:
        filepath: Output path (adds .glb extension if missing)
        selected_only: Export only selected objects
        apply_modifiers: Apply modifiers before export
        
    Returns:
        True if successful, False otherwise
    """
    if not filepath.endswith('.glb'):
        filepath += '.glb'
    
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    
    try:
        bpy.ops.export_scene.gltf(
            filepath=filepath,
            export_format='GLB',
            use_selection=selected_only,
            export_apply=apply_modifiers
        )
        print(f"✅ Exported GLB: {filepath}")
        return True
    except Exception as e:
        print(f"⚠️ Failed to export GLB: {e}")
        return False


def export_gltf(filepath, selected_only=False, apply_modifiers=True):
    """
    Export scene or selected objects to GLTF format (separate files).
    
    Args:
        filepath: Output path (adds .gltf extension if missing)
        selected_only: Export only selected objects
        apply_modifiers: Apply modifiers before export
        
    Returns:
        True if successful, False otherwise
    """
    if not filepath.endswith('.gltf'):
        filepath += '.gltf'
    
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    
    try:
        bpy.ops.export_scene.gltf(
            filepath=filepath,
            export_format='GLTF_SEPARATE',
            use_selection=selected_only,
            export_apply=apply_modifiers
        )
        print(f"✅ Exported GLTF: {filepath}")
        return True
    except Exception as e:
        print(f"⚠️ Failed to export GLTF: {e}")
        return False


def export_fbx(filepath, selected_only=False, apply_modifiers=True):
    """
    Export scene or selected objects to FBX format.
    
    Args:
        filepath: Output path (adds .fbx extension if missing)
        selected_only: Export only selected objects
        apply_modifiers: Apply modifiers before export
        
    Returns:
        True if successful, False otherwise
    """
    if not filepath.endswith('.fbx'):
        filepath += '.fbx'
    
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    
    try:
        bpy.ops.export_scene.fbx(
            filepath=filepath,
            use_selection=selected_only,
            use_mesh_modifiers=apply_modifiers
        )
        print(f"✅ Exported FBX: {filepath}")
        return True
    except Exception as e:
        print(f"⚠️ Failed to export FBX: {e}")
        return False


def export_obj(filepath, selected_only=False, apply_modifiers=True):
    """
    Export scene or selected objects to OBJ format.
    
    Args:
        filepath: Output path (adds .obj extension if missing)
        selected_only: Export only selected objects
        apply_modifiers: Apply modifiers before export
        
    Returns:
        True if successful, False otherwise
    """
    if not filepath.endswith('.obj'):
        filepath += '.obj'
    
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    
    try:
        bpy.ops.wm.obj_export(
            filepath=filepath,
            export_selected_objects=selected_only,
            apply_modifiers=apply_modifiers
        )
        print(f"✅ Exported OBJ: {filepath}")
        return True
    except Exception as e:
        # Try legacy export
        try:
            bpy.ops.export_scene.obj(
                filepath=filepath,
                use_selection=selected_only,
                use_mesh_modifiers=apply_modifiers
            )
            print(f"✅ Exported OBJ: {filepath}")
            return True
        except Exception as e2:
            print(f"⚠️ Failed to export OBJ: {e2}")
            return False


def export_ply(filepath, selected_only=True, apply_modifiers=True):
    """
    Export mesh to PLY format.
    
    Note: PLY export typically works with a single active mesh object.
    
    Args:
        filepath: Output path (adds .ply extension if missing)
        selected_only: Export only selected objects
        apply_modifiers: Apply modifiers before export
        
    Returns:
        True if successful, False otherwise
    """
    if not filepath.endswith('.ply'):
        filepath += '.ply'
    
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    
    try:
        bpy.ops.wm.ply_export(
            filepath=filepath,
            export_selected_objects=selected_only,
            apply_modifiers=apply_modifiers
        )
        print(f"✅ Exported PLY: {filepath}")
        return True
    except Exception as e:
        try:
            bpy.ops.export_mesh.ply(
                filepath=filepath,
                use_selection=selected_only,
                use_mesh_modifiers=apply_modifiers
            )
            print(f"✅ Exported PLY: {filepath}")
            return True
        except Exception as e2:
            print(f"⚠️ Failed to export PLY: {e2}")
            return False


def export_stl(filepath, selected_only=False, apply_modifiers=True):
    """
    Export mesh to STL format.
    
    Args:
        filepath: Output path (adds .stl extension if missing)
        selected_only: Export only selected objects
        apply_modifiers: Apply modifiers before export
        
    Returns:
        True if successful, False otherwise
    """
    if not filepath.endswith('.stl'):
        filepath += '.stl'
    
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    
    try:
        bpy.ops.wm.stl_export(
            filepath=filepath,
            export_selected_objects=selected_only,
            apply_modifiers=apply_modifiers
        )
        print(f"✅ Exported STL: {filepath}")
        return True
    except Exception as e:
        try:
            bpy.ops.export_mesh.stl(
                filepath=filepath,
                use_selection=selected_only,
                use_mesh_modifiers=apply_modifiers
            )
            print(f"✅ Exported STL: {filepath}")
            return True
        except Exception as e2:
            print(f"⚠️ Failed to export STL: {e2}")
            return False


def export_usd(filepath, selected_only=False):
    """
    Export scene to USD format.
    
    Args:
        filepath: Output path (adds .usd extension if missing)
        selected_only: Export only selected objects
        
    Returns:
        True if successful, False otherwise
    """
    if not any(filepath.endswith(ext) for ext in ('.usd', '.usda', '.usdc', '.usdz')):
        filepath += '.usd'
    
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    
    try:
        bpy.ops.wm.usd_export(
            filepath=filepath,
            selected_objects_only=selected_only
        )
        print(f"✅ Exported USD: {filepath}")
        return True
    except Exception as e:
        print(f"⚠️ Failed to export USD: {e}")
        return False


# =============================================================================
# Batch Export
# =============================================================================

def export_selected(filepath, format='glb', apply_modifiers=True):
    """
    Export selected objects to specified format.
    
    Args:
        filepath: Output path (extension added based on format)
        format: Output format ('glb', 'gltf', 'fbx', 'obj', 'ply', 'stl', 'usd')
        apply_modifiers: Apply modifiers before export
        
    Returns:
        True if successful, False otherwise
    """
    format = format.lower()
    
    exporters = {
        'glb': lambda: export_glb(filepath, selected_only=True, apply_modifiers=apply_modifiers),
        'gltf': lambda: export_gltf(filepath, selected_only=True, apply_modifiers=apply_modifiers),
        'fbx': lambda: export_fbx(filepath, selected_only=True, apply_modifiers=apply_modifiers),
        'obj': lambda: export_obj(filepath, selected_only=True, apply_modifiers=apply_modifiers),
        'ply': lambda: export_ply(filepath, selected_only=True, apply_modifiers=apply_modifiers),
        'stl': lambda: export_stl(filepath, selected_only=True, apply_modifiers=apply_modifiers),
        'usd': lambda: export_usd(filepath, selected_only=True),
    }
    
    if format not in exporters:
        print(f"⚠️ Unsupported export format: {format}")
        print(f"   Supported formats: {', '.join(exporters.keys())}")
        return False
    
    return exporters[format]()


def export_objects(objects, filepath, format='glb', apply_modifiers=True):
    """
    Export specific objects to file.
    
    Args:
        objects: List of objects to export
        filepath: Output path
        format: Output format
        apply_modifiers: Apply modifiers before export
        
    Returns:
        True if successful, False otherwise
    """
    # Deselect all, then select only the target objects
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        if obj and obj.name in bpy.data.objects:
            obj.select_set(True)
    
    return export_selected(filepath, format=format, apply_modifiers=apply_modifiers)


# =============================================================================
# Utility Functions
# =============================================================================

def ensure_output_dir(filepath):
    """
    Ensure the output directory exists.
    
    Args:
        filepath: File path or directory path
        
    Returns:
        Absolute path to the directory
    """
    dirpath = os.path.dirname(os.path.abspath(filepath))
    os.makedirs(dirpath, exist_ok=True)
    return dirpath


def get_output_path(filename, output_dir=None):
    """
    Get full output path, creating directory if needed.
    
    Args:
        filename: Output filename
        output_dir: Optional output directory (defaults to ./output/)
        
    Returns:
        Full absolute path
    """
    if output_dir is None:
        output_dir = os.path.join(os.getcwd(), 'output')
    
    os.makedirs(output_dir, exist_ok=True)
    return os.path.join(output_dir, filename)
