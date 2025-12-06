# Test Scripts

This folder contains debug and testing scripts used during development.

## Files

- **`debug_dual_local.py`** - Tests dual viewport setup with local scene objects
- **`debug_walk.py`** - Tests robot walking animation and IK system
- **`inspect_ik.py`** - Inspects and debugs IK bone configurations

## Usage

These scripts are for development and debugging purposes. They may require specific assets or setups that are not part of the main examples.

To run a test script:
```bash
blender -b -P test/debug_walk.py
```

## Note

These are not part of the main simulation suite (`run_all.sh`). See the `examples/` folder for production-ready simulation scripts.
