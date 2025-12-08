"""
Demo: 3D Gaussian Splatting Viewer with Dual Viewport

Demonstrates loading a 3DGS PLY file with dual viewport:
- Left viewport: Material/rendered view (Gaussian splat colors)
- Right viewport: Point cloud view (solid with vertex colors)

Usage:
    python demo_3dgs_viewer.py --input /path/to/splat.ply
    
    # Or with default test file:
    python demo_3dgs_viewer.py
"""

import sys
import os
import bpy
import argparse
import mathutils

# Setup imports (works with both pip install and local development)
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(_root, 'src'))

from vibephysics.setup import (
    save_blend,
    clear_scene,
    load_gsplat,
    setup_dual_viewport,
    setup_gsplat_display,
)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='3D Gaussian Splatting Viewer with Dual Viewport',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument('--input', '-i', type=str,
                        default='/Users/shamangary/codeDemo/marble/almond tree/almond_tree_marble.ply',
                        help='Path to 3DGS PLY file')
    parser.add_argument('--output', '-o', type=str, default='demo_3dgs_viewer.blend',
                        help='Output blend file name')
    parser.add_argument('--point-size', type=float, default=0.005,
                        help='Point size for visualization')
    parser.add_argument('--no-dual-viewport', action='store_true',
                        help='Disable dual viewport setup')
    
    # Support both: python script.py --arg  AND  blender -P script.py -- --arg
    if '--' in sys.argv:
        argv = sys.argv[sys.argv.index('--') + 1:]
    else:
        argv = sys.argv[1:]
    
    return parser.parse_args(argv)


def create_point_cloud_material(name="GaussianSplatMaterial"):
    """
    Create a material that displays vertex colors from Gaussian splat PLY.
    
    Gaussian splat PLYs typically store colors as vertex colors or attributes.
    """
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Output
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (600, 0)
    
    # Principled BSDF for nice shading
    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.location = (300, 0)
    principled.inputs['Roughness'].default_value = 0.8
    principled.inputs['Specular IOR Level'].default_value = 0.0
    
    # Try to get vertex colors - common attribute names in 3DGS PLY files
    # 1. First try: Color attribute node (Blender 3.2+)
    color_attr = nodes.new('ShaderNodeVertexColor')
    color_attr.location = (0, 100)
    color_attr.layer_name = "Col"  # Default vertex color name
    
    # 2. Also create attribute node for fallback (f_dc_0, etc. from 3DGS)
    attr_r = nodes.new('ShaderNodeAttribute')
    attr_r.location = (-200, 200)
    attr_r.attribute_name = "red"
    attr_r.attribute_type = 'GEOMETRY'
    
    attr_g = nodes.new('ShaderNodeAttribute')
    attr_g.location = (-200, 50)
    attr_g.attribute_name = "green"
    attr_g.attribute_type = 'GEOMETRY'
    
    attr_b = nodes.new('ShaderNodeAttribute')
    attr_b.location = (-200, -100)
    attr_b.attribute_name = "blue"
    attr_b.attribute_type = 'GEOMETRY'
    
    # Combine RGB
    combine = nodes.new('ShaderNodeCombineColor')
    combine.location = (0, -50)
    
    links.new(attr_r.outputs['Fac'], combine.inputs['Red'])
    links.new(attr_g.outputs['Fac'], combine.inputs['Green'])
    links.new(attr_b.outputs['Fac'], combine.inputs['Blue'])
    
    # Mix between vertex color and attribute-based color
    mix = nodes.new('ShaderNodeMix')
    mix.location = (150, 50)
    mix.data_type = 'RGBA'
    mix.inputs['Factor'].default_value = 0.0  # Use vertex colors by default
    
    links.new(color_attr.outputs['Color'], mix.inputs['A'])
    links.new(combine.outputs['Color'], mix.inputs['B'])
    
    # Connect to principled
    links.new(mix.outputs['Result'], principled.inputs['Base Color'])
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    return mat


