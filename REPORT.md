# Analysis Report: `tests/nunchunks.py`

## Executive Summary
The file `tests/nunchunks.py` is a monolithic Python script (~10,357 lines) that programmatically reconstructs a sophisticated Blender Geometry Nodes system named `UGRS_MainNodeTree_v1.0`. It implements a **full feature-complete Gaussian Splat renderer** entirely within Blender's Geometry Nodes, supporting both 3DGS (static) and 4DGS (dynamic/animated) splats.

---

## Part 1: Architecture Overview

### Node Group Hierarchy

```
Nunchucks (Wrapper/Entry Point)
    └── UGRS_MainNodeTree_v1.0 (Core Engine)
            ├── Input Method (3DGS vs 4DGS switcher)
            ├── Menu Switching (Frame control logic)
            ├── Sigmod_G (Opacity sigmoid activation)
            └── SH_G (Spherical Harmonics view-dependent color)
```

### Input Sources (Lines 1056-1072)
The system accepts three input modes:
1. **3DGS** (`Collection`): A collection of PLY mesh objects for frame-by-frame 3DGS sequence
2. **4DGS** (`Object`): A single object containing 4D Gaussian Splat data with `motion_*` attributes
3. **multi4DGS** (`Collection`): Multiple 4DGS objects in a collection

---

## Part 2: Viewport Visualization Pipeline

### Step 1: Geometry Input
The system reads geometry from Collections or Objects using `GeometryNodeCollectionInfo` or `GeometryNodeObjectInfo`.

### Step 2: Attribute Reading
The following PLY attributes are read (Lines 1567-1618):

| Attribute | Type | Description |
|-----------|------|-------------|
| `scale_0`, `scale_1`, `scale_2` | FLOAT | Gaussian scale (log-space) |
| `rot_0`, `rot_1`, `rot_2`, `rot_3` | FLOAT | Quaternion rotation (w, x, y, z) |
| `opacity` | FLOAT | Opacity (logit-space, needs sigmoid) |
| `f_dc_0`, `f_dc_1`, `f_dc_2` | FLOAT | Spherical Harmonics degree 0 (color) |
| `motion_0`, `motion_1`, `motion_2` | FLOAT | 4D motion vectors |
| `t_scale` | FLOAT | Time scale for 4D animation |

### Step 3: Quaternion to Rotation Conversion (Line 3607)
```python
FunctionNodeQuaternionToRotation  # Converts rot_0..rot_3 to Blender rotation
```
The `rot_*` attributes are combined and converted to a rotation using Blender's built-in `QuaternionToRotation` node.

### Step 4: Scale Processing (Lines 1567-1578)
```python
# scale attributes are in log-space, converted via exponent
scale_vector = CombineXYZ(exp(scale_0), exp(scale_1), exp(scale_2))
```

### Step 5: Spherical Harmonics Color (Lines 3714-3798)
The SH coefficients used are:
```python
C0 = 0.282094806432724      # SH degree 0 constant
C1 = 0.48860251903533936    # SH degree 1 constant
C20 = 1.0925484895706177    # SH degree 2 constants
C21 = -1.0925484895706177
C22 = 0.31539157032966614
```

The color computation follows the standard 3DGS SH evaluation:
```
color = C0 * SH_0 + C1 * (y*SH_1 + z*SH_2 + x*SH_3) + ...
```
Where `(x, y, z)` is the normalized view direction.

### Step 6: Opacity Sigmoid (Lines 312-471, `sigmod_g_1`)
```python
# Sigmoid function: 1 / (1 + exp(-x))
opacity_final = 1.0 / (1.0 + EXPONENT(-opacity_raw))
```

### Step 7: Display Mode Selection (Lines 1833-1844)
Three display modes are available via `GeometryNodeMenuSwitch`:
1. **PointCloud**: Raw point cloud display
2. **Mesh**: Instance mesh geometry on points
3. **MotionLine**: Visualize motion vectors as lines

### Step 8: Mesh Instancing (Lines 4700-4710)
Mesh options for instancing:
- **Cube**
- **IcoSphere**
- **DualIcoSphere** (default)

The instancing uses `GeometryNodeInstanceOnPoints` (Line 1758) with:
- **Position**: Point position (+ motion offset for 4D)
- **Rotation**: Quaternion converted to rotation
- **Scale**: Exponential of `scale_*` attributes

