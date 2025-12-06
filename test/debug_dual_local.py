"""
Test script: Dual Local View
Left Viewport: Local View (Cube)
Right Viewport: Local View (Sphere)
"""
import bpy

def test_dual_local_view():
    print("\n" + "="*50)
    print("DUAL LOCAL VIEW TEST")
    print("="*50)
    
    # Clear scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # Create Cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(-2, 0, 0))
    cube = bpy.context.active_object
    cube.name = "Left_Cube"
    mat1 = bpy.data.materials.new(name="Red")
    mat1.diffuse_color = (1, 0, 0, 1)
    cube.data.materials.append(mat1)
    
    # Create Sphere
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(2, 0, 0))
    sphere = bpy.context.active_object
    sphere.name = "Right_Sphere"
    mat2 = bpy.data.materials.new(name="Green")
    mat2.diffuse_color = (0, 1, 0, 1)
    sphere.data.materials.append(mat2)
    
    # Split viewport
    screen = bpy.context.screen
    view3d_areas = sorted([a for a in screen.areas if a.type == 'VIEW_3D'], key=lambda a: a.x)
    
    if len(view3d_areas) < 2:
        area = view3d_areas[0]
        with bpy.context.temp_override(area=area, region=area.regions[0]):
            bpy.ops.screen.area_split(direction='VERTICAL', factor=0.5)
        view3d_areas = sorted([a for a in screen.areas if a.type == 'VIEW_3D'], key=lambda a: a.x)
    
    left_area = view3d_areas[0]
    right_area = view3d_areas[1]
    
    # Setup Left Viewport (Cube Only)
    print("Setting up Left Viewport (Cube)...")
    bpy.ops.object.select_all(action='DESELECT')
    cube.select_set(True)
    bpy.context.view_layer.objects.active = cube
    
    # Check if already in local view
    left_space = left_area.spaces[0]
    if left_space.local_view:
        with bpy.context.temp_override(area=left_area, region=left_area.regions[-1], space_data=left_space):
             bpy.ops.view3d.localview() # Exit
    
    with bpy.context.temp_override(area=left_area, region=left_area.regions[-1], space_data=left_space):
        bpy.ops.view3d.localview() # Enter
        bpy.ops.view3d.view_all()
    
    # Setup Right Viewport (Sphere Only)
    print("Setting up Right Viewport (Sphere)...")
    bpy.ops.object.select_all(action='DESELECT')
    sphere.select_set(True)
    bpy.context.view_layer.objects.active = sphere
    
    right_space = right_area.spaces[0]
    if right_space.local_view:
        with bpy.context.temp_override(area=right_area, region=right_area.regions[-1], space_data=right_space):
             bpy.ops.view3d.localview() # Exit
             
    with bpy.context.temp_override(area=right_area, region=right_area.regions[-1], space_data=right_space):
        bpy.ops.view3d.localview() # Enter
        bpy.ops.view3d.view_all()
        
    print("✅ Done! Check viewports.")
    print("Left: Red Cube Only | Right: Green Sphere Only")

if __name__ == "__main__":
    test_dual_local_view()