def create_emission_material(name="GaussianSplatEmission"):
    """
    Create an emission material for brighter point cloud display.
    Uses vertex colors with emission for self-illuminated points.
    """
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    nodes.clear()
    
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    # Emission shader for bright, unshaded colors
    emission = nodes.new('ShaderNodeEmission')
    emission.location = (200, 0)
    emission.inputs['Strength'].default_value = 1.0
    
    # Vertex color
    color_attr = nodes.new('ShaderNodeVertexColor')
    color_attr.location = (0, 0)
    color_attr.layer_name = "Col"
    
    links.new(color_attr.outputs['Color'], emission.inputs['Color'])
    links.new(emission.outputs['Emission'], output.inputs['Surface'])
    
    return mat


def setup_point_display(obj, point_size=0.005):
    """
    Configure object for optimal point cloud display.
    
    Uses geometry nodes to instance small spheres at each vertex
    for better visualization than default point display.
    """
    # Create a geometry nodes modifier for point visualization
    modifier = obj.modifiers.new(name="PointDisplay", type='NODES')
    
    # Create the node tree
    node_group = bpy.data.node_groups.new(name="PointCloudDisplay", type='GeometryNodeTree')
    modifier.node_group = node_group
    
    # Setup interface
    node_group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    node_group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    
    nodes = node_group.nodes
    links = node_group.links
    
    # Group input/output
    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-400, 0)
    
    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (400, 0)
    
    # Mesh to Points (convert mesh vertices to point cloud)
    mesh_to_points = nodes.new('GeometryNodeMeshToPoints')
    mesh_to_points.location = (-200, 0)
    mesh_to_points.inputs['Radius'].default_value = point_size
    
    # Instance on Points with small icosphere
    instance_on_points = nodes.new('GeometryNodeInstanceOnPoints')
    instance_on_points.location = (0, 0)
    instance_on_points.inputs['Scale'].default_value = (1.0, 1.0, 1.0)
    
    # Create icosphere for instancing
    ico = nodes.new('GeometryNodeMeshIcoSphere')
    ico.location = (-200, -150)
    ico.inputs['Radius'].default_value = point_size
    ico.inputs['Subdivisions'].default_value = 1
    
    # Realize instances for proper rendering
    realize = nodes.new('GeometryNodeRealizeInstances')
    realize.location = (200, 0)
    
    # Connect nodes
    links.new(input_node.outputs['Geometry'], mesh_to_points.inputs['Mesh'])
    links.new(mesh_to_points.outputs['Points'], instance_on_points.inputs['Points'])
    links.new(ico.outputs['Mesh'], instance_on_points.inputs['Instance'])
    links.new(instance_on_points.outputs['Instances'], realize.inputs['Geometry'])
    links.new(realize.outputs['Geometry'], output_node.inputs['Geometry'])
    
    return modifier


def configure_viewport_for_gsplat(left_area, right_area):
    """
    Configure dual viewport specifically for Gaussian splat viewing.
    
    Note: Point clouds don't render with materials in Material Preview mode.
    Both viewports use Solid mode with vertex colors for best display.
    
    Left: Solid mode with STUDIO lighting (shows vertex colors with depth)
    Right: Solid mode with FLAT lighting (pure unlit vertex colors)
    """
    # Configure left viewport - Solid with studio lighting
    if left_area:
        for space in left_area.spaces:
            if space.type == 'VIEW_3D':
                space.shading.type = 'SOLID'
                space.shading.light = 'STUDIO'  # Studio lighting for depth
                space.shading.color_type = 'VERTEX'  # Show vertex colors
                space.shading.show_backface_culling = False
                space.overlay.show_overlays = True
                space.overlay.show_floor = True
                space.overlay.show_axis_x = True
                space.overlay.show_axis_y = True
    
    # Configure right viewport - Solid with flat lighting (pure colors)
    if right_area:
        for space in right_area.spaces:
            if space.type == 'VIEW_3D':
                space.shading.type = 'SOLID'
                space.shading.light = 'FLAT'  # No lighting for pure colors
                space.shading.color_type = 'VERTEX'  # Show vertex colors
                space.shading.show_backface_culling = False
                space.overlay.show_overlays = True
                space.overlay.show_floor = True


def add_basic_lighting():
    """Add simple lighting for material preview."""
    # Sun light
    bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
    sun = bpy.context.active_object
    sun.name = "GSplat_Sun"
    sun.data.energy = 3.0
    sun.rotation_euler = (0.8, 0.2, 0.5)
    
    # Ambient light via world
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    
    world.use_nodes = True
    bg_node = world.node_tree.nodes.get("Background")
    if bg_node:
        bg_node.inputs['Color'].default_value = (0.05, 0.05, 0.08, 1.0)
        bg_node.inputs['Strength'].default_value = 1.0


