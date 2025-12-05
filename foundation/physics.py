import bpy
from .materials import create_seabed_material, create_sphere_material

def setup_rigid_body_world(substeps=60, solver_iters=60):
    """
    Initializes the Rigid Body World.
    SIMULATION TYPE: Bullet Physics (Rigid Body Dynamics)
    
    What it does:
    - Enables physics simulation in the scene.
    - Sets high substeps (60) to prevent 'tunneling' and 'explosion' of light objects (0.001kg).
    - Solver iterations (60) ensures contact stability.
    """
    if not bpy.context.scene.rigidbody_world:
        bpy.ops.rigidbody.world_add()
    
    world = bpy.context.scene.rigidbody_world
    world.substeps_per_frame = substeps  # CRITICAL for stability of light objects (0.001kg)
    world.solver_iterations = solver_iters   # CRITICAL for stable collisions
    
    # Disable disk cache to prevent "blendcache" folder creation
    if world.point_cache:
        world.point_cache.use_disk_cache = False

def create_buoyancy_field(z_bottom, z_surface, strength, flow=0.5, spawn_radius=2.0, hide=True):
    """
    Creates the 'Water Density' Force Field.
    SIMULATION TYPE: Force Field (Wind)
    """

    # Location: Z = z_bottom (Deep)
    # Max Dist: z_surface - z_bottom
    bpy.ops.object.effector_add(type='FORCE', location=(0, 0, z_bottom)) 
    buoyancy = bpy.context.active_object
    buoyancy.name = "BuoyancyField"
    f_field = buoyancy.field
    
    buoyancy.field.type = 'WIND'   # Upward wind = Buoyancy
    f_field.strength = strength # Net Upward Force
    f_field.flow = flow             # Drag/Viscosity (Prevents infinite oscillation)
    f_field.z_direction = 'POSITIVE' # Points UP
    
    # Spatial Limits (Only underwater)
    # PLANE shape ensures the force is infinite in X/Y directions (entire ocean)
    f_field.shape = 'PLANE'
    f_field.use_max_distance = True
    f_field.distance_max = z_surface - z_bottom

    # VISUALIZATION: Scale the object so the "Plane" looks like the ocean size (50m)
    # Force fields are usually empties, scaling them might not change the 'icon' size if it's drawn as a point.
    # However, 'WIND' with 'PLANE' usually draws a plane.
    # If it still looks like a sphere, we need to ensure the EMPTY DISPLAY TYPE is appropriate.
    buoyancy.empty_display_type = 'PLAIN_AXES' # Removes the "Sphere" empty draw if it exists
    # Scale matches the spawn radius to visually cover the area
    buoyancy.scale = (spawn_radius, spawn_radius, 1)

    # Hide from viewport if requested (dotted line thing)
    if hide:
        buoyancy.hide_set(True)
    buoyancy.hide_render = True  # Always hide from render

def create_underwater_currents(z_bottom, z_surface, strength, turbulence_scale, spawn_radius=2.0, hide=True):
    """
    Creates random underwater movement.
    SIMULATION TYPE: Force Field (Turbulence)
    """
    # Match Buoyancy Field: Start at Z=z_bottom
    bpy.ops.object.effector_add(type='TURBULENCE', location=(0, 0, z_bottom))
    brownian = bpy.context.active_object
    brownian.name = "UnderwaterCurrents"
    b_field = brownian.field
    
    # Physics Properties
    # Scale turbulence with wave intensity so "peace" means no currents
    b_field.strength = strength
    b_field.size = turbulence_scale
    b_field.flow = 0.0       # No drag, pure force adds velocity
    b_field.noise = 1.0      # High-freq jitter
    
    # Spatial Limits
    b_field.use_max_distance = True
    b_field.distance_max = z_surface - z_bottom # Ends at Z=z_surface
    # Ensure the random currents are GLOBAL in X/Y
    b_field.shape = 'PLANE'
    # b_field.z_direction not applicable to Turbulence
    
    # VISUALIZATION: Scale the object so the "Plane" looks like the ocean size
    brownian.empty_display_type = 'PLAIN_AXES'
    # Scale matches the spawn radius to visually cover the area
    brownian.scale = (spawn_radius, spawn_radius, 1)

    # Hide from viewport if requested
    if hide:
        brownian.hide_set(True)
    brownian.hide_render = True  # Always hide from render

def create_seabed(z_bottom):
    """
    Creates the sea floor.
    SIMULATION TYPE: Rigid Body (Passive / Static Mesh)
    
    What it does:
    - Stops heavy objects (Mass > Buoyancy) from falling forever.
    """
    # Location matches z_bottom to act as the floor of the simulation
    bpy.ops.mesh.primitive_plane_add(size=100, location=(0, 0, z_bottom))
    seabed = bpy.context.active_object
    seabed.name = "Seabed"
    # seabed.hide_render = True  <-- Removed this to make it visible
    
    bpy.ops.rigidbody.object_add(type='PASSIVE')
    seabed.rigid_body.collision_shape = 'MESH'
    
    # Assign Material
    create_seabed_material(seabed)

