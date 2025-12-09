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
    setup_gsplat_display,
    setup_dual_viewport,
    ensure_collection,
)
from vibephysics.setup.gsplat import (
    print_gsplat_info,
    get_gsplat_info,
    setup_gsplat_display_advanced,
    MeshType,
    ShaderMode,
    PointScale,
    OutputChannel,
)
from vibephysics.camera import CameraManager


def setup_simple_dual_viewport():
    """Setup dual viewport: Left=Material+Camera, Right=Solid (no local view)."""
    from vibephysics.setup.viewport import (
        split_viewport_horizontal, 
        get_space_view3d,
        configure_viewport_shading,
        lock_viewport_to_camera
    )
    
    left_area, right_area = split_viewport_horizontal(0.5)
    if not left_area or not right_area:
        print("   ⚠️ Could not split viewport")
        return False
    
    left_space = get_space_view3d(left_area)
    right_space = get_space_view3d(right_area)
    
    # Left: Material Preview + Camera View
    configure_viewport_shading(left_space, shading_type='MATERIAL')
    lock_viewport_to_camera(left_space)
    
    # Right: Solid with vertex colors
    configure_viewport_shading(right_space, shading_type='SOLID', light='FLAT', color_type='VERTEX')
    
    return True


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
                        help='Point size for visualization (used in Fix mode)')
    parser.add_argument('--no-dual-viewport', action='store_true',
                        help='Disable dual viewport setup')
    
    # Advanced display options based on UGRS/Nunchucks
    parser.add_argument('--mesh-type', type=str, default='Circle',
                        choices=['Cube', 'IcoSphere', 'DualIcoSphere', 'Circle'],
                        help='Mesh type for point instancing. '
                             'Circle is best for Gaussian splat appearance (disk-like), '
                             'DualIcoSphere creates hexagonal pattern')
    parser.add_argument('--shader-mode', type=str, default='Gaussian',
                        choices=['Gaussian', 'Ring', 'Wireframe', 'Freestyle'],
                        help='Shader rendering mode. '
                             'Gaussian creates transparent disk-like splats with falloff')
    parser.add_argument('--point-scale', type=str, default='Anisotropic',
                        choices=['Fix', 'Auto', 'Max', 'Anisotropic'],
                        help='Point scale mode. '
                             'Anisotropic uses (scale_0, scale_1, scale_2) as X,Y,Z for ellipsoid shapes (thin needles). '
                             'Max uses max(scale_0, scale_1, scale_2) for uniform spheres')
    parser.add_argument('--output-channel', type=str, default='Final color',
                        choices=['Final color', 'Normal', 'Depth', 'Alpha', 'Albedo'],
                        help='Output channel for visualization')
    parser.add_argument('--geo-size', type=float, default=3.0,
                        help='Geometry size multiplier (default 3.0). Controls how large the mesh is '
                             'relative to the visible Gaussian. Larger = more transparent area around '
                             'the splat center. This is key for the Gaussian appearance!')
    parser.add_argument('--use-advanced', action='store_true', default=True,
                        help='Use advanced display mode with UGRS-style geometry nodes (default: True)')
    parser.add_argument('--use-simple', action='store_true',
                        help='Use simple display mode (solid colors, no transparency)')
    parser.add_argument('--no-rotate', action='store_true',
                        help='Do NOT rotate object (by default, rotates -90° X to convert Z-up to Y-up)')
    
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


