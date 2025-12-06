import bpy

def create_visual_water(scale, wave_scale, radius=None, time=None, start_frame=1, end_frame=250):
    """
    Creates the water surface mesh.
    SIMULATION TYPE: Ocean Modifier (Vertex Displacement)
    """
    if radius:
        # --- POOL MODE (DISPLACE on Circle) ---
        grid_size = radius * 2.2
        bpy.ops.mesh.primitive_grid_add(
            x_subdivisions=128,
            y_subdivisions=128, 
            size=grid_size, 
            location=(0, 0, 0)
        )
        water = bpy.context.active_object
        water.name = "Water_Visual"
        water.scale = (1, 1, 1)
        
        # Delete corners to make it circular
        bpy.ops.object.mode_set(mode='EDIT')
        import bmesh
        bm = bmesh.from_edit_mesh(water.data)
        
        verts_to_delete = []
        for v in bm.verts:
            if v.co.length > radius:
                verts_to_delete.append(v)
        
        bmesh.ops.delete(bm, geom=verts_to_delete, context='VERTS')
        bmesh.update_edit_mesh(water.data)
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Ocean Modifier in DISPLACE mode
        ocean_mod = water.modifiers.new(name="OceanSim", type='OCEAN')
        ocean_mod.geometry_mode = 'DISPLACE'
        ocean_mod.resolution = 12
        ocean_mod.spatial_size = int(radius * 2.5)
        
        # --- EDGE PINNING ---
        vg = water.vertex_groups.new(name="PinEdge")
        
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(water.data)
        
        dvert_lay = bm.verts.layers.deform.verify()
        
        pin_margin = 0.8
        safe_radius = max(radius - pin_margin, 0.1)
        
        for v in bm.verts:
            dist = v.co.length
            if dist < safe_radius:
                weight = 0.0
            elif dist >= radius:
                weight = 1.0
            else:
                weight = (dist - safe_radius) / pin_margin
                
            v[dvert_lay][vg.index] = weight
            
        bmesh.update_edit_mesh(water.data)
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Stabilizer plane
        bpy.ops.mesh.primitive_plane_add(size=radius*4, location=(0, 0, 0))
        stabilizer = bpy.context.active_object
        stabilizer.name = "Water_Stabilizer"
        stabilizer.hide_render = True
        stabilizer.hide_viewport = True
        
        bpy.context.view_layer.objects.active = water
        
        ocean_mod.choppiness = 0.0
        
        # Roundness fix
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=256,
            radius=radius, 
            depth=1.0, 
            location=(0, 0, 0)
        )
        round_target = bpy.context.active_object
        round_target.name = "Round_Target"
        round_target.hide_render = True
        round_target.hide_viewport = True
        
        bpy.context.view_layer.objects.active = water
        
        sw_round = water.modifiers.new(name="MakeRound", type='SHRINKWRAP')
        sw_round.target = round_target
        sw_round.wrap_method = 'NEAREST_SURFACEPOINT'
        
        vg_rim = water.vertex_groups.new(name="RimOnly")
        
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(water.data)
        dvert_lay = bm.verts.layers.deform.verify()
        
        for v in bm.verts:
            if v.co.length >= radius * 0.99:
                v[dvert_lay][vg_rim.index] = 1.0
                
        bmesh.update_edit_mesh(water.data)
        bpy.ops.object.mode_set(mode='OBJECT')
        
        sw_round.vertex_group = "RimOnly"
        bpy.ops.object.modifier_move_to_index(modifier="MakeRound", index=0)
        
    else:
        # --- OPEN OCEAN MODE (GENERATE) ---
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
        water = bpy.context.active_object
        water.name = "Water_Visual"
        water.scale = (1, 1, 1)
        
        ocean_mod = water.modifiers.new(name="OceanSim", type='OCEAN')
        ocean_mod.geometry_mode = 'GENERATE'
        ocean_mod.resolution = 12
        ocean_mod.spatial_size = 50

    ocean_mod.wave_scale = wave_scale
    
    if not radius:
        ocean_mod.choppiness = min(max(wave_scale, 0), 4.0)
    
    ocean_mod.wind_velocity = max(wave_scale * 10.0, 0.0)
    
    # Animation
    if time is not None:
        ocean_mod.time = time
    else:
        ocean_mod.time = 0.0
        water.keyframe_insert(data_path='modifiers["OceanSim"].time', frame=start_frame)
        ocean_mod.time = 5.0
        water.keyframe_insert(data_path='modifiers["OceanSim"].time', frame=end_frame)
    
    bpy.ops.object.shade_smooth()
    
    # Subdivision
    subsurf = water.modifiers.new(name="Subsurf", type='SUBSURF')
    subsurf.levels = 2
    subsurf.render_levels = 3
    
    return water