### Step 9: Point Cloud Mode (Lines 4711-4718)
```python
GeometryNodeMeshToPoints(mode='VERTICES')  # Converts mesh to point cloud
# Radius is controlled by `Point Radius` input * computeAlpha
```

### Step 10: Material Assignment (Lines 4879-4885)
```python
GeometryNodeSetMaterial(material="UGRP_Shader_G")
```
**Important**: The script does NOT create this material. It expects `UGRP_Shader_G` to exist.

---

## Part 3: 4D Gaussian Splat Animation

### Time Deformation Logic (Lines 1687-1756)
The 4D animation works by:

1. **Read motion vector**: `motion_vec = CombineXYZ(motion_0, motion_1, motion_2)`
2. **Read time scale**: `t_scale` (from attribute)
3. **Compute time offset**: `t = (frame - t_center) / t_scale`
4. **Compute Gaussian weight**: `weight = exp(-0.5 * t^2 / t_scale^2)`
5. **Apply motion**: `position_offset = motion_vec * t * weight`

The marginal time (`ttt` attribute) is used to compute temporal visibility, ensuring splats fade in/out smoothly.

### Frame Control (Lines 1129-1183)
- **Control Method**: Frame Index vs SRC Frame
- **FrameOffset**: On/Off toggle
- **Frame_Index_input**: Manual frame override

---

## Part 4: Stored Attributes for Shader

The Geometry Nodes store these attributes for the shader material:

| Attribute Name | Type | Purpose |
|----------------|------|---------|
| `computeAlpha` | FLOAT | Final computed opacity (sigmoid × marginal) |
| `SH_0` | FLOAT_VECTOR | Base SH color (f_dc_0, f_dc_1, f_dc_2) |
| `Precompute` | FLOAT_VECTOR | Precomputed view-dependent color |
| `PPP` | FLOAT_VECTOR | Projected point position |
| `G_Rot` | FLOAT_VECTOR | Gaussian rotation (Euler) |
| `inv_L0`, `inv_L1`, `inv_L2` | FLOAT_VECTOR | Inverse covariance matrix rows |
| `Mode` | INT | Shader mode index |

---

## Part 5: Material Requirements (`UGRP_Shader_G`)

The expected material should:
1. Read `computeAlpha` for transparency
2. Read `Precompute` or `SH_0` for color
3. Support HDR mode toggle
4. Handle different shader modes (Gaussian, Ring, Wireframe, Freestyle)

---

## Part 6: Recommendations for Reimplementation

### Minimal 3DGS Viewer (Priority Order)

1. **PLY Loader** (existing in `gsplat.py`)
   - Ensure attributes are named correctly (`f_dc_*`, `rot_*`, `scale_*`, `opacity`)

2. **Simple Geometry Nodes**
   - Read SH and convert to RGB: `color = 0.282 * f_dc + 0.5`
   - Read opacity and apply sigmoid: `alpha = 1 / (1 + exp(-opacity))`
   - Instance IcoSphere with scale = `exp(scale_*)`

3. **Simple Material**
   - Read vertex color attribute
   - Use emission shader for unlit display
   - Apply alpha from `computeAlpha` attribute

### Full 4DGS Support (Advanced)

1. **Add motion deformation** in Geometry Nodes
2. **Frame driver** that reads scene frame
3. **Temporal fading** using Gaussian weight

### Key Constants to Reuse

```python
# Spherical Harmonics
SH_C0 = 0.28209479177387814  # Used in gsplat.py
SH_C1 = 0.4886025119029199
SH_C2_0 = 1.0925484305920792
SH_C2_1 = -1.0925484305920792
SH_C2_2 = 0.31539156525252005

# Scale conversion
# scale_final = exp(scale_raw)

# Opacity conversion
# opacity_final = sigmoid(opacity_raw) = 1 / (1 + exp(-opacity_raw))
```

---

## Part 7: Code Extraction Recommendations

The following functions from `nunchunks.py` can be extracted and adapted:

1. **`sigmod_g_1_node_group`** (Lines 312-471): Sigmoid activation
2. **`sh_g_1_node_group`** (Lines 474-997): View-dependent SH color
3. **Quaternion handling** (Lines 3606-3608): Rotation conversion
4. **Scale/Opacity pipeline** (Lines 1567-1756): Attribute processing

These can serve as reference implementations for building a clean, modular Gaussian Splat viewer in `src/vibephysics/setup/gsplat.py`.