def add_camera_for_gsplat(obj):
    """Add a camera positioned to view the Gaussian splat."""
    # Get object bounds
    bbox = [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]
    center = sum(bbox, mathutils.Vector()) / 8
    
    # Calculate distance based on object size
    dims = obj.dimensions
    max_dim = max(dims)
    distance = max_dim * 2.5
    
    # Create camera
    bpy.ops.object.camera_add(location=(center.x + distance, center.y - distance, center.z + distance * 0.5))
    camera = bpy.context.active_object
    camera.name = "GSplat_Camera"
    
    # Point at center
    direction = center - camera.location
    camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    
    # Set as active camera
    bpy.context.scene.camera = camera
    
    return camera


def register_gsplat_viewport_handler():
    """
    Register a load_post handler that automatically sets up the dual viewport
    when the .blend file is opened in Blender GUI.
    
    This is the preferred approach - viewport auto-configures on file load.
    """
    handler_name = "restore_gsplat_viewport"
    
    # Remove existing handler if present
    for handler in list(bpy.app.handlers.load_post):
        if hasattr(handler, '__name__') and handler.__name__ == handler_name:
            bpy.app.handlers.load_post.remove(handler)
    
    def restore_gsplat_viewport(dummy):
        """Auto-restore viewport when file is loaded."""
        if bpy.app.background:
            return
        
        # Ensure GSplatColor attribute is active on mesh objects
        for obj in bpy.data.objects:
            if obj.type == 'MESH' and obj.data and obj.data.color_attributes:
                for ca in obj.data.color_attributes:
                    if ca.name == 'GSplatColor':
                        obj.data.color_attributes.active_color = ca
                        break
        
        # Find or split viewport
        screen = bpy.context.screen
        if not screen:
            return
            
        view3d_areas = sorted([a for a in screen.areas if a.type == 'VIEW_3D'], key=lambda a: a.x)
        
        if not view3d_areas:
            return
        
        if len(view3d_areas) < 2:
            # Split viewport
            area = view3d_areas[0]
            with bpy.context.temp_override(area=area, region=area.regions[0]):
                try:
                    bpy.ops.screen.area_split(direction='VERTICAL', factor=0.5)
                except:
                    return
            view3d_areas = sorted([a for a in screen.areas if a.type == 'VIEW_3D'], key=lambda a: a.x)
        
        if len(view3d_areas) < 2:
            return
        
        left_area = view3d_areas[0]
        right_area = view3d_areas[-1]
        
        # Configure left viewport - Solid with studio lighting
        for space in left_area.spaces:
            if space.type == 'VIEW_3D':
                space.shading.type = 'SOLID'
                space.shading.light = 'STUDIO'
                space.shading.color_type = 'VERTEX'
                space.shading.show_backface_culling = False
                space.overlay.show_overlays = True
                space.overlay.show_floor = True
        
        # Configure right viewport - Solid with flat lighting
        for space in right_area.spaces:
            if space.type == 'VIEW_3D':
                space.shading.type = 'SOLID'
                space.shading.light = 'FLAT'
                space.shading.color_type = 'VERTEX'
                space.shading.show_backface_culling = False
                space.overlay.show_overlays = True
                space.overlay.show_floor = True
        
        print("✅ Gaussian Splat dual viewport auto-configured!")
    
    restore_gsplat_viewport.__name__ = handler_name
    bpy.app.handlers.load_post.append(restore_gsplat_viewport)
    
    print(f"📝 Registered load_post handler: {handler_name}")
    print(f"   Viewport will auto-configure when .blend file is opened")