def create_flat_surface(size, z_level, subdivisions=200, name="Water_Visual"):
    """
    Creates a flat high-resolution grid for dynamic paint water ripples.
    Hides bpy.ops calls for grid creation.
    
    Args:
        size: Size of the square water plane
        z_level: Z-coordinate for water surface
        subdivisions: Grid resolution (higher = smoother ripples)
        name: Object name
        
    Returns:
        water object
    """
    bpy.ops.mesh.primitive_grid_add(
        x_subdivisions=subdivisions,
        y_subdivisions=subdivisions,
        size=size,
        location=(0, 0, z_level)
    )
    water = bpy.context.active_object
    water.name = name
    bpy.ops.object.shade_smooth()
    return water

def setup_dynamic_paint_interaction(water_obj, brush_objs, ripple_strength):
    """
    Sets up the Ripple Interaction.
    SIMULATION TYPE: Dynamic Paint (Vertex Weight / Displacement)
    
    Works with ANY mesh objects as brushes, not just spheres.
    """
    # 1. Setup Canvas (Water)
    bpy.context.view_layer.objects.active = water_obj
    bpy.ops.object.modifier_add(type='DYNAMIC_PAINT')
    canvas_mod = water_obj.modifiers[-1]
    canvas_mod.ui_type = 'CANVAS'
    bpy.ops.dpaint.type_toggle(type='CANVAS')
    bpy.ops.dpaint.output_toggle(output='A')
    
    surface = canvas_mod.canvas_settings.canvas_surfaces[-1]
    
    if surface.point_cache:
        surface.point_cache.use_disk_cache = False
        surface.point_cache.use_library_path = False
    
    surface.surface_type = 'WAVE'
    surface.wave_timescale = 1.0
    surface.wave_speed = 1.5
    surface.wave_damping = 0.05
    surface.wave_spring = 0.2
    surface.wave_smoothness = 1.0
    surface.use_wave_open_border = True

    # 2. Setup Brushes (Any Objects)
    for obj in brush_objs:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_add(type='DYNAMIC_PAINT')
        brush_mod = obj.modifiers[-1]
        brush_mod.ui_type = 'BRUSH'
        bpy.ops.dpaint.type_toggle(type='BRUSH')
        
        settings = brush_mod.brush_settings
        settings.paint_source = 'VOLUME_DISTANCE'
        settings.paint_distance = 0.25
        settings.use_particle_radius = True
        
        # Try to get mass from rigid body if available
        current_mass = 1.0
        if obj.rigid_body:
            current_mass = obj.rigid_body.mass
        
        base_factor = min(current_mass * 4.0, 4.0)
        settings.wave_factor = base_factor * ripple_strength
        settings.wave_clamp = 5.0 * max(1.0, ripple_strength)

