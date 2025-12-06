"""
3D Bounding Box Visualization Module

Creates dynamic bounding box visualizations for objects.
Supports both static and animated meshes (via frame handler).
"""

import bpy
import mathutils

from . import base


def get_object_bounds(obj, depsgraph=None):
    """
    Get the world-space 8 corners of the object's bounding box.
    """
    return base.get_object_world_bounds(obj, depsgraph)


def create_bbox_mesh_data(name="BBoxMesh"):
    """Create a cube mesh for the bounding box."""
    mesh = bpy.data.meshes.new(name)
    
    # Cube vertices (standard -1 to 1)
    vertices = [
        (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
        (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)
    ]
    
    # Edges for wireframe look
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0), # Bottom face
        (4, 5), (5, 6), (6, 7), (7, 4), # Top face
        (0, 4), (1, 5), (2, 6), (3, 7)  # Vertical pillars
    ]
    
    mesh.from_pydata(vertices, edges, [])
    mesh.update()
    return mesh


def create_embedded_bbox_script():
    """
    Create an embedded script that runs when the blend file is opened.
    This ensures the BBox updates during animation playback.
    """
    script_name = "bbox_driver.py"
    if script_name in bpy.data.texts:
        return bpy.data.texts[script_name]
        
    script_text = '''"""
BBox Annotation Driver
This script is automatically generated to animate bounding boxes.
"""
import bpy
import mathutils

def bbox_get_object_bounds(obj, depsgraph=None):
    if depsgraph:
        try:
            obj_eval = obj.evaluated_get(depsgraph)
            corners = [obj_eval.matrix_world @ mathutils.Vector(corner) for corner in obj_eval.bound_box]
            return corners
        except Exception as e:
            pass
    corners = [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]
    return corners

def bbox_update_single(bbox_obj, depsgraph=None):
    if not bbox_obj or "target_object" not in bbox_obj:
        return
        
    target_name = bbox_obj["target_object"]
    target_obj = bpy.data.objects.get(target_name)
    if not target_obj:
        return

    corners = bbox_get_object_bounds(target_obj, depsgraph)
    if len(bbox_obj.data.vertices) != 8:
        return

    for i, corner in enumerate(corners):
        if i < len(bbox_obj.data.vertices):
            bbox_obj.data.vertices[i].co = corner

    bbox_obj.data.update()

def bbox_update_all(scene):
    collection = bpy.data.collections.get("AnnotationViz")
    if not collection:
        return
        
    try:
        depsgraph = bpy.context.evaluated_depsgraph_get()
    except:
        depsgraph = None
    
    for obj in collection.objects:
        if "target_object" in obj and obj.name.startswith("BBox_"):
            bbox_update_single(obj, depsgraph)

def bbox_frame_handler(scene):
    bbox_update_all(scene)

def register():
    handlers = bpy.app.handlers.frame_change_post
    for h in list(handlers):
        if hasattr(h, '__name__') and h.__name__ == 'bbox_frame_handler':
            handlers.remove(h)
    handlers.append(bbox_frame_handler)
    print("✅ BBox Annotation Handler Registered")

# Auto-register on load
register()
'''
    return base.create_embedded_script(script_name, script_text)


def create_bbox_annotation(target_obj, color=(1.0, 0.6, 0.0, 1.0), thickness=2.0, 
                           collection_name=None):
    """
    Create a bounding box annotation for the target object.
    
    Args:
        target_obj: The object to track
        color: RGBA color tuple
        thickness: Line thickness (only visible in some modes/renders)
        collection_name: Collection to put the annotation in
    
    Returns:
        bbox_obj: The visualization object
    """
    if not target_obj:
        return None
        
    # Ensure collection exists
    collection = base.ensure_collection(collection_name)
        
    # Create visualization object
    mesh = create_bbox_mesh_data(f"BBox_{target_obj.name}")
    bbox_obj = bpy.data.objects.new(f"BBox_{target_obj.name}", mesh)
    collection.objects.link(bbox_obj)
    
    # Setup material using base utility
    mat = base.create_emission_material(
        f"BBoxMat_{target_obj.name}",
        color=color,
        strength=1.0
    )
    bbox_obj.data.materials.append(mat)
    
    # Store target reference
    bbox_obj["target_object"] = target_obj.name
    bbox_obj["annotation_type"] = "bbox"
    
    # Initial update
    update_bbox(bbox_obj)
    
    return bbox_obj


def update_bbox(bbox_obj, depsgraph=None):
    """Update the bounding box vertices to match the target object."""
    if not bbox_obj or "target_object" not in bbox_obj:
        return
        
    target_name = bbox_obj["target_object"]
    target_obj = bpy.data.objects.get(target_name)
    
    if not target_obj:
        return

    # Get bounds
    corners = get_object_bounds(target_obj, depsgraph)
    
    if len(bbox_obj.data.vertices) != 8:
        return
    
    for i, corner in enumerate(corners):
        if i < len(bbox_obj.data.vertices):
            bbox_obj.data.vertices[i].co = corner

    bbox_obj.data.update()


def update_all_bboxes(scene):
    """Frame change handler to update all bboxes."""
    collection = bpy.data.collections.get(base.DEFAULT_COLLECTION_NAME)
    if not collection:
        return
        
    depsgraph = base.get_depsgraph()
    
    for obj in collection.objects:
        # Only update objects that are bboxes (have target_object and name starts with BBox_)
        if "target_object" in obj and obj.name.startswith("BBox_"):
            update_bbox(obj, depsgraph)


def register():
    """Register frame handler."""
    
    # Create embedded script so it persists
    create_embedded_bbox_script()
    
    # Also ensure the embedded script is registered to run on load
    if "bbox_driver.py" in bpy.data.texts:
        bpy.data.texts["bbox_driver.py"].use_module = True
            
    def bbox_frame_handler(scene):
        update_all_bboxes(scene)
        
    base.register_frame_handler(bbox_frame_handler, "bbox_frame_handler")
    print("✅ BBox Annotation Handler Registered")


if __name__ == "__main__":
    register()
