import bpy
import math

def create_caustics_light(scale, energy=20.0):
    """
    Creates a Sun Light that projects a caustic pattern.
    Visuals: God Rays + Seabed patterns (Global coverage)
    """
    # 1. Create Texture Projection Object (Empty)
    # This allows the texture to stay 'fixed' in world space even if the sun moves, 
    # and provides a stable coordinate system for the Voronoi.
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    texture_control = bpy.context.active_object
    texture_control.name = "Caustic_Texture_Control"
    
    # 2. Create Sun Light
    # Placed high, pointing down. 
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 50))
    light = bpy.context.active_object
    light.name = "CausticLight"
    
    # Sun Settings
    light.data.energy = energy  # Sun strength is different from Spot. Start lower, tune up.
    # For clear caustics, we want a small angle (hard shadows)
    light.data.angle = math.radians(0.5) 
    
    # Node Setup for Texture Projection (Gobo)
    light.data.use_nodes = True
    nodes = light.data.node_tree.nodes
    links = light.data.node_tree.links
    nodes.clear()
    
    # Nodes
    node_out = nodes.new(type='ShaderNodeOutputLight')
    node_emission = nodes.new(type='ShaderNodeEmission')
    
    # Coordinate System: Object (The Empty)
    node_coord = nodes.new(type='ShaderNodeTexCoord')
    node_coord.object = texture_control # Link to the Empty
    
    node_mapping = nodes.new(type='ShaderNodeMapping')
    # Point Z down for projection? Object coords are usually XYZ. 
    # We'll map XY of the empty to the noise.
    
    # Voronoi (Caustic Pattern)
    node_voronoi = nodes.new(type='ShaderNodeTexVoronoi')
    node_voronoi.voronoi_dimensions = '4D'
    node_voronoi.feature = 'SMOOTH_F1'
    node_voronoi.inputs['Scale'].default_value = scale
    
    # ColorRamp (Sharpen)
    node_ramp = nodes.new(type='ShaderNodeValToRGB')
    node_ramp.color_ramp.elements[0].position = 0.05
    node_ramp.color_ramp.elements[1].position = 0.25
    
    # Linking
    links.new(node_coord.outputs['Object'], node_mapping.inputs['Vector'])
    links.new(node_mapping.outputs['Vector'], node_voronoi.inputs['Vector'])
    links.new(node_voronoi.outputs['Distance'], node_ramp.inputs['Fac'])
    links.new(node_ramp.outputs['Color'], node_emission.inputs['Color'])
    links.new(node_emission.outputs['Emission'], node_out.inputs['Surface'])
    
    # Animate W (Time)
    fcurve = node_voronoi.inputs['W'].driver_add("default_value")
    driver = fcurve.driver
    driver.expression = "frame / 24.0"
    
    # Set Strength
    # Sun strength in nodes interacts with data.energy. 
    # We keep emission strength 1.0 and control via data.energy
    node_emission.inputs['Strength'].default_value = 1.0


