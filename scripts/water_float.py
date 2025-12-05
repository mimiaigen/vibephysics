import sys
import os
import bpy
import math
import random

# Add parent directory to path to import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src import physics, visuals, materials, lighting

# --- USER CONFIGURATION ---
# Simulation Settings
N = 25  # Number of mass samples
SPHERE_MASSES = [0.001 * (1/0.001) ** (i/(N-1)) for i in range(N)]  # Logarithmic scale from 0.001 to 1
COLLISION_SPAWN = False
SPAWN_RADIUS = 2.0

# Physics Fields
ENABLE_BUOYANCY = True
ENABLE_CURRENTS = True

# Field Dimensions (Z-Axis)
FIELD_Z_BOTTOM = -5
FIELD_Z_SURFACE = 0.0

# Physics Strengths (User Control)
BUOYANCY_STRENGTH = 10.0  # 2.0 floats typical objects. Increase for stronger lift.
CURRENT_STRENGTH = 20.0   # Force of random currents.
TURBULENCE_SCALE = 1      # Size of the noise pattern (meters)
RIPPLE_STRENGTH = 10.0     # Multiplier for ripple height (1.0 = default)
WATER_WAVE_SCALE = 0.5    # Scale of the visual ocean waves (1.0 = default)
FIXED_WATER_WAVE_TIME = None # If set (e.g., 2.0), locks the wave to that time. None = animated.
HIDE_FORCE_FIELDS = True   # Set to True to hide the "dotted line" representations (Eye icon)

# Realism / Lighting Settings (Caustics & God Rays)
WATER_COLOR = (0.0, 0.6, 1.0, 1.0) # Deep Blue-ish (RGBA)
ENABLE_CAUSTICS = True
CAUSTIC_STRENGTH = 8000.0     # Sun Strength (Sun is much brighter per unit than Spot)
CAUSTIC_SCALE = 15.0       # Scale of the light patterns
VOLUMETRIC_ENABLED = True
VOLUMETRIC_DENSITY = 0.02  # Density of the water "fog"


# Animation Settings
START_FRAME = 1
END_FRAME = 250

# Camera Settings
CAMERA_RADIUS = 30.0    # Distance from the center
CAMERA_HEIGHT = 2.0     # Height above the water
RESOLUTION_X = 1920
RESOLUTION_Y = 1080
# --------------------------

def run_simulation_setup():
    print("Initializing Water Simulation...")
    
    # 0. Clear Handlers (avoid duplicates)
    bpy.app.handlers.frame_change_pre.clear()
    
    # cleanup
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # 1. Physics Environment
    physics.setup_rigid_body_world()
    
    if ENABLE_BUOYANCY:
        physics.create_buoyancy_field(
            z_bottom=FIELD_Z_BOTTOM,
            z_surface=FIELD_Z_SURFACE,
            strength=BUOYANCY_STRENGTH,
            spawn_radius=SPAWN_RADIUS,
            hide=HIDE_FORCE_FIELDS
        )
        
    if ENABLE_CURRENTS:
        # Calculate effective strength based on wave scale
        effective_strength = CURRENT_STRENGTH * WATER_WAVE_SCALE
        physics.create_underwater_currents(
            z_bottom=FIELD_Z_BOTTOM,
            z_surface=FIELD_Z_SURFACE,
            strength=effective_strength,
            turbulence_scale=TURBULENCE_SCALE,
            spawn_radius=SPAWN_RADIUS,
            hide=HIDE_FORCE_FIELDS
        )
        
    physics.create_seabed(z_bottom=FIELD_Z_BOTTOM)
    
    # 2. Visual Environment
    water_visual = visuals.create_visual_water(
        scale=1.0, # Fixed scale in original
        wave_scale=WATER_WAVE_SCALE,
        time=FIXED_WATER_WAVE_TIME,
        start_frame=START_FRAME,
        end_frame=END_FRAME
    )
    materials.create_water_material(water_visual, color=WATER_COLOR)
    
    # 3. Objects
    spheres = []
    base_z = 5.0
    spacing = 1.2
    start_x = -((len(SPHERE_MASSES) - 1) * spacing) / 2.0
    
    for i, mass in enumerate(SPHERE_MASSES):
        if COLLISION_SPAWN:
            r = SPAWN_RADIUS * math.sqrt(random.random())
            theta = random.random() * 2 * math.pi
            
            x_pos = r * math.cos(theta)
            y_pos = r * math.sin(theta)
            z_pos = base_z + (i * 2.0)
            
            pos = (x_pos, y_pos, z_pos)
        else:
            pos = (start_x + i * spacing, 0.0, base_z + i * 0.5)
            
        sphere = physics.create_floating_sphere(i, mass, pos, len(SPHERE_MASSES))
        spheres.append(sphere)
        
    # 4. Interactions
    visuals.setup_dynamic_paint_interaction(water_visual, spheres, RIPPLE_STRENGTH)
    
    # 5. Rendering
    lighting.setup_lighting_and_camera(
        camera_radius=CAMERA_RADIUS,
        camera_height=CAMERA_HEIGHT,
        resolution_x=RESOLUTION_X,
        resolution_y=RESOLUTION_Y,
        start_frame=START_FRAME,
        end_frame=END_FRAME,
        enable_caustics=ENABLE_CAUSTICS,
        enable_volumetric=VOLUMETRIC_ENABLED,
        z_surface=FIELD_Z_SURFACE,
        z_bottom=FIELD_Z_BOTTOM,
        volumetric_density=VOLUMETRIC_DENSITY,
        caustic_scale=CAUSTIC_SCALE,
        caustic_strength=CAUSTIC_STRENGTH
    )
    
    print("✅ Simulation Ready!")
    print("   - Physics: Bullet Rigid Body + Force Fields (Buoyancy, Currents)")
    print("   - Visuals: Ocean Modifier + Dynamic Paint (Ripples)")

if __name__ == "__main__":
    run_simulation_setup()
    
    # CRITICAL: Disable disk cache RIGHT BEFORE saving to ensure it persists
    print("Disabling all disk caches before save...")
    if bpy.context.scene.rigidbody_world and bpy.context.scene.rigidbody_world.point_cache:
        bpy.context.scene.rigidbody_world.point_cache.use_disk_cache = False
        print("  - Disabled Rigid Body World cache")
        
    for obj in bpy.data.objects:
        for mod in obj.modifiers:
            if mod.type == 'DYNAMIC_PAINT':
                if mod.canvas_settings:
                    for surface in mod.canvas_settings.canvas_surfaces:
                        if hasattr(surface, "point_cache") and surface.point_cache:
                            surface.point_cache.use_disk_cache = False
                            print(f"  - Disabled cache for {obj.name} - {surface.name}")
    
    blend_path = os.path.abspath("water_simulation.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print("✅ Saved to water_simulation.blend")
    
    # Clean up blendcache folder (Blender creates it despite use_disk_cache=False)
    # This is a known Blender bug where the setting reverts to True on save
    import shutil
    cache_folder = os.path.abspath("blendcache_water_simulation")
    if os.path.exists(cache_folder):
        shutil.rmtree(cache_folder)
        print(f"🗑️  Removed cache folder: {cache_folder}")
