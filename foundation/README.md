# Physics Implementation Guide

This document bridges the gap between real-world physics concepts and their implementation within the VibePhysics framework.

## Physics to Function Mapping

| Real Physics Concept | Equation / Principle | VibePhysics Function / Method | Implementation Details |
|----------------------|---------------------|-------------------------------|------------------------|
| **Newtonian Mechanics** | $F = ma$ (Second Law)<br>$F_g = mg$ (Gravity) | `physics.setup_rigid_body_world()` | **Engine:** Bullet Physics<br>**Config:** High substeps (60) to prevent tunneling of light objects ($0.001\text{kg}$). |
| **Buoyancy** | $F_b = \rho V g$ (Archimedes) | `physics.create_buoyancy_field()` | **Method:** Wind Force Field (+Z)<br>**Hack:** Constant upward force below $Z=0$ instead of exact volume calculation.<br>**Limit:** Bounded by `distance_max` at surface. |
| **Hydrodynamic Drag** | $F_d = -\frac{1}{2} \rho v^2 C_d A$ | `physics.create_floating_sphere()` | **Method:** Adaptive Damping Driver<br>**Logic:** Python driver switches damping dynamically:<br>`damping = 0.99` if $Z < 0.5$ (Water)<br>`damping = 0.01` if $Z \ge 0.5$ (Air) |
| **Turbulence** | Turbulent Flow (Chaotic) | `physics.create_underwater_currents()` | **Method:** Turbulence Force Field<br>**Math:** 3D Perlin Noise / Gradient Noise to generate random force vectors (Brownian motion). |
| **Wave Mechanics** (Ambient) | Spectral Synthesis (FFT) | `visuals.create_visual_water()` | **Method:** Ocean Modifier<br>**Tech:** Fourier Transform based surface displacement for realistic deep ocean swells. |
| **Wave Mechanics** (Ripples) | $\frac{\partial^2 u}{\partial t^2} = c^2 \nabla^2 u$ | `visuals.setup_dynamic_paint_interaction()` | **Method:** Dynamic Paint (Wave Surface)<br>**Tech:** Solves 2D Wave Equation on vertex grid.<br>**Coupling:** One-way (Objects $\to$ Waves). |

## Detailed Explanations

### 1. Newtonian Mechanics & Rigid Bodies
We run the simulation at **60 physics steps per frame** (standard is often 10). This is critical for light objects ($0.001\text{kg}$) which accelerate extremely fast. Low substeps would cause them to "tunnel" through collisions or explode due to numerical instability.

### 2. Buoyancy (Archimedes' Principle)
Real buoyancy depends on the *exact volume* submerged ($V$). Our implementation approximates this using a global upward **Wind Force Field**. The field is strictly bounded to stop exactly at the water surface ($Z=0$), creating a "zone" of lift rather than calculating mesh displacement per object.

### 3. Hydrodynamic Drag (Fluid Resistance)
Blender's Rigid Body system has a single global `damping` value. This is insufficient for water entry/exit. We use a **Python Driver** to "hit" objects with high resistance the moment they enter the water, creating realistic splash-down deceleration.

### 4. Wave Mechanics (Hybrid)
*   **Ambient Waves:** Good for infinite oceans and storm swells (visual only).
*   **Interactive Ripples:** Objects act as "Brushes" on a "Canvas" that solves the wave equation. This creates the wake and ripples, but does not exert force back on the objects.
