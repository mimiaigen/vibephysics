# Water Simulation Script

Generate realistic water simulations in Blender with floating spheres, physics, and dynamic paint effects.

## Quick Start

```bash
# Run with default settings
./run.sh

# Run with custom parameters
./run.sh --num-spheres 10 --wave-scale 1.5 --output my_simulation.blend

# See all available options
./run.sh --help
```

## Configuration Options

### Simulation Settings
- `--num-spheres NUM` - Number of floating spheres (default: 25)
- `--collision-spawn` - Spawn spheres randomly in a circle
- `--spawn-radius RADIUS` - Radius for random spawning (default: 2.0)

### Physics Settings
- `--no-buoyancy` - Disable buoyancy force field
- `--no-currents` - Disable underwater currents
- `--z-bottom Z` - Ocean floor Z coordinate (default: -5.0)
- `--z-surface Z` - Water surface Z coordinate (default: 0.0)
- `--buoyancy-strength STRENGTH` - Buoyancy force strength (default: 10.0)
- `--current-strength STRENGTH` - Underwater current strength (default: 20.0)
- `--turbulence-scale SCALE` - Turbulence noise pattern size (default: 1.0)
- `--ripple-strength STRENGTH` - Ripple height multiplier (default: 10.0)
- `--wave-scale SCALE` - Ocean wave scale (default: 0.5)
- `--fixed-wave-time TIME` - Lock waves to specific time (default: animated)
- `--show-force-fields` - Show force field visualizations

### Visual Settings
- `--water-color R G B A` - Water color RGBA (default: 0.0 0.6 1.0 1.0)
- `--no-caustics` - Disable caustics lighting
- `--caustic-strength STRENGTH` - Caustic light strength (default: 8000.0)
- `--caustic-scale SCALE` - Caustic pattern scale (default: 15.0)
- `--no-volumetric` - Disable volumetric fog
- `--volumetric-density DENSITY` - Fog density (default: 0.02)

### Animation Settings
- `--start-frame FRAME` - First animation frame (default: 1)
- `--end-frame FRAME` - Last animation frame (default: 250)

### Camera Settings
- `--camera-radius RADIUS` - Camera distance from center (default: 30.0)
- `--camera-height HEIGHT` - Camera height above water (default: 2.0)
- `--resolution-x WIDTH` - Render width (default: 1920)
- `--resolution-y HEIGHT` - Render height (default: 1080)

### Output Settings
- `--output FILENAME` - Output blend file name (default: water_simulation.blend)

## Examples

### Calm water with few spheres
```bash
./run.sh --num-spheres 5 --wave-scale 0.2 --output calm.blend
```

### Stormy water with many spheres
```bash
./run.sh --num-spheres 50 --wave-scale 2.0 --current-strength 40.0 --output storm.blend
```

### Quick preview (low resolution, short animation)
```bash
./run.sh --resolution-x 640 --resolution-y 480 --end-frame 50 --output preview.blend
```

### Disable visual effects for faster simulation
```bash
./run.sh --no-caustics --no-volumetric --output fast.blend
```

## Notes

- The script runs in Blender's headless mode (`-b` flag)
- Cache folders (`blendcache_*`) are automatically cleaned up
- All cache folders are ignored by git (see `.gitignore`)
- Generated `.blend` files are also ignored by git
