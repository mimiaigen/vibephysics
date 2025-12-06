"""
Base Annotation Module

Provides common utilities and base classes for all annotation types.
This enables easy extension and unified control of annotations.
"""

import bpy
from abc import ABC, abstractmethod


# =============================================================================
# Constants
# =============================================================================

DEFAULT_COLLECTION_NAME = "AnnotationViz"


# =============================================================================
# Collection Utilities
# =============================================================================

def ensure_collection(name=None):
    """
    Get or create an annotation collection.
    
    Args:
        name: Collection name (defaults to DEFAULT_COLLECTION_NAME)
        
    Returns:
        bpy.types.Collection
    """
    collection_name = name or DEFAULT_COLLECTION_NAME
    
    if collection_name not in bpy.data.collections:
        collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(collection)
    else:
        collection = bpy.data.collections[collection_name]
        
    return collection


def find_layer_collection(layer_collection, collection_name):
    """Recursively find a layer collection by name."""
    if layer_collection.name == collection_name:
        return layer_collection
    
    for child in layer_collection.children:
        result = find_layer_collection(child, collection_name)
        if result:
            return result
    
    return None


# =============================================================================
# Material Utilities
# =============================================================================

def create_emission_material(name, color, strength=1.0):
    """
    Create a standard emission material for annotations.
    
    Args:
        name: Material name
        color: RGBA color tuple (r, g, b, a)
        strength: Emission strength
        
    Returns:
        bpy.types.Material
    """
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    node_out = nodes.new(type='ShaderNodeOutputMaterial')
    node_emission = nodes.new(type='ShaderNodeEmission')
    
    node_emission.inputs['Color'].default_value = color
    node_emission.inputs['Strength'].default_value = strength
    
    links.new(node_emission.outputs['Emission'], node_out.inputs['Surface'])
    
    return mat


def create_vertex_color_material(name, color_layer_name="PointColors", strength=2.0):
    """
    Create a material that displays vertex colors.
    
    Args:
        name: Material name
        color_layer_name: Name of the vertex color layer
        strength: Emission strength
        
    Returns:
        bpy.types.Material
    """
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    node_out = nodes.new(type='ShaderNodeOutputMaterial')
    node_emission = nodes.new(type='ShaderNodeEmission')
    node_vcol = nodes.new(type='ShaderNodeVertexColor')
    node_vcol.layer_name = color_layer_name
    
    node_emission.inputs['Strength'].default_value = strength
    
    links.new(node_vcol.outputs['Color'], node_emission.inputs['Color'])
    links.new(node_emission.outputs['Emission'], node_out.inputs['Surface'])
    
    return mat


# =============================================================================
# Frame Handler Utilities
# =============================================================================

def register_frame_handler(handler_func, handler_name=None):
    """
    Register a frame change handler, removing any existing handler with the same name.
    
    Args:
        handler_func: The handler function to register
        handler_name: Name for identification (uses function name if not provided)
    """
    if handler_name:
        handler_func.__name__ = handler_name
    else:
        handler_name = handler_func.__name__
    
    handlers = bpy.app.handlers.frame_change_post
    
    # Remove existing handlers with the same name
    for h in list(handlers):
        if hasattr(h, '__name__') and h.__name__ == handler_name:
            handlers.remove(h)
    
    handlers.append(handler_func)
    return handler_func


def unregister_frame_handler(handler_name):
    """
    Unregister a frame change handler by name.
    
    Args:
        handler_name: Name of the handler to remove
    """
    handlers = bpy.app.handlers.frame_change_post
    
    for h in list(handlers):
        if hasattr(h, '__name__') and h.__name__ == handler_name:
            handlers.remove(h)


# =============================================================================
# Embedded Script Utilities
# =============================================================================

def create_embedded_script(script_name, script_content, use_module=True):
    """
    Create an embedded script in the blend file.
    
    These scripts can run on file load to restore functionality
    like frame handlers.
    
    Args:
        script_name: Name for the script (e.g., "my_driver.py")
        script_content: The Python script content
        use_module: Whether to mark as module (runs on load)
        
    Returns:
        bpy.types.Text block
    """
    if script_name in bpy.data.texts:
        return bpy.data.texts[script_name]
    
    text_block = bpy.data.texts.new(script_name)
    text_block.write(script_content)
    text_block.use_module = use_module
    
    return text_block


def get_embedded_script(script_name):
    """Get an existing embedded script by name."""
    return bpy.data.texts.get(script_name)


# =============================================================================
# Object Utilities
# =============================================================================

