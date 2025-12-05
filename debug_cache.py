import bpy
import os

print("\n--- DEBUG CACHE SETTINGS ---")

# 1. Rigid Body World
if bpy.context.scene.rigidbody_world and bpy.context.scene.rigidbody_world.point_cache:
    print(f"Rigid Body World Disk Cache: {bpy.context.scene.rigidbody_world.point_cache.use_disk_cache}")
else:
    print("Rigid Body World: None")

# 2. Dynamic Paint
for obj in bpy.data.objects:
    for mod in obj.modifiers:
        if mod.type == 'DYNAMIC_PAINT' and mod.ui_type == 'CANVAS':
            if mod.canvas_settings:
                for surface in mod.canvas_settings.canvas_surfaces:
                    if surface.point_cache:
                        print(f"Dynamic Paint '{obj.name}' Surface '{surface.name}' Disk Cache: {surface.point_cache.use_disk_cache}")

print("----------------------------\n")
