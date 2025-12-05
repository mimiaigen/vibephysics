import bpy
import math
import random
from .materials import create_sphere_material

def make_object_floatable(obj, mass, z_surface=0.0, collision_shape='CONVEX_HULL'):
    """
    Makes any existing mesh object physics-enabled and floatable.
    SIMULATION TYPE: Rigid Body (Active)
    
    Args:
        obj: The Blender object to make floatable
        mass: Mass in kg (affects buoyancy and inertia)
        z_surface: Water surface Z coordinate for damping transition
        collision_shape: 'SPHERE', 'BOX', 'CONVEX_HULL', 'MESH', etc.
    
    What it does:
    - Adds Rigid Body physics (Active)
    - Adds Adaptive Damping Driver for water/air transition
    """
    bpy.context.view_layer.objects.active = obj
    
    # Physics Properties
    bpy.ops.rigidbody.object_add(type='ACTIVE')
    rb = obj.rigid_body
    rb.mass = mass
    rb.collision_shape = collision_shape
    rb.friction = 0.1  # Slippery (wet)
    rb.restitution = 0.2  # Low bounce
    
    # --- HYBRID PHYSICS: WATER DAMPING DRIVER ---
    base_damping = 0.01
    adaptive_damp = base_damping + (0.005 / max(mass, 0.0001))
    final_damping = min(max(adaptive_damp, 0.01), 0.99)
    
    # Transition zone slightly above water surface
    z_threshold = z_surface + 0.5
        
    for attr in ["linear_damping", "angular_damping"]:
        d_driver = obj.driver_add(f"rigid_body.{attr}").driver
        d_driver.type = 'SCRIPTED'
        d_driver.expression = f"{final_damping} if var < {z_threshold} else 0.01" 
        var = d_driver.variables.new()
        var.name = "var"
        var.type = 'TRANSFORMS'
        target = var.targets[0]
        target.id = obj
        target.transform_type = 'LOC_Z'
    
    return obj

def create_floating_sphere(index, mass, location, total_count, z_surface=0.0):
    """
    Creates a sphere and makes it floatable.
    Convenience function for the common use case.
    """
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=location)
    sphere = bpy.context.active_object
    sphere.name = f"FloatingSphere_{index}_Mass_{mass}"
    bpy.ops.object.shade_smooth()
    
    # Visuals
    sub = sphere.modifiers.new(name="Subsurf", type='SUBSURF')
    sub.levels = 2
    sub.render_levels = 2
    
    # Make floatable
    make_object_floatable(sphere, mass, z_surface, collision_shape='SPHERE')
    
    # Material
    create_sphere_material(sphere, index, total_count)
    
    return sphere

def create_floating_cube(index, mass, location, size=0.5, z_surface=0.0):
    """
    Creates a cube and makes it floatable.
    """
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.active_object
    cube.name = f"FloatingCube_{index}_Mass_{mass}"
    
    make_object_floatable(cube, mass, z_surface, collision_shape='BOX')
    
    return cube

def create_floating_mesh(index, mesh_type, mass, location, z_surface=0.0, **kwargs):
    """
    Creates various mesh types and makes them floatable.
    
    Args:
        mesh_type: 'SPHERE', 'CUBE', 'CYLINDER', 'CONE', 'TORUS', 'MONKEY'
        **kwargs: Additional parameters for the mesh (e.g., radius, size, depth)
    """
    mesh_type = mesh_type.upper()
    
    if mesh_type == 'SPHERE':
        radius = kwargs.get('radius', 0.5)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location)
        collision = 'SPHERE'
    elif mesh_type == 'CUBE':
        size = kwargs.get('size', 1.0)
        bpy.ops.mesh.primitive_cube_add(size=size, location=location)
        collision = 'BOX'
    elif mesh_type == 'CYLINDER':
        radius = kwargs.get('radius', 0.5)
        depth = kwargs.get('depth', 1.0)
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
        collision = 'CYLINDER'
    elif mesh_type == 'CONE':
        radius1 = kwargs.get('radius1', 0.5)
        depth = kwargs.get('depth', 1.0)
        bpy.ops.mesh.primitive_cone_add(radius1=radius1, depth=depth, location=location)
        collision = 'CONE'
    elif mesh_type == 'TORUS':
        major_radius = kwargs.get('major_radius', 0.5)
        minor_radius = kwargs.get('minor_radius', 0.2)
        bpy.ops.mesh.primitive_torus_add(major_radius=major_radius, minor_radius=minor_radius, location=location)
        collision = 'CONVEX_HULL'
    elif mesh_type == 'MONKEY':
        bpy.ops.mesh.primitive_monkey_add(size=kwargs.get('size', 1.0), location=location)
        collision = 'CONVEX_HULL'
    else:
        raise ValueError(f"Unknown mesh_type: {mesh_type}")
    
    obj = bpy.context.active_object
    obj.name = f"Floating{mesh_type.capitalize()}_{index}"
    bpy.ops.object.shade_smooth()
    
    make_object_floatable(obj, mass, z_surface, collision_shape=collision)
    
    return obj

def generate_scattered_positions(num_points, spawn_radius, min_dist, z_pos, z_range=0.0):
    """
    Generates random positions within a circle/cylinder, ensuring no overlap.
    If z_range > 0, it will distribute objects vertically if needed to avoid collisions.
    """
    positions = []
    max_attempts = num_points * 200
    attempts = 0
    
    # Track current layer height if using z_range
    current_layer_z = z_pos
    layer_height = min_dist * 0.8 # Slightly overlap layers vertically is usually fine for falling objects
    
    # Keep track of attempts per layer to know when to move up
    layer_attempts = 0
    max_layer_attempts = num_points * 20
    
    while len(positions) < num_points and attempts < max_attempts:
        attempts += 1
        layer_attempts += 1
        
        # If we tried too many times on this layer, move up
        if z_range > 0 and layer_attempts > max_layer_attempts:
            current_layer_z += layer_height
            layer_attempts = 0
            # If we exceeded range, reset or stop? Let's just keep going up effectively
            if current_layer_z > z_pos + z_range:
                # Reset to bottom but maybe with offset? 
                # Actually just keep going up, better than overlap.
                pass
        
        r = spawn_radius * math.sqrt(random.random())
        theta = random.random() * 2 * math.pi
        
        x = r * math.cos(theta)
        y = r * math.sin(theta)
        
        # If z_range is active, we use the current layer Z
        # Otherwise just use z_pos
        if z_range > 0:
            # Add small random variation to Z to prevent perfect grid artifacts
            this_z = current_layer_z + random.uniform(-0.1, 0.1)
        else:
            this_z = z_pos
        
        collision = False
        for px, py, pz in positions:
            # Check 3D distance if using z_range, otherwise 2D
            if z_range > 0:
                dist_sq = (x - px)**2 + (y - py)**2 + (this_z - pz)**2
            else:
                dist_sq = (x - px)**2 + (y - py)**2
                
            if dist_sq < min_dist**2:
                collision = True
                break
        
        if not collision:
            positions.append((x, y, this_z))
            
    if len(positions) < num_points:
        print(f"⚠️ Warning: Could only fit {len(positions)}/{num_points} objects without overlap.")
        
    return positions
