# VibePhysics

A Blender physics simulation framework for creating realistic water and fluid dynamics simulations.

## Project Structure

```
vibephysics/
├── foundation/          # Mid-level physics implementation
│   ├── physics.py      # Core physics systems (rigid body, buoyancy, currents)
│   ├── visuals.py      # Visual effects (ocean modifier, dynamic paint)
│   ├── materials.py    # Material shaders (water, seabed, objects)
│   └── lighting.py     # Lighting and camera setup
├── scripts/            # High-level simulation scenarios
│   ├── water_float.py  # Floating spheres with mass variations
│   ├── water_rise.py   # Calm water rising simulation
│   ├── water_bucket.py    # Periodic water bucket
│   └── storm.py        # Intense storm with debris
└── README.md
```

## Foundation Module

The `foundation` directory contains reusable mid-level physics implementations:

### `physics.py`
- **`setup_rigid_body_world()`** - Initializes Bullet physics with optimized substeps
- **`create_buoyancy_field()`** - Upward force field simulating water buoyancy
- **`create_underwater_currents()`** - Turbulence force for water movement
- **`create_seabed()`** - Ocean floor collision mesh
- **`create_floating_sphere()`** - Physics-enabled object with adaptive damping

### `visuals.py`
- **`create_visual_water()`** - Ocean modifier for realistic wave surfaces
- **`setup_dynamic_paint_interaction()`** - Ripple effects from object interactions

### `materials.py`
- **`create_water_material()`** - Transparent water shader with caustics support
- **`create_seabed_material()`** - Ground material
- **`create_sphere_material()`** - Colorful materials for objects

### `lighting.py`
- **`setup_lighting_and_camera()`** - Complete scene lighting with caustics and volumetrics
- **`create_caustics_light()`** - Animated caustic pattern projection
- **`create_underwater_volume()`** - Volumetric god rays

## Simulation Scripts

Each script in the `scripts/` directory demonstrates different physics scenarios using the foundation modules:

### 1. **water_float.py** - Classic Floating Objects
Demonstrates objects with different masses floating and interacting with water.

**Features:**
- Multiple spheres with logarithmic mass distribution
- Buoyancy force fields
- Underwater currents
- Dynamic paint ripples
- Customizable wave intensity

**Usage:**
```bash
blender -b -P scripts/water_float.py -- --num-spheres 25 --wave-scale 1.0
```

**Key Arguments:**
- `--num-spheres` - Number of floating objects
- `--wave-scale` - Wave intensity (0.1 = calm, 2.0 = rough)
- `--buoyancy-strength` - Upward force strength
- `--output` - Output .blend file name

---

### 2. **water_rise.py** - Rising Water Level
Simulates calm water rising from z=0 to a specified height, revealing how objects float as water level increases.

**Features:**
- Animated water level rise
- Very calm waves (wave_scale = 0.1)
- Objects initially resting on seabed
- Realistic buoyancy as water rises

**Usage:**
```bash
blender -b -P scripts/water_rise.py -- --rise-height 10.0 --rise-duration 200
```

**Key Arguments:**
- `--rise-height` - Final water height (default: 10.0)
- `--rise-duration` - Number of frames for rise (default: 200)
- `--calm-wave-scale` - Wave scale for calm water (default: 0.1)
- `--num-objects` - Number of floating objects

---

### 3. **water_bucket.py** - Water Bucket Simulation
Simulates a water bucket with periodic waves and multiple floating objects distributed across the surface.

**Features:**
- Grid distribution of floats
- Periodic wave patterns
- Enhanced underwater currents
- Strong ripple interactions

**Usage:**
```bash
blender -b -P scripts/water_bucket.py -- --wave-intensity 1.5 --num-floats 20
```

**Key Arguments:**
- `--wave-intensity` - Wave strength multiplier
- `--num-floats` - Number of floating objects
- `--bucket-radius` - Radius of the bucket area
- `--ripple-strength` - Ripple intensity

---

### 4. **storm.py** - Storm Simulation
Extreme weather simulation with violent waves, chaotic forces, and debris being tossed around.