def create_bucket_container(z_bottom, z_surface, radius, wall_thickness=0.2):
    """
    Creates a cylindrical bucket container.
    SIMULATION TYPE: Rigid Body (Passive / Static Mesh)
    """
    # Calculate dimensions
    water_depth = z_surface - z_bottom
    # Make container slightly taller than water surface to hold waves
    container_height = water_depth + 2.0 
    # Cylinder center Z
    z_center = z_bottom + (container_height / 2.0)
    
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=128, 
        radius=radius, 
        depth=container_height, 
        location=(0, 0, z_center)
    )
    container = bpy.context.active_object
    container.name = "BucketContainer"
    
    # Delete top face to make it a bucket
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    # Select top face: normal points up (Z > 0) and is at top Z
    # Easier way: Select face at center top
    bpy.ops.mesh.select_face_by_sides(number=0, type='NOTEQUAL', extend=False) # Select nothing
    
    # We can just delete the top face by index if we know it, but indices vary.
    # Let's rely on bmesh or just select by location.
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Using bmesh to delete top face
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(container.data)
    bm.faces.ensure_lookup_table()
    
    # Find top face (highest Z center)
    top_face = None
    max_z = -float('inf')
    for f in bm.faces:
        if f.calc_center_median().z > max_z:
            max_z = f.calc_center_median().z
            top_face = f
            
    if top_face:
        bm.faces.remove(top_face)
        
    bm.to_mesh(container.data)
    bm.free()
    
    # Add Solidify to give walls thickness
    mod = container.modifiers.new(name="Solidify", type='SOLIDIFY')
    mod.thickness = wall_thickness
    mod.offset = 1.0 # Extrude outwards, preserving inner radius
    
    # Add Bevel for nice edges (optional)
    bevel = container.modifiers.new(name="Bevel", type='BEVEL')
    bevel.width = 0.05
    bevel.segments = 3
    
    bpy.ops.object.shade_smooth()
    
    # Physics
    bpy.ops.rigidbody.object_add(type='PASSIVE')
    container.rigid_body.collision_shape = 'MESH'
    container.rigid_body.friction = 0.5
    
    # Assign Material (reuse seabed material logic or create new)
    create_seabed_material(container)
    
    return container

def generate_scattered_positions(num_points, spawn_radius, min_dist, z_pos):
    """
    Generates random positions within a circle, ensuring no overlap.
    """
    import math
    import random
    
    positions = []
    max_attempts = num_points * 100  # Prevent infinite loop
    attempts = 0
    
    while len(positions) < num_points and attempts < max_attempts:
        attempts += 1
        
        # Random point in circle (uniform distribution)
        r = spawn_radius * math.sqrt(random.random())
        theta = random.random() * 2 * math.pi
        
        x = r * math.cos(theta)
        y = r * math.sin(theta)
        
        # Check collision with existing points
        collision = False
        for px, py, pz in positions:
            dist_sq = (x - px)**2 + (y - py)**2
            if dist_sq < min_dist**2:
                collision = True
                break
        
        if not collision:
            positions.append((x, y, z_pos))
            
    if len(positions) < num_points:
        print(f"⚠️ Warning: Could only fit {len(positions)}/{num_points} objects without overlap.")
        
    return positions

def create_floating_sphere(i, mass_val, location, total_spheres):
    """
    Creates a floating object.
    SIMULATION TYPE: Rigid Body (Active)
    
    What it does:
    - Standard Newtonian Physics object (F=ma).
    - Mass: Determines inertia and gravity force (F=mg).
    - Damping: Simulates Air/Water resistance.
    
    Custom Physics (Drivers):
    - 'Adaptive Damping': Real objects experience MUCH higher drag in water than air.
      Blender's Rigid Body has only one global damping value.
      We use a DRIVER to switch Damping from 0.01 (Air) to High (Water) based on Z height.
    """
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=location)
    sphere = bpy.context.active_object
    sphere.name = f"FloatingSphere_{i}_Mass_{mass_val}"
    bpy.ops.object.shade_smooth()
        
    # Visuals
    sphere_sub = sphere.modifiers.new(name="Subsurf", type='SUBSURF')
    sphere_sub.levels = 2
    sphere_sub.render_levels = 2
        
    # Physics Properties
    bpy.ops.rigidbody.object_add(type='ACTIVE')
    rb = sphere.rigid_body
    rb.mass = mass_val
    rb.collision_shape = 'SPHERE'
    rb.friction = 0.1      # Slippery (wet)
    rb.restitution = 0.2   # Low bounce
    
    # --- HYBRID PHYSICS: WATER DAMPING DRIVER ---
    # Calculate damping based on mass (Lighter objects need more damping to be stable)
    base_damping = 0.01
    adaptive_damp = base_damping + (0.005 / max(mass_val, 0.0001))
    final_damping = min(max(adaptive_damp, 0.01), 0.99)
        
    # Driver: IF (z < 0.5) THEN (WaterDamping) ELSE (AirDamping)
    for attr in ["linear_damping", "angular_damping"]:
        d_driver = sphere.driver_add(f"rigid_body.{attr}").driver
        d_driver.type = 'SCRIPTED'
        d_driver.expression = f"{final_damping} if var < 0.5 else 0.01" 
        var = d_driver.variables.new()
        var.name = "var"
        var.type = 'TRANSFORMS'
        target = var.targets[0]
        target.id = sphere
        target.transform_type = 'LOC_Z'
        
    # Material (Visuals)
    create_sphere_material(sphere, i, total_spheres)
    
    return sphere
