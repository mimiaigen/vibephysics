import bpy
from .materials import create_seabed_material

def create_seabed(z_bottom, size=100):
    """
    Creates the sea floor.
    SIMULATION TYPE: Rigid Body (Passive / Static Mesh)
    
    What it does:
    - Stops heavy objects (Mass > Buoyancy) from falling forever.
    """
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, z_bottom))
    seabed = bpy.context.active_object
    seabed.name = "Seabed"
    
    bpy.ops.rigidbody.object_add(type='PASSIVE')
    seabed.rigid_body.collision_shape = 'MESH'
    
    create_seabed_material(seabed)
    return seabed

def create_uneven_ground(z_base, size, noise_scale=10.0, strength=2.0):
    """
    Creates an uneven terrain mesh using displacement.
    SIMULATION TYPE: Rigid Body (Passive / Mesh)
    """
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, z_base))
    ground = bpy.context.active_object
    ground.name = "UnevenGround"
    
    # Subdivide
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide(number_cuts=50)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # --- FLATTEN EDGES ---
    vg = ground.vertex_groups.new(name="DisplaceGroup")
    
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(ground.data)
    
    dvert_lay = bm.verts.layers.deform.verify()
    
    radius = size / 2.0
    margin = size * 0.1
    safe_radius = radius - margin
    
    for v in bm.verts:
        dist_x = abs(v.co.x)
        dist_y = abs(v.co.y)
        dist = max(dist_x, dist_y)
        
        weight = 0.0
        if dist < safe_radius:
            weight = 1.0
        elif dist >= radius:
            weight = 0.0
        else:
            weight = (radius - dist) / margin
            
        v[dvert_lay][vg.index] = weight
        
    bm.to_mesh(ground.data)
    bm.free()
    
    # Add Displacement
    disp = ground.modifiers.new(name="Displace", type='DISPLACE')
    tex = bpy.data.textures.new(name="GroundNoise", type='CLOUDS')
    tex.noise_scale = noise_scale
    tex.noise_depth = 2
    disp.texture = tex
    disp.strength = strength
    disp.mid_level = 0.5
    disp.vertex_group = "DisplaceGroup"
    
    bpy.ops.object.shade_smooth()
    
    # Physics
    bpy.ops.rigidbody.object_add(type='PASSIVE')
    ground.rigid_body.collision_shape = 'MESH'
    ground.rigid_body.friction = 0.8
    
    return ground

def create_bucket_container(z_bottom, z_surface, radius, wall_thickness=0.2):
    """
    Creates a cylindrical bucket container.
    SIMULATION TYPE: Rigid Body (Passive / Static Mesh)
    """
    water_depth = z_surface - z_bottom
    container_height = water_depth + 2.0 
    z_center = z_bottom + (container_height / 2.0)
    
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=128, 
        radius=radius, 
        depth=container_height, 
        location=(0, 0, z_center)
    )
    container = bpy.context.active_object
    container.name = "BucketContainer"
    
    # Delete top face
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_face_by_sides(number=0, type='NOTEQUAL', extend=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(container.data)
    bm.faces.ensure_lookup_table()
    
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
    
    # Solidify
    mod = container.modifiers.new(name="Solidify", type='SOLIDIFY')
    mod.thickness = wall_thickness
    mod.offset = 1.0
    
    # Bevel
    bevel = container.modifiers.new(name="Bevel", type='BEVEL')
    bevel.width = 0.05
    bevel.segments = 3
    
    bpy.ops.object.shade_smooth()
    
    # Physics
    bpy.ops.rigidbody.object_add(type='PASSIVE')
    container.rigid_body.collision_shape = 'MESH'
    container.rigid_body.friction = 0.5
    
    create_seabed_material(container)
    
    return container
