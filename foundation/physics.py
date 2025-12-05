import bpy

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
    world.substeps_per_frame = substeps
    world.solver_iterations = solver_iters
    
    if world.point_cache:
        world.point_cache.use_disk_cache = False

def create_buoyancy_field(z_bottom, z_surface, strength, flow=0.5, spawn_radius=2.0, hide=True):
    """
    Creates the 'Water Density' Force Field.
    SIMULATION TYPE: Force Field (Wind)
    """
    bpy.ops.object.effector_add(type='FORCE', location=(0, 0, z_bottom)) 
    buoyancy = bpy.context.active_object
    buoyancy.name = "BuoyancyField"
    f_field = buoyancy.field
    
    buoyancy.field.type = 'WIND'
    f_field.strength = strength
    f_field.flow = flow
    f_field.z_direction = 'POSITIVE'
    
    f_field.shape = 'PLANE'
    f_field.use_max_distance = True
    f_field.distance_max = z_surface - z_bottom

    buoyancy.empty_display_type = 'PLAIN_AXES'
    buoyancy.scale = (spawn_radius, spawn_radius, 1)

    if hide:
        buoyancy.hide_set(True)
    buoyancy.hide_render = True

def create_underwater_currents(z_bottom, z_surface, strength, turbulence_scale, spawn_radius=2.0, hide=True):
    """
    Creates random underwater movement.
    SIMULATION TYPE: Force Field (Turbulence)
    """
    bpy.ops.object.effector_add(type='TURBULENCE', location=(0, 0, z_bottom))
    brownian = bpy.context.active_object
    brownian.name = "UnderwaterCurrents"
    b_field = brownian.field
    
    b_field.strength = strength
    b_field.size = turbulence_scale
    b_field.flow = 0.0
    b_field.noise = 1.0
    
    b_field.use_max_distance = True
    b_field.distance_max = z_surface - z_bottom
    b_field.shape = 'PLANE'
    
    brownian.empty_display_type = 'PLAIN_AXES'
    brownian.scale = (spawn_radius, spawn_radius, 1)

    if hide:
        brownian.hide_set(True)
    brownian.hide_render = True