**Features:**
- Intense wave patterns (storm_intensity = 3.0)
- Chaotic turbulence forces
- Random debris distribution
- Dense atmospheric fog
- Dark, dramatic lighting

**Usage:**
```bash
blender -b -P scripts/storm.py -- --storm-intensity 3.0 --num-debris 30
```

**Key Arguments:**
- `--storm-intensity` - Overall storm severity (1.0-5.0)
- `--wind-chaos` - Turbulence force strength
- `--num-debris` - Number of debris objects
- `--volumetric-density` - Fog density

---

## Common Arguments (All Scripts)

### Physics
- `--z-bottom` - Ocean floor Z coordinate
- `--z-surface` - Water surface Z coordinate
- `--show-force-fields` - Visualize force fields in viewport

### Animation
- `--start-frame` - First frame (default: 1)
- `--end-frame` - Last frame (default: 250)

### Camera
- `--camera-radius` - Distance from center
- `--camera-height` - Height above water
- `--resolution-x` - Render width (default: 1920)
- `--resolution-y` - Render height (default: 1080)

### Visual Effects
- `--water-color` - RGBA color (e.g., `0.0 0.6 1.0 1.0`)
- `--no-caustics` - Disable light caustics
- `--no-volumetric` - Disable god rays
- `--caustic-strength` - Intensity of caustic patterns
- `--volumetric-density` - Fog/scatter density

### Output
- `--output` - Output .blend filename

## Creating Custom Simulations

To create your own simulation:

1. **Import foundation modules:**
```python
from foundation import physics, visuals, materials, lighting
```

2. **Setup physics environment:**
```python
physics.setup_rigid_body_world()
physics.create_buoyancy_field(z_bottom=-5, z_surface=0, strength=10.0)
physics.create_underwater_currents(z_bottom=-5, z_surface=0, strength=20.0)
physics.create_seabed(z_bottom=-5)
```

3. **Create visual water:**
```python
water = visuals.create_visual_water(scale=1.0, wave_scale=1.0)
materials.create_water_material(water)
```

4. **Add objects:**
```python
sphere = physics.create_floating_sphere(index=0, mass_val=1.0, location=(0,0,5))
```

5. **Setup interactions:**
```python
visuals.setup_dynamic_paint_interaction(water, [sphere], ripple_strength=10.0)
```

6. **Configure rendering:**
```python
lighting.setup_lighting_and_camera(
    camera_radius=30, 
    camera_height=5,
    enable_caustics=True,
    enable_volumetric=True
)
```

## Physics Principles

### Buoyancy System
- Uses **Wind force field** pointing upward
- Strength determines lift force
- `flow` parameter adds water resistance/drag
- Limited to `z_bottom` → `z_surface` range

### Underwater Currents
- Uses **Turbulence force field**
- Creates random Brownian motion
- Simulates water circulation patterns
- Scaled with wave intensity

### Adaptive Damping
Objects have **Z-dependent damping**:
- **Above water (z > 0.5)**: Low damping (0.01) - air resistance
- **Below water (z < 0.5)**: High damping (mass-based) - water resistance

This creates realistic behavior where objects slow down when submerged.

### Dynamic Paint Ripples
- Water surface acts as **Canvas** (wave equation)
- Objects act as **Brushes** (wave source)
- Ripple strength scales with object mass
- **Note:** Ripples are visual only (don't push objects)

## Technical Notes

- **Rigid Body Substeps**: Set to 60+ for stability with light objects (0.001kg)
- **Ocean Resolution**: Optimized to level 12 for performance
- **Subdivision Levels**: Viewport = 1, Render = 2 (performance vs quality)
- **Cycles Samples**: 128 (balance of quality and speed)
- **Disk Cache**: Automatically disabled to prevent `blendcache` folders

## Requirements

- Blender 3.0+ (tested on 3.6, 4.0, 4.2)
- Cycles render engine (for caustics and volumetrics)
- Python 3.x (bundled with Blender)

## License

See LICENSE file.
