# Physics Implementation Guide

This document bridges the gap between real-world physics concepts and their implementation within the VibePhysics framework.

## 1. Newtonian Mechanics & Rigid Bodies

### Real Physics Concept
**Newton's Second Law:** $F = ma$
Objects move based on the sum of forces applied to them. Gravity pulls objects down with $F_g = mg$.

### Code Implementation
*   **Location:** `foundation/physics.py` -> `setup_rigid_body_world()`
*   **Engine:** Blender uses the **Bullet Physics** engine.
*   **Key Configuration:**
    *   **Substeps (60):** We run the simulation at 60 physics steps per frame (standard is often 10). This is critical for light objects ($0.001\text{kg}$) which accelerate extremely fast. Low substeps would cause them to "tunnel" through collisions or explode due to numerical instability.

## 2. Buoyancy (Archimedes' Principle)

### Real Physics Concept
**Archimedes' Principle:** $F_b = \rho V g$
An upward buoyant force is exerted on a body immersed in a fluid, equal to the weight of the fluid displaced.

### Code Implementation
*   **Location:** `foundation/physics.py` -> `create_buoyancy_field()`
*   **Method:** We use a **Wind Force Field** pointing in the $+Z$ direction.
*   **Approximation:**
    *   Real buoyancy depends on the *exact volume* submerged ($V$).
    *   **Our Hack:** We apply a constant upward field below $Z=0$. This mimics the effect well enough for floating spheres without the heavy computational cost of calculating mesh boolean intersections every frame.
    *   **Limit:** The field is bounded by `distance_max` to stop exactly at the water surface ($Z=0$).

## 3. Hydrodynamic Drag (Fluid Resistance)

### Real Physics Concept
**Drag Equation:** $F_d = -\frac{1}{2} \rho v^2 C_d A$
Objects encounter significantly more resistance moving through water than through air. This "damping" force opposes motion.

### Code Implementation
*   **Location:** `foundation/physics.py` -> `create_floating_sphere()` -> *Adaptive Damping Driver*
*   **Method:** Blender's Rigid Body system has a single global `damping` value. This is insufficient for water entry/exit.
*   **Solution:** We use a **Python Driver** (a per-frame script) on the object's damping property:
    ```python
    damping = WATER_DAMPING if z < 0.5 else AIR_DAMPING
    ```
*   **Result:** Objects "hit a wall" of resistance when they splash down, preventing them from sinking endlessly like they are in a vacuum.

## 4. Turbulence & Currents

### Real Physics Concept
**Turbulent Flow:** Chaotic changes in pressure and flow velocity. In the ocean, this manifests as complex currents that push objects unpredictably.

### Code Implementation
*   **Location:** `foundation/physics.py` -> `create_underwater_currents()`
*   **Method:** **Turbulence Force Field**.
*   **Math:** Uses 3D Perlin Noise (or similar gradient noise) to generate randomized force vectors in space.
*   **Effect:** Adds "Brownian motion" to objects, making them drift and rotate naturally rather than sitting perfectly still.

## 5. Wave Mechanics

### Real Physics Concept
**Wave Equation:** $\frac{\partial^2 u}{\partial t^2} = c^2 \nabla^2 u$
Disturbances propagate through a medium.

### Code Implementation
We use a hybrid approach in `foundation/visuals.py`:

1.  **Ambient Waves (Ocean Modifier):**
    *   Uses **Fourier Transform (FFT)** spectral synthesis to generate realistic, non-interactive ocean surface displacements.
    *   Good for: Infinite oceans, storm swells.

2.  **Interactive Ripples (Dynamic Paint):**
    *   **Method:** Solves a 2D Wave Equation on the mesh vertex grid.
    *   **Canvas:** The water surface mesh.
    *   **Brush:** The floating objects.
    *   **Coupling:** This is *One-Way Coupling*. Objects create waves (visual), but these specific ripple waves do not exert force back on the objects (physics). The Buoyancy Field handles the lifting force.