def run():
    args = parse_args()
    
    print("=" * 60)
    print("  3D Gaussian Splatting Viewer")
    print("=" * 60)
    
    # Check input file exists
    if not os.path.exists(args.input):
        print(f"❌ File not found: {args.input}")
        return
    
    # Clear scene using setup module
    clear_scene()
    
    # Set dark background for better point cloud visibility
    add_basic_lighting()
    
    print(f"\n📦 Loading 3DGS: {os.path.basename(args.input)}")
    
    # Load the Gaussian splat using setup.load_gsplat (calls gsplat.py internally)
    # This auto-detects 3DGS (single file) vs 4DGS (folder)
    obj = load_gsplat(
        args.input,
        collection_name="3DGS"
    )
    
    if not obj:
        print("❌ Failed to load Gaussian splat")
        return
    
    # Get point count
    point_count = len(obj.data.vertices) if obj.data else 0
    print(f"   Points: {point_count:,}")
    
    # Check for vertex colors and Gaussian Splat SH attributes
    has_vertex_colors = False
    color_attr_names = []
    if obj.data and obj.data.color_attributes:
        has_vertex_colors = True
        color_attr_names = [vc.name for vc in obj.data.color_attributes]
        print(f"   Vertex colors: {color_attr_names}")
        for vc in obj.data.color_attributes:
            print(f"      - {vc.name}: type={vc.data_type}, domain={vc.domain}")
    else:
        print(f"   ⚠️ No vertex colors found (yet)")
    
    # Check for Gaussian Splat specific attributes (f_dc_*, scale_*, rot_*)
    if obj.data and hasattr(obj.data, 'attributes'):
        all_attrs = [a.name for a in obj.data.attributes]
        
        # Check for spherical harmonics (f_dc_*)
        sh_attrs = [a for a in all_attrs if a.startswith('f_dc_')]
        if sh_attrs:
            print(f"   Spherical harmonics (SH): {sh_attrs}")
        
        # Check for other 3DGS attributes  
        scale_attrs = [a for a in all_attrs if a.startswith('scale_')]
        rot_attrs = [a for a in all_attrs if a.startswith('rot_')]
        if scale_attrs:
            print(f"   Scale attributes: {scale_attrs}")
        if rot_attrs:
            print(f"   Rotation attributes: {rot_attrs}")
        
        # Opacity
        if 'opacity' in all_attrs:
            print(f"   Opacity: found")
    
    # Setup Gaussian splat display with geometry nodes and material
    # Geometry nodes are REQUIRED for proper vertex color display on point clouds
    print(f"\n🎨 Setting up Gaussian splat display...")
    setup_gsplat_display(obj, point_size=args.point_size, use_emission=True, use_geometry_nodes=True)
    print(f"   ✅ Geometry nodes and material applied")
    
    # Add camera
    add_camera_for_gsplat(obj)
    
    # Setup dual viewport using load_post handler
    # The handler auto-configures viewport when .blend is opened in Blender GUI
    if not args.no_dual_viewport:
        print("\n🖼️ Setting up dual viewport...")
        
        # Register load_post handler for auto-configuration on file open
        register_gsplat_viewport_handler()
        
        # Try immediate setup if running in Blender GUI (not background)
        if not bpy.app.background:
            viewport_result = setup_dual_viewport({
                'split_factor': 0.5,
                'left_shading': 'SOLID',
                'right_shading': 'SOLID',
                'sync_views': True
            })
            
            if viewport_result:
                configure_viewport_for_gsplat(
                    viewport_result.get('left_area'),
                    viewport_result.get('right_area')
                )
        
        print("   ✅ Viewport will auto-configure on file open")
        print("   Left viewport: Studio lighting (vertex colors)")
        print("   Right viewport: Flat lighting (vertex colors)")
    
    # Frame the object in view
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    
    # Try to frame in 3D views
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for region in area.regions:
                if region.type == 'WINDOW':
                    override = {'area': area, 'region': region}
                    try:
                        with bpy.context.temp_override(**override):
                            bpy.ops.view3d.view_selected()
                    except:
                        pass
    
    # Save using setup module
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'output'))
    output_path = os.path.join(output_dir, args.output)
    save_blend(output_path)
    
    print("\n" + "=" * 60)
    print("✅ Demo Complete!")
    print("=" * 60)
    print(f"\n📊 Summary:")
    print(f"   Input: {args.input}")
    print(f"   Points: {point_count:,}")
    print(f"   Output: {output_path}")
    print(f"\n💡 To view:")
    print(f"   1. Open the .blend file in Blender")
    print(f"   2. Dual viewport auto-configures on file load!")
    print(f"\n   Left viewport: Studio lighting (vertex colors with depth)")
    print(f"   Right viewport: Flat lighting (pure vertex colors)")
    print(f"\n   - Use mouse scroll to zoom")
    print(f"   - Middle-click drag to rotate view")


if __name__ == "__main__":
    run()

