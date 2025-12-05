import bpy

def create_visual_water(scale, wave_scale, radius=None, time=None, start_frame=1, end_frame=250):
    """
    Creates the water surface mesh.
    SIMULATION TYPE: Ocean Modifier (Vertex Displacement)
    """
    # 1. Create Base Mesh
    if radius:
        # --- POOL MODE (DISPLACE on Circle) ---
        # Create a round, grid-filled mesh manually to avoid Boolean issues ("flashing")
        # We create a grid, select vertices outside radius, and delete them.
        
        # Create grid (Plane)
        # Size needs to be slightly larger than diameter to ensure coverage
        grid_size = radius * 2.2
        bpy.ops.mesh.primitive_grid_add(
            x_subdivisions=128, # Increased from 64 for smoother base mesh
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
        
        # Select vertices outside radius
        verts_to_delete = []
        for v in bm.verts:
            if v.co.length > radius:
                verts_to_delete.append(v)
        
        bmesh.ops.delete(bm, geom=verts_to_delete, context='VERTS')
        bmesh.update_edit_mesh(water.data)
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Now add Ocean Modifier in DISPLACE mode
        ocean_mod = water.modifiers.new(name="OceanSim", type='OCEAN')
        ocean_mod.geometry_mode = 'DISPLACE' # Displace existing mesh
        ocean_mod.resolution = 12
        ocean_mod.spatial_size = int(radius * 2.5)
        
        # --- EDGE PINNING ---
        # Create a Vertex Group for pinning edges to Z=0
        vg = water.vertex_groups.new(name="PinEdge")
        
        # Assign weights: 0.0 in center (free), 1.0 at edge (pinned)
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(water.data)
        
        dvert_lay = bm.verts.layers.deform.verify()
        
        pin_margin = 0.8 # meters from edge where waves fade out
        safe_radius = max(radius - pin_margin, 0.1)
        
        for v in bm.verts:
            dist = v.co.length
            if dist < safe_radius:
                weight = 0.0
            elif dist >= radius:
                weight = 1.0
            else:
                # Linear fade 0 -> 1
                weight = (dist - safe_radius) / pin_margin
                
            v[dvert_lay][vg.index] = weight
            
        bmesh.update_edit_mesh(water.data)
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Assign Vertex Group to Ocean Modifier? 
        # Ocean Modifier python API for vertex group is tricky/version dependent.
        # Instead, we use a Shrinkwrap modifier to force the edges to Z=0.
        
        # Create a hidden stabilizer plane at Z=0
        bpy.ops.mesh.primitive_plane_add(size=radius*4, location=(0, 0, 0))
        stabilizer = bpy.context.active_object
        stabilizer.name = "Water_Stabilizer"
        stabilizer.hide_render = True
        stabilizer.hide_viewport = True
        
        # Switch back to water
        bpy.context.view_layer.objects.active = water
        
        # Force Choppiness to 0 for Pool Mode to prevent X/Y edge separation
        ocean_mod.choppiness = 0.0
        
        # --- ROUNDNESS FIX ---
        # The grid, even high res, looks aliased at the edge.
        # We can fix this by Shrinkwrapping the OUTER edge to a perfect cylinder.
        # Reuse the "PinEdge" group but only for vertices with weight > 0.9 (the very edge).
        
        # Create a Cylinder Target for horizontal roundness
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=256, # High res circle
            radius=radius, 
            depth=1.0, 
            location=(0, 0, 0)
        )
        round_target = bpy.context.active_object
        round_target.name = "Round_Target"
        round_target.hide_render = True
        round_target.hide_viewport = True
        
        bpy.context.view_layer.objects.active = water
        
        # Horizontal Shrinkwrap (Nearest Vertex on Cylinder Surface)
        sw_round = water.modifiers.new(name="MakeRound", type='SHRINKWRAP')
        sw_round.target = round_target
        sw_round.wrap_method = 'NEAREST_SURFACEPOINT'
        # We only want to affect the outer edge vertices
        # But we need a vertex group that is ONLY the edge (weight=1.0)
        # Let's make a new one quickly
        
        vg_rim = water.vertex_groups.new(name="RimOnly")
        
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(water.data)
        dvert_lay = bm.verts.layers.deform.verify()
        
        for v in bm.verts:
            # Only select vertices that are basically at the radius boundary
            if v.co.length >= radius * 0.99:
                v[dvert_lay][vg_rim.index] = 1.0
                
        bmesh.update_edit_mesh(water.data)
        bpy.ops.object.mode_set(mode='OBJECT')
        
        sw_round.vertex_group = "RimOnly"
        
        # Important: Move "MakeRound" BEFORE "EdgePin" (Z-stabilize) or Subsurf
        # Actually, let's put it first to reshape the grid into a circle before displacement
        # Move to top
        bpy.ops.object.modifier_move_to_index(modifier="MakeRound", index=0)
        
    else:
        # --- OPEN OCEAN MODE (GENERATE) ---
        # Standard Ocean Modifier generation
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
        water = bpy.context.active_object
        water.name = "Water_Visual"
        water.scale = (1, 1, 1)
        
        ocean_mod = water.modifiers.new(name="OceanSim", type='OCEAN')
        ocean_mod.geometry_mode = 'GENERATE'
        ocean_mod.resolution = 12
        ocean_mod.spatial_size = 50

    # Link parameters to wave_scale to create a "Storm" vs "Calm" slider
    ocean_mod.wave_scale = wave_scale
    
    # Only apply choppiness if NOT in pool mode (radius is None)
    # Or if we are in pool mode, we already set it to 0.0 above, so we preserve it.
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
    
    # Add Subdivision for Dynamic Paint resolution
    # For the pool (Displace mode), the mesh is already subdivided (64x64).
    # Increasing subdivisions improves ripple quality and reduces grid artifacts
    subsurf = water.modifiers.new(name="Subsurf", type='SUBSURF')
    
    # Apply high-quality subdivision to BOTH pool and open water
    # User preferred the pool quality ("dropping ball effect")
    subsurf.levels = 2
    subsurf.render_levels = 3
    
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
    surface.wave_timescale = 1.0 # Increased from 0.8 for slightly faster physics
    surface.wave_speed = 1.5
    surface.wave_damping = 0.05 # Moderate damping to decay waves naturally
    surface.wave_spring = 0.2   # Increased from 0.1: Higher tension makes water settle faster
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