def create_point_cloud_duplicate(obj, collection_name="PointCloudViz"):
    """
    Create a point cloud duplicate of the Gaussian splat object.
    
    This creates a separate object without geometry nodes that shows
    just the raw vertices with vertex colors - used for the right viewport.
    
    Args:
        obj: Source Gaussian splat object
        collection_name: Collection name for the point cloud
        
    Returns:
        The point cloud object
    """
    # Create collection for point cloud
    pc_collection = ensure_collection(collection_name)
    
    # Duplicate the mesh data (not linked)
    new_mesh = obj.data.copy()
    pc_obj = bpy.data.objects.new(f"{obj.name}_PointCloud", new_mesh)
    
    # Link to collection
    pc_collection.objects.link(pc_obj)
    
    # Copy transform
    pc_obj.location = obj.location.copy()
    pc_obj.rotation_euler = obj.rotation_euler.copy()
    pc_obj.scale = obj.scale.copy()
    
    # Create a simple vertex color material for the point cloud
    mat = bpy.data.materials.new(name="PointCloudMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    # Output
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # Emission shader for bright vertex colors
    emission = nodes.new('ShaderNodeEmission')
    emission.location = (100, 0)
    emission.inputs['Strength'].default_value = 1.0
    
    # Vertex color
    color_attr = nodes.new('ShaderNodeVertexColor')
    color_attr.location = (-100, 0)
    # Try to use the GSplatColor attribute if it exists
    if new_mesh.color_attributes:
        for ca in new_mesh.color_attributes:
            if ca.name == 'GSplatColor':
                color_attr.layer_name = 'GSplatColor'
                break
        else:
            color_attr.layer_name = new_mesh.color_attributes[0].name
    
    links.new(color_attr.outputs['Color'], emission.inputs['Color'])
    links.new(emission.outputs['Emission'], output.inputs['Surface'])
    
    # Assign material
    pc_obj.data.materials.append(mat)
    
    print(f"   ✅ Created point cloud duplicate: {pc_obj.name}")
    return pc_obj


def setup_camera_system(obj):
    """
    Setup camera system similar to demo_all_annotations.py.
    
    Creates center-pointing cameras around the origin.
    
    Args:
        obj: The Gaussian splat object (used to determine camera radius)
        
    Returns:
        CameraManager instance
    """
    print("\n📷 Setting up Camera System...")
    
    radius = 5
    
    # Create camera manager
    cam_manager = CameraManager()
    
    # ==========================================================================
    # Center-Pointing Cameras (4 cameras around origin, height=0)
    # ==========================================================================
    print("  📷 Creating center-pointing cameras (4 cameras)")
    center_rig = cam_manager.add_center_pointing(
        name='center', 
        num_cameras=4, 
        radius=radius, 
        height=0.0  # Cameras at same height as origin
    )
    center_rig.create(target_location=(0, 0, 0))  # Point at origin
    
    # ==========================================================================
    # Set default active camera (camera at 270°)
    # ==========================================================================
    cam_manager.activate_rig('center', camera_index=3)  # Camera_3_Angle_270
    
    print(f"\n  Total cameras created: {len(cam_manager.get_all_cameras())}")
    print("    - 4 center-pointing cameras (fixed positions, track origin)")
    print(f"    - Radius: {radius:.1f}, Height: 0.0")
    print(f"    - Target: (0, 0, 0)")
    
    return cam_manager


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
    
    # Rotate object by default (Z-up to Y-up for Blender)
    if not args.no_rotate:
        import math
        obj.rotation_euler[0] = -math.pi / 2  # Rotate -90° around X axis
        print(f"   Rotated: Z-up → Y-up (X rotation: -90°)")
    
    # Get point count
    point_count = len(obj.data.vertices) if obj.data else 0
    print(f"   Points: {point_count:,}")
    
    # Print detailed Gaussian Splat info using the new utility
    gsplat_info = print_gsplat_info(obj)
    
    # Check for vertex colors (before SH conversion)
    if obj.data and obj.data.color_attributes:
        print(f"\n   Existing vertex colors:")
        for vc in obj.data.color_attributes:
            print(f"      - {vc.name}: type={vc.data_type}, domain={vc.domain}")
    
    # Setup Gaussian splat display with geometry nodes and material
    # Geometry nodes are REQUIRED for proper vertex color display on point clouds
    print(f"\n🎨 Setting up Gaussian splat display...")
    
    if args.use_simple:
        # Use simple display mode (faster for large point clouds, solid colors)
        print(f"   Using simple display mode (solid colors)")
        setup_gsplat_display(obj, point_size=args.point_size, use_emission=True, use_geometry_nodes=True)
    else:
        # Use advanced UGRS-style display with configurable options
        print(f"   Using advanced display mode (Gaussian splat appearance):")
        print(f"   - Mesh type: {args.mesh_type}")
        print(f"   - Shader mode: {args.shader_mode}")
        print(f"   - Point scale: {args.point_scale}")
        print(f"   - Geo size: {args.geo_size} (mesh is {args.geo_size}x larger than visible Gaussian)")
        print(f"   - Output channel: {args.output_channel}")
        
        setup_gsplat_display_advanced(
            obj,
            mesh_type=args.mesh_type,
            shader_mode=args.shader_mode,
            point_scale=args.point_scale,
            output_channel=args.output_channel,
            fixed_scale=args.point_size,
            geo_size=args.geo_size,
            use_emission=True
        )
    
    print(f"   ✅ Geometry nodes and material applied")
    
    # Setup camera system (similar to demo_all_annotations.py)
    cam_manager = setup_camera_system(obj)
    
    # Setup dual viewport (both showing Gaussian splat)
    # Left: Material Preview, Right: Solid view
    if not args.no_dual_viewport:
        print("\n🖼️ Setting up dual viewport...")
        if setup_simple_dual_viewport():
            print("   ✅ Dual viewport created")
            print("   Left viewport: Material Preview (Gaussian splat)")
            print("   Right viewport: Solid view (vertex colors)")
    
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
    print(f"   Cameras: {len(cam_manager.get_all_cameras())}")
    print(f"   Output: {output_path}")
    
    if not args.use_simple:
        print(f"\n🎛️ Advanced Display Options (UGRS-style):")
        print(f"   - Mesh type: {args.mesh_type}")
        print(f"     └─ Circle: Flat disk (best for Gaussian shader)")
        print(f"     └─ IcoSphere: Round 3D appearance")
        print(f"     └─ DualIcoSphere: Hexagonal pattern")
        print(f"     └─ Cube: Simple cube mesh")
        print(f"   - Shader mode: {args.shader_mode}")
        print(f"     └─ Gaussian: Transparent disk with falloff (default)")
        print(f"     └─ Ring: Hollow ring shape")
        print(f"     └─ Wireframe: Wireframe rendering")
        print(f"   - Point scale: {args.point_scale}")
        print(f"     └─ Anisotropic: (scale_0, scale_1, scale_2) as X,Y,Z - ellipsoid (thin needles!)")
        print(f"     └─ Max: max(scale_0, scale_1, scale_2) - uniform spheres")
        print(f"     └─ Auto: Automatic scaling")
        print(f"     └─ Fix: Fixed size ({args.point_size})")
        print(f"   - Geo size: {args.geo_size}")
        print(f"     └─ Mesh is {args.geo_size}x larger than visible Gaussian")
        print(f"     └─ Higher = smaller visible splat relative to mesh")
        print(f"   - Output: {args.output_channel}")
    
    print(f"\n💡 To view:")
    print(f"   Open the .blend file in Blender: {output_path}")
    print(f"   Left viewport: Material Preview (Gaussian splat)")
    print(f"   Right viewport: Solid view (vertex colors)")
    print(f"\n📷 Camera Controls:")
    print(f"   - Numpad 0: View through active camera")
    print(f"   - Switch cameras: Properties → Scene → Camera")
    print(f"\n   Note: Colors are converted from SH coefficients (f_dc_*) to RGB")
    print(f"   Formula: RGB = SH_C0 × f_dc + 0.5, where SH_C0 = 0.282...")
    print(f"\n   - Mouse scroll: zoom")
    print(f"   - Middle-click drag: rotate view")
    print(f"   - Shift + middle-click: pan view")
    
    if args.use_simple:
        print(f"\n💡 Tip: Default mode now uses Gaussian splat appearance with:")
        print(f"   --mesh-type IcoSphere --shader-mode Gaussian --point-scale Anisotropic")
        print(f"   Remove --use-simple to enable ellipsoid splats (thin as needles!)")


if __name__ == "__main__":
    run()

