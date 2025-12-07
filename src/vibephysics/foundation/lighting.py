import bpy
import math

def create_caustics_light(scale, energy=20.0):
    """
    Creates a subtle Sun Light that projects a soft caustic pattern.
    Designed to complement natural sky lighting, not overpower it.
    """
    # 1. Create Texture Projection Object (Empty)
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    texture_control = bpy.context.active_object
    texture_control.name = "Caustic_Texture_Control"
    
    # 2. Create Sun Light - angled like natural sunlight
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 50))
    light = bpy.context.active_object
    light.name = "CausticLight"
    
    # Rotate sun to come from an angle (not straight down) for natural look
    light.rotation_euler = (math.radians(45), 0, math.radians(30))
    
    # Sun Settings - much softer and natural
    # Clamp energy to reasonable values for natural look
    natural_energy = min(energy * 0.005, 5.0)  # Very subtle, max 5.0
    light.data.energy = natural_energy
    # Larger angle = softer shadows (real sun is ~0.5 degrees, we use larger for softness)
    light.data.angle = math.radians(3.0)
    
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
    node_coord.object = texture_control
    
    node_mapping = nodes.new(type='ShaderNodeMapping')
    
    # Voronoi (Caustic Pattern) - softer settings
    node_voronoi = nodes.new(type='ShaderNodeTexVoronoi')
    node_voronoi.voronoi_dimensions = '4D'
    node_voronoi.feature = 'SMOOTH_F1'
    node_voronoi.inputs['Scale'].default_value = scale
    node_voronoi.inputs['Smoothness'].default_value = 1.0  # Maximum smoothness
    
    # ColorRamp - much softer gradient for subtle caustics
    node_ramp = nodes.new(type='ShaderNodeValToRGB')
    node_ramp.color_ramp.interpolation = 'EASE'
    node_ramp.color_ramp.elements[0].position = 0.2
    node_ramp.color_ramp.elements[0].color = (0.7, 0.7, 0.7, 1.0)  # Not pure black
    node_ramp.color_ramp.elements[1].position = 0.6
    node_ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
    
    # Linking
    links.new(node_coord.outputs['Object'], node_mapping.inputs['Vector'])
    links.new(node_mapping.outputs['Vector'], node_voronoi.inputs['Vector'])
    links.new(node_voronoi.outputs['Distance'], node_ramp.inputs['Fac'])
    links.new(node_ramp.outputs['Color'], node_emission.inputs['Color'])
    links.new(node_emission.outputs['Emission'], node_out.inputs['Surface'])
    
    # Animate W (Time) - slower animation for natural feel
    fcurve = node_voronoi.inputs['W'].driver_add("default_value")
    driver = fcurve.driver
    driver.expression = "frame / 48.0"  # Slower caustic movement
    
    # Emission strength kept at 1.0, controlled via data.energy
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
    """Visual Scene Setup (Non-Physics) - Natural lighting from sky only"""
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
        
        # Point camera at center or water object
        constraint = cam.constraints.new(type='TRACK_TO')
        target_obj = bpy.data.objects.get(water_obj_name)
        
        if target_obj:
            # Track the water object if it exists
            constraint.target = target_obj
        else:
            # Fallback: Create an empty at (0,0,0) to track the center
            if not bpy.data.objects.get("Camera_Target_Center"):
                bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
                center_empty = bpy.context.active_object
                center_empty.name = "Camera_Target_Center"
                center_empty.empty_display_size = 0.5
                center_empty.hide_render = True
            constraint.target = bpy.data.objects.get("Camera_Target_Center")
        
        constraint.track_axis = 'TRACK_NEGATIVE_Z'
        constraint.up_axis = 'UP_Y'
        
    # Set the active camera (Default to first one)
    if cameras:
        bpy.context.scene.camera = cameras[0]
    
    # NO artificial lights - only environment lighting
    # Caustics disabled by default for natural look
    if enable_caustics:
        # Subtle caustics that complement natural sky lighting
        create_caustics_light(scale=caustic_scale, energy=caustic_strength)
        
    if enable_volumetric:
        create_underwater_volume(z_surface, z_bottom, volumetric_density)
    
    # World/Sky - Natural HDRI-style lighting using Sky Texture
    world = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    nodes.clear()
    
    # Create Sky Texture for natural outdoor lighting
    node_out = nodes.new(type='ShaderNodeOutputWorld')
    node_bg = nodes.new(type='ShaderNodeBackground')
    node_sky = nodes.new(type='ShaderNodeTexSky')
    
    # Sky Texture settings for natural daylight
    # Handle different Blender versions (NISHITA for 2.9-4.x, HOSEK_WILKIE for 5.0+)
    try:
        node_sky.sky_type = 'NISHITA'
        node_sky.sun_elevation = math.radians(45)
        node_sky.sun_rotation = math.radians(0)
        node_sky.altitude = 0
        node_sky.air_density = 1.0
        node_sky.dust_density = 1.0
        node_sky.ozone_density = 1.0
    except TypeError:
        # Blender 5.0+ uses different sky types
        node_sky.sky_type = 'HOSEK_WILKIE'
        node_sky.turbidity = 2.0  # Lower = clearer sky
        # Sun direction as vector (x, y, z) - sun at 45 degrees elevation
        node_sky.sun_direction = (0.0, 0.707, 0.707)
    
    # Background strength - controls overall scene brightness
    node_bg.inputs['Strength'].default_value = 1.0
    
    # Connect nodes
    links.new(node_sky.outputs['Color'], node_bg.inputs['Color'])
    links.new(node_bg.outputs['Background'], node_out.inputs['Surface'])
    
    # Render Settings
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 128
    bpy.context.scene.render.resolution_x = resolution_x
    bpy.context.scene.render.resolution_y = resolution_y
    bpy.context.scene.frame_start = start_frame
    bpy.context.scene.frame_end = end_frame
    
    # EEVEE / Viewport Settings
    try:
        bpy.context.scene.eevee.use_ssr = True
        bpy.context.scene.eevee.use_ssr_refraction = True
    except AttributeError:
        try:
            if hasattr(bpy.context.scene.eevee, "use_raytracing"):
                 bpy.context.scene.eevee.use_raytracing = True
        except:
            pass

def setup_camera_tracking(target_object, track_axis='TRACK_NEGATIVE_Z', up_axis='UP_Y'):
    """
    Make the scene camera track a target object.
    Hides low-level constraint setup.
    
    Args:
        target_object: Object for camera to track
        track_axis: Which camera axis points at target
        up_axis: Which camera axis points up
    """
    cam = bpy.context.scene.camera
    if cam:
        constraint = cam.constraints.new(type='TRACK_TO')
        constraint.target = target_object
        constraint.track_axis = track_axis
        constraint.up_axis = up_axis
    return cam