def create_underwater_volume(z_surface, z_bottom, density):
    """
    Creates a volume object to scatter light (God Rays).
    """
    # Cube covering the water depth
    # Center Z = (Surface + Bottom) / 2
    z_center = (z_surface + z_bottom) / 2.0
    z_height = abs(z_surface - z_bottom)
    
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, z_center))
    vol = bpy.context.active_object
    vol.name = "UnderwaterVolume"
    
    # Scale: X, Y big, Z matches depth
    # Cube primitive is 2m by default (radius 1). Scale 1 = 2m.
    # We want Z dimension to be z_height. So Scale Z = z_height / 2.
    vol.scale = (50.0, 50.0, z_height / 2.0)
    
    # Material
    mat = bpy.data.materials.new(name="VolumeMat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    node_out = nodes.new(type='ShaderNodeOutputMaterial')
    node_add = nodes.new(type='ShaderNodeAddShader')
    node_scatter = nodes.new(type='ShaderNodeVolumeScatter')
    node_absorb = nodes.new(type='ShaderNodeVolumeAbsorption')
    
    # Scatter Settings
    node_scatter.inputs['Density'].default_value = density
    node_scatter.inputs['Anisotropy'].default_value = 0.7 # Forward scattering (glare)
    node_scatter.inputs['Color'].default_value = (0.9, 0.95, 1.0, 1.0) # White/Blueish scatter
    
    # Absorption Settings
    node_absorb.inputs['Density'].default_value = density * 0.5
    node_absorb.inputs['Color'].default_value = (0.1, 0.3, 0.9, 1.0) # Deep Blue
    
    links.new(node_scatter.outputs['Volume'], node_add.inputs[0])
    links.new(node_absorb.outputs['Volume'], node_add.inputs[1])
    links.new(node_add.outputs['Shader'], node_out.inputs['Volume'])
    
    vol.data.materials.append(mat)
    
    # Disable shadow casting for the volume box itself (optional, but good for performance)
    vol.visible_shadow = False


def setup_lighting_and_camera(camera_radius, camera_height, resolution_x, resolution_y, start_frame, end_frame, 
                              enable_caustics, enable_volumetric, z_surface, z_bottom, volumetric_density, caustic_scale, 
                              caustic_strength=8000.0, water_obj_name="Water_Visual"):
    """Visual Scene Setup (Non-Physics)"""
    # Cameras - Create 6 cameras evenly distributed around the circle
    cameras = []
    num_cameras = 6
    
    for i in range(num_cameras):
        angle_deg = i * (360.0 / num_cameras)
        angle_rad = math.radians(angle_deg)
        
        # Calculate position on circle
        cam_x = camera_radius * math.cos(angle_rad)
        cam_y = camera_radius * math.sin(angle_rad)
        cam_z = camera_height
        
        bpy.ops.object.camera_add(location=(cam_x, cam_y, cam_z))
        cam = bpy.context.active_object
        cam.name = f"Camera_{i}_Angle_{int(angle_deg)}"
        cameras.append(cam)
        
        # Point tracking at center (0,0,0) / Water_Visual
        constraint = cam.constraints.new(type='TRACK_TO')
        target_obj = bpy.data.objects.get(water_obj_name)
        if target_obj:
            constraint.target = target_obj
        constraint.track_axis = 'TRACK_NEGATIVE_Z'
        constraint.up_axis = 'UP_Y'
        
    # Set the active camera (Default to first one)
    if cameras:
        bpy.context.scene.camera = cameras[0]
    
    # Sun -> Specular Point Light
    # Replace broad Sun with a bright Point Light to create sharp specular highlights
    bpy.ops.object.light_add(type='POINT', location=(5, 5, 10))
    light = bpy.context.active_object
    light.name = "SpecularLight"
    light.data.energy = 5000.0 # High energy for point light to reach far
    light.data.shadow_soft_size = 0.1 # Small size = sharp shadows/speculars
    
    # Add a Rim Light for extra definition (optional)
    bpy.ops.object.light_add(type='AREA', location=(-8, -8, 5))
    rim = bpy.context.active_object
    rim.name = "RimLight"
    rim.data.energy = 500.0
    rim.rotation_euler = (math.radians(60), 0, math.radians(-45))
    
    if enable_caustics:
        create_caustics_light(scale=caustic_scale, energy=caustic_strength)
        
    if enable_volumetric:
        create_underwater_volume(z_surface, z_bottom, volumetric_density)
    
    # World/Sky
    world = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.6, 0.8, 1.0, 1)
    
    # Render Settings
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 128
    bpy.context.scene.render.resolution_x = resolution_x
    bpy.context.scene.render.resolution_y = resolution_y
    bpy.context.scene.frame_start = start_frame
    bpy.context.scene.frame_end = end_frame
    
    # EEVEE / Viewport Settings (so it looks good in "Material Preview" mode)
    # Even if we render in Cycles, these help the viewport look correct
    # Handle API change for Blender 4.2+ (use_ssr removed/changed)
    try:
        bpy.context.scene.eevee.use_ssr = True        # Screen Space Reflections
        bpy.context.scene.eevee.use_ssr_refraction = True # Refraction
    except AttributeError:
        # Blender 4.2+ (Eevee Next) enables Raytracing by default or via different property
        # We can try enabling Raytracing if available, or just pass
        try:
            # For Blender 4.2+, 'use_raytracing' might be the key if it exists, 
            # or it might just be 'on' by default for refraction if material requests it.
            # Checking for 'use_raytracing' which replaced SSR in some contexts
            if hasattr(bpy.context.scene.eevee, "use_raytracing"):
                 bpy.context.scene.eevee.use_raytracing = True
            
            # Also ensure Refraction is enabled in Raytracing if applicable
            # In some builds, it's purely material-based.
        except:
            pass