def get_object_world_bounds(obj, depsgraph=None):
    """
    Get the world-space 8 corners of an object's bounding box.
    
    Args:
        obj: The Blender object
        depsgraph: Optional dependency graph for evaluated mesh
        
    Returns:
        List of 8 Vector corners
    """
    import mathutils
    
    if depsgraph:
        try:
            obj_eval = obj.evaluated_get(depsgraph)
            corners = [obj_eval.matrix_world @ mathutils.Vector(corner) 
                      for corner in obj_eval.bound_box]
            return corners
        except:
            pass
    
    corners = [obj.matrix_world @ mathutils.Vector(corner) 
              for corner in obj.bound_box]
    return corners


def get_evaluated_object(obj, depsgraph=None):
    """
    Get the evaluated version of an object (with modifiers/physics applied).
    
    Args:
        obj: The Blender object
        depsgraph: Optional dependency graph
        
    Returns:
        Evaluated object or original if evaluation fails
    """
    if not depsgraph:
        try:
            depsgraph = bpy.context.evaluated_depsgraph_get()
        except:
            return obj
    
    try:
        return obj.evaluated_get(depsgraph)
    except:
        return obj


def get_depsgraph():
    """Safely get the current dependency graph."""
    try:
        return bpy.context.evaluated_depsgraph_get()
    except:
        return None


# =============================================================================
# Base Annotation Class
# =============================================================================

class BaseAnnotation(ABC):
    """
    Abstract base class for all annotation types.
    
    Subclasses should implement:
    - create(): Create the annotation visualization
    - update(): Update the annotation (for animated annotations)
    - get_handler_name(): Return a unique handler name
    - get_embedded_script(): Return embedded script content
    """
    
    # Class-level registry of annotation types
    _registry = {}
    
    def __init__(self, target_obj, collection_name=None):
        """
        Initialize annotation.
        
        Args:
            target_obj: The object to annotate
            collection_name: Collection to put annotation in
        """
        self.target_obj = target_obj
        self.collection_name = collection_name or DEFAULT_COLLECTION_NAME
        self.viz_object = None
        
    @abstractmethod
    def create(self):
        """Create the annotation visualization object."""
        pass
    
    def update(self, depsgraph=None):
        """Update the annotation (override for animated annotations)."""
        pass
    
    @classmethod
    def get_handler_name(cls):
        """Return unique handler name for this annotation type."""
        return f"{cls.__name__}_frame_handler"
    
    @classmethod
    def get_embedded_script_name(cls):
        """Return embedded script name for this annotation type."""
        return f"{cls.__name__}_driver.py"
    
    @classmethod
    def get_embedded_script_content(cls):
        """Return embedded script content. Override in subclasses."""
        return None
    
    @classmethod
    def register_handler(cls):
        """Register the frame change handler for this annotation type."""
        pass
    
    @classmethod
    def create_embedded_script(cls):
        """Create the embedded script for this annotation type."""
        content = cls.get_embedded_script_content()
        if content:
            return create_embedded_script(
                cls.get_embedded_script_name(), 
                content
            )
        return None
    
    @classmethod
    def register(cls, name=None):
        """Register this annotation type in the global registry."""
        key = name or cls.__name__
        cls._registry[key] = cls
    
    @classmethod
    def get_registered(cls, name):
        """Get a registered annotation type by name."""
        return cls._registry.get(name)
    
    @classmethod
    def list_registered(cls):
        """List all registered annotation types."""
        return list(cls._registry.keys())


# =============================================================================
# Annotation Factory
# =============================================================================

class AnnotationType:
    """Enum-like class for annotation types."""
    BBOX = "bbox"
    MOTION_TRAIL = "motion_trail"
    POINT_TRACKING = "point_tracking"


def create_annotation(annotation_type, target_obj, **kwargs):
    """
    Factory function to create annotations.
    
    Args:
        annotation_type: Type of annotation (use AnnotationType constants)
        target_obj: Object to annotate
        **kwargs: Additional arguments for the specific annotation type
        
    Returns:
        The created annotation visualization object
    """
    # Import here to avoid circular imports
    from . import bbox as bbox_module
    from . import motion_trail as trail_module
    from . import point_tracking as tracking_module
    
    if annotation_type == AnnotationType.BBOX:
        return bbox_module.create_bbox_annotation(target_obj, **kwargs)
    elif annotation_type == AnnotationType.MOTION_TRAIL:
        return trail_module.create_motion_trail(target_obj, **kwargs)
    elif annotation_type == AnnotationType.POINT_TRACKING:
        # Point tracking takes a list of objects
        return tracking_module.setup_point_tracking_visualization([target_obj], **kwargs)
    else:
        raise ValueError(f"Unknown annotation type: {annotation_type}")
