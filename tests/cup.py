import bpy
import math

def create_cup_and_sphere():
    # Ensure Object Mode and Frame 1
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.scene.frame_set(1)

    # Clear existing objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # --- 1. Create a "Real" Cup (Hollow Cylinder) ---
    # Create cylinder without caps
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=64,
        radius=1.0,
        depth=2.0,
        location=(0, 0, 1.0),
        enter_editmode=False,
        end_fill_type='NOTHING' 
    )
    cup = bpy.context.active_object
    cup.name = "Cup"
    cup.location = (0, 0, 1.0)
    
    # Fill the bottom
    # Default cylinder local vertices z range is -1 to 1. 1 is top, -1 is bottom.
    # We want to fill z = -1.
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    
    for v in cup.data.vertices:
        if v.co.z < -0.99:
            v.select = True
            
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.fill() # Fills the bottom
    bpy.ops.object.mode_set(mode='OBJECT')

    # Add Solidify Modifier to give thickness
    mod = cup.modifiers.new(name="Solidify", type='SOLIDIFY')
    mod.thickness = 0.1
    mod.offset = 1.0 # Offset towards outside or inside
    
    # Apply the solidify modifier to make the geometry real for the physics/constraint to respect thickness
    # Actually for shrinkwrap, it works on the mesh. If we don't apply, it wraps to the base mesh (thin paper).
    # If we want it to wrap to the THICK surface, we should apply it or target the modified mesh.
    # Leaving it unapplied means it wraps to the infinity thin cylinder.
    # Applying it makes it a double-walled mesh.
    # Let's apply it.
    bpy.ops.object.modifier_apply(modifier="Solidify")
    
    # Recalculate normals to ensure outside is outside
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Smooth shading
    for poly in cup.data.polygons:
        poly.use_smooth = True

    # --- 2. Create the Sphere ---
    sphere_radius = 0.2
    # Start slightly outside. Cup radius is 1.0 + thickness.
    # Solidify with offset 1.0 adds thickness to the outside? 
    # Default solidify offset -1 is inside, 1 is outside. 
    # So radius becomes 1.1 roughly.
    start_x = 1.3 
    
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=sphere_radius,
        location=(start_x, 0, 1.0)
    )
    sphere = bpy.context.active_object
    sphere.name = "Sphere"
    bpy.ops.object.shade_smooth()

    # --- 3. Animation Setup (Orbit) ---
    # Create the controller (Small Cube instead of Empty for RB stability) in the center of the cup
    bpy.ops.mesh.primitive_cube_add(size=0.2, location=(0, 0, 1.0))
    controller = bpy.context.active_object
    controller.name = "SphereController"
    controller.display_type = 'WIRE'
    # Hide from render only
    controller.hide_render = True

    # Animate Controller Location (Continuous Spiral Out)
    # Radius grows linearly. Z goes Up then Down.
    total_frames = 250
    rotations = 3
    
    for f in range(1, total_frames + 1):
        t = (f - 1) / (total_frames - 1) # Normalized time 0 to 1
        angle = t * rotations * 2 * math.pi
        
        # Continuous Radius Growth (Center to Outside)
        r = 0.1 + 1.5 * t  # 0.1 -> 1.6
        
        # Simple Z Phase: Up then Down
        if t < 0.5:
            # Phase 1: Up
            phase_t = t / 0.5
            z = 0.5 + 2.3 * phase_t # 0.5 -> 2.8
        else:
            # Phase 2: Down
            phase_t = (t - 0.5) / 0.5
            z = 2.8 - 2.3 * phase_t # 2.8 -> 0.5
            
        # Convert polar to cartesian
        x = r * math.cos(angle)
        y = r * math.sin(angle)
        
        controller.location = (x, y, z)
        controller.keyframe_insert(data_path="location", frame=f)

    # Set scene length
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = total_frames

    # Linear Interpolation
    if controller.animation_data and controller.animation_data.action:
        try:
            for fcurve in controller.animation_data.action.fcurves:
                for kf in fcurve.keyframe_points:
                    kf.interpolation = 'LINEAR'
        except AttributeError:
             print("Warning: Could not set linear interpolation. Action object might not support .fcurves or API has changed.")

    # --- 4. Rigid Body Setup ---
    # Ensure Rigid Body World exists
    if not bpy.context.scene.rigidbody_world:
        bpy.ops.rigidbody.world_add()

    # 4a. Cup: Passive, Mesh (accurate collision for hollow object)
    bpy.ops.object.select_all(action='DESELECT')
    cup.select_set(True)
    bpy.context.view_layer.objects.active = cup
    bpy.ops.rigidbody.object_add()
    cup.rigid_body.type = 'PASSIVE'
    cup.rigid_body.collision_shape = 'MESH'
    cup.rigid_body.friction = 1.0 # High friction for rolling
    cup.rigid_body.use_margin = True
    cup.rigid_body.collision_margin = 0.005 # Small margin to avoid "plugging" the hole if it sees it as too thick

    # 4b. Controller: Passive, Animated (It drives the motion)
    bpy.ops.object.select_all(action='DESELECT')
    controller.select_set(True)
    bpy.context.view_layer.objects.active = controller
    bpy.ops.rigidbody.object_add()
    controller.rigid_body.type = 'PASSIVE'
    controller.rigid_body.kinematic = True # 'Animated' check box
    controller.rigid_body.collision_shape = 'BOX' # Explicit shape

    # 4c. Sphere: Active, Sphere (Physical object)
    # Use Kinematic (Animated) to follow controller precisely + Shrinkwrap
    bpy.ops.object.select_all(action='DESELECT')
    sphere.select_set(True)
    bpy.context.view_layer.objects.active = sphere
    bpy.ops.rigidbody.object_add()
    sphere.rigid_body.type = 'ACTIVE'
    sphere.rigid_body.collision_shape = 'SPHERE'
    sphere.rigid_body.kinematic = True # drive by animation/constraint
    sphere.rigid_body.friction = 1.0 
    sphere.rigid_body.linear_damping = 0.5
    sphere.rigid_body.angular_damping = 0.5

    # Parent Sphere to Controller to follow its orbit
    sphere.parent = controller
    # Reset sphere location to zero relative to controller (since controller is at the orbit point)
    sphere.location = (0,0,0)

    # Add Shrinkwrap to keep it on surface (trajectory Project)
    const = sphere.constraints.new(type='SHRINKWRAP')
    const.target = cup
    const.shrinkwrap_type = 'NEAREST_SURFACE'
    const.distance = sphere_radius # Touch surface
    
    print("Created Hollow Cup and Sphere. Kinematic Sphere + Shrinkwrap for controlled trajectory.")

if __name__ == "__main__":
    create_cup_and_sphere()