def setup_custom_water_interaction(water_obj, interaction_groups):
    """
    Setup water interactions with specific settings for different groups.
    interaction_groups should be a list of dictionaries:
    [
        {
            'objects': [obj1, obj2],
            'paint_distance': 0.5,
            'wave_factor_scale': 1.5,
            'wave_clamp': 10.0
        },
        ...
    ]
    """
    # 1. Ensure Canvas
    bpy.context.view_layer.objects.active = water_obj
    if not any(m.type == 'DYNAMIC_PAINT' for m in water_obj.modifiers):
        bpy.ops.object.modifier_add(type='DYNAMIC_PAINT')
        
    canvas_mod = next((m for m in water_obj.modifiers if m.type == 'DYNAMIC_PAINT'), None)
    if canvas_mod:
        if canvas_mod.ui_type != 'CANVAS':
            canvas_mod.ui_type = 'CANVAS'
            # Force update if needed, though usually ui_type set is enough for properties, 
            # operator might be needed for internal data init
            try:
                bpy.ops.dpaint.type_toggle(type='CANVAS')
            except:
                pass
            
        # Ensure surface exists
        if canvas_mod.canvas_settings and not canvas_mod.canvas_settings.canvas_surfaces:
            bpy.ops.dpaint.output_toggle(output='A')
            
        if canvas_mod.canvas_settings and canvas_mod.canvas_settings.canvas_surfaces:
            surface = canvas_mod.canvas_settings.canvas_surfaces[-1]
            
            if surface.point_cache:
                surface.point_cache.use_disk_cache = False
                surface.point_cache.use_library_path = False
            
            # Verify basic settings are reasonable (though they might be set by caller previously)
            if surface.surface_type != 'WAVE':
                surface.surface_type = 'WAVE'
                surface.wave_timescale = 1.0
                surface.wave_speed = 2.0
                surface.wave_damping = 0.04
                surface.wave_spring = 0.3
                surface.wave_smoothness = 1.0
                surface.use_wave_open_border = True
        else:
            print("Warning: Could not initialize Dynamic Paint Canvas settings.")

    # 2. Setup Brushes
    for group in interaction_groups:
        objects = group.get('objects', [])
        paint_dist = group.get('paint_distance', 0.25)
        wave_scale = group.get('wave_factor_scale', 1.0)
        clamp = group.get('wave_clamp', 5.0)
        
        for obj in objects:
            bpy.context.view_layer.objects.active = obj
            
            # Remove existing if any (to reset)
            # (Optional: might want to keep? But for now let's ensure clean state)
            
            if not any(m.type == 'DYNAMIC_PAINT' for m in obj.modifiers):
                bpy.ops.object.modifier_add(type='DYNAMIC_PAINT')
                
            brush_mod = next((m for m in obj.modifiers if m.type == 'DYNAMIC_PAINT'), None)
            if brush_mod:
                brush_mod.ui_type = 'BRUSH'
                if not brush_mod.brush_settings: # Toggle type if needed
                    bpy.ops.dpaint.type_toggle(type='BRUSH')
                
                settings = brush_mod.brush_settings
                settings.paint_source = 'VOLUME_DISTANCE'
                settings.paint_distance = paint_dist
                
                # Mass-based factor
                current_mass = 1.0
                if obj.rigid_body:
                    current_mass = obj.rigid_body.mass
                
                # Base logic: roughly mass * 4
                base_strength = min(current_mass * 4.0, 4.0)
                
                settings.wave_factor = base_strength * wave_scale
                settings.wave_clamp = clamp

def setup_robot_water_interaction(water_obj, robot_parts, debris_objects, ripple_strength=15.0):
    """
    Simplified water interaction setup for robot + debris scenario.
    Robot parts get larger paint distance, debris gets normal.
    
    Args:
        water_obj: Water surface object
        robot_parts: List of robot mesh objects
        debris_objects: List of debris/ball objects
        ripple_strength: Overall ripple intensity multiplier
    """
    print("  - setting up water ripple interactions...")
    interaction_config = [
        # Robot: Larger paint distance for small parts
        {
            'objects': robot_parts,
            'paint_distance': 0.5,
            'wave_factor_scale': 1.5,
            'wave_clamp': 10.0
        },
        # Debris: Normal paint distance
        {
            'objects': debris_objects,
            'paint_distance': 0.3,
            'wave_factor_scale': 1.0,
            'wave_clamp': 8.0
        }
    ]
    
    setup_custom_water_interaction(water_obj, interaction_config)

def create_puddle_water(z_level, size, ground_cutter_obj, color=None):
    """
    Creates a water plane that is cut by the ground_cutter to form puddles.
    """
    # Create plane
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, z_level))
    water = bpy.context.active_object
    water.name = "Water_Puddles"
    
    # Subdivide for ripples
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide(number_cuts=100)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Boolean Cut
    if ground_cutter_obj:
        mod_bool = water.modifiers.new(name="CutTerrain", type='BOOLEAN')
        mod_bool.object = ground_cutter_obj
        mod_bool.operation = 'DIFFERENCE'
        
        # Apply strict solver if needed, or stick to default (Exact in new Blender)
        
        # Apply
        bpy.context.view_layer.objects.active = water
        bpy.ops.object.modifier_apply(modifier="CutTerrain")
    
    # Visuals: Ripples (Displacement)
    disp = water.modifiers.new(name="Ripples", type='DISPLACE')
    tex = bpy.data.textures.new(name="WaterNoise", type='CLOUDS')
    tex.noise_scale = 0.2
    tex.noise_depth = 1
    disp.texture = tex
    disp.strength = 0.05
    
    bpy.ops.object.shade_smooth()
    
    # Subsurf
    sub = water.modifiers.new(name="Subsurf", type='SUBSURF')
    sub.levels = 1
    sub.render_levels = 2
    
    return water
