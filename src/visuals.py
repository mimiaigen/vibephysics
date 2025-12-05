import bpy

def create_visual_water(scale, wave_scale, time=None, start_frame=1, end_frame=250):
    """
    Creates the water surface mesh.
    SIMULATION TYPE: Ocean Modifier (Vertex Displacement)
    
    What it does:
    - Generates a realistic wave spectrum (Phillips/JONSWAP).
    - Purely visual displacement (does not apply force to rigid bodies directly).
    - Animated via 'Time' parameter.
    """
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    water = bpy.context.active_object
    water.name = "Water_Visual"
    water.scale = (1, 1, 1)
    
    ocean_mod = water.modifiers.new(name="OceanSim", type='OCEAN')
    ocean_mod.geometry_mode = 'GENERATE'
    ocean_mod.resolution = 12      # Optimized (was 16)
    ocean_mod.spatial_size = 50
    # Link parameters to wave_scale to create a "Storm" vs "Calm" slider
    ocean_mod.wave_scale = wave_scale
    ocean_mod.choppiness = min(max(wave_scale, 0), 4.0)
    ocean_mod.wind_velocity = max(wave_scale * 10.0, 0.0)
    
    # Animation
    if time is not None:
        # If fixed time is set, lock the wave to that specific timeframe constantly
        ocean_mod.time = time
    else:
        # Standard animation
        ocean_mod.time = 0.0
        water.keyframe_insert(data_path='modifiers["OceanSim"].time', frame=start_frame)
        ocean_mod.time = 5.0
        water.keyframe_insert(data_path='modifiers["OceanSim"].time', frame=end_frame)
    
    bpy.ops.object.shade_smooth()
    
    # Add Subdivision for Dynamic Paint resolution
    subsurf = water.modifiers.new(name="Subsurf", type='SUBSURF')
    subsurf.levels = 1          # Optimized (was 4) - HUGE performance saver
    subsurf.render_levels = 2   # Higher for render only
    
    return water

def setup_dynamic_paint_interaction(water_obj, sphere_objs, ripple_strength):
    """
    Sets up the Ripple Interaction.
    SIMULATION TYPE: Dynamic Paint (Vertex Weight / Displacement)
    
    What it does:
    - 'Canvas' (Water): Simulates a 2D Wave Equation surface.
    - 'Brush' (Spheres): When near the surface, they add energy/waves.
    - Generates the "Wake" and "Ripples" moving away from the spheres.
    
    Missing Physics:
    - Two-way coupling: The ripples do NOT push the sphere back up. 
      (The sphere floats due to the Buoyancy Field, not the waves it creates).
    - Splash/Particles: No droplets are generated (requires Particle System).
    """
    # 1. Setup Canvas (Water)
    bpy.context.view_layer.objects.active = water_obj
    bpy.ops.object.modifier_add(type='DYNAMIC_PAINT')
    canvas_mod = water_obj.modifiers[-1]
    canvas_mod.ui_type = 'CANVAS'
    bpy.ops.dpaint.type_toggle(type='CANVAS')
    bpy.ops.dpaint.output_toggle(output='A')
    
    surface = canvas_mod.canvas_settings.canvas_surfaces[-1]
    
    # CRITICAL: Disable disk cache IMMEDIATELY before any other configuration
    # This prevents Blender from creating blendcache folders
    if surface.point_cache:
        surface.point_cache.use_disk_cache = False
        surface.point_cache.use_library_path = False  # Don't use external cache path
    
    surface.surface_type = 'WAVE'
    surface.wave_timescale = 0.8
    surface.wave_speed = 1.5
    surface.wave_damping = 0.02
    surface.wave_spring = 0.1  # Low tension = Loose water
    surface.wave_smoothness = 1.0
    surface.use_wave_open_border = True

    # 2. Setup Brushes (Spheres)
    for sphere in sphere_objs:
        bpy.context.view_layer.objects.active = sphere
        bpy.ops.object.modifier_add(type='DYNAMIC_PAINT')
        brush_mod = sphere.modifiers[-1]
        brush_mod.ui_type = 'BRUSH'
        bpy.ops.dpaint.type_toggle(type='BRUSH')
        
        settings = brush_mod.brush_settings
        settings.paint_source = 'VOLUME_DISTANCE'
        settings.paint_distance = 0.25 # Interaction range
        settings.use_particle_radius = True
        
        # Physics Logic: Heavier objects make bigger waves
        current_mass = sphere.rigid_body.mass
        # Base factor: Mass 1.0 -> 4.0 strength.
        base_factor = min(current_mass * 4.0, 4.0)
        settings.wave_factor = base_factor * ripple_strength
        settings.wave_clamp = 5.0 * max(1.0, ripple_strength) # Adjust clamp if strength is boosted
