import bpy
import colorsys

def create_seabed_material(obj):
    """Creates a dirt/ground material for the seabed"""
    mat = bpy.data.materials.new(name="SeabedMat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    
    # Dark brown/dirt color
    bsdf.inputs['Base Color'].default_value = (0.15, 0.1, 0.05, 1)
    bsdf.inputs['Roughness'].default_value = 0.9
    
    # Handle different Blender versions for Specular
    if 'Specular' in bsdf.inputs:
        bsdf.inputs['Specular'].default_value = 0.1
    elif 'Specular IOR Level' in bsdf.inputs: # Blender 4.0+
        bsdf.inputs['Specular IOR Level'].default_value = 0.1
    
    obj.data.materials.append(mat)

def create_sphere_material(sphere, index, count):
    """Visual Material only (Non-Physics)"""
    mat = bpy.data.materials.new(name=f"SphereMat_{index}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    
    hue = (index / count) * 0.8
    rgb = colorsys.hsv_to_rgb(hue, 0.9, 0.9)
    
    bsdf.inputs['Base Color'].default_value = (rgb[0], rgb[1], rgb[2], 1)
    bsdf.inputs['Metallic'].default_value = 0.2
    bsdf.inputs['Roughness'].default_value = 0.3
    sphere.data.materials.append(mat)

def create_water_material(water_obj, color=(0.0, 0.6, 1.0, 1.0)):
    """
    Visual Material with Transparent Shadows hack.
    Allows the 'Fake Caustic' light to pass through the surface without being blocked.
    Includes EEVEE/Viewport transparency fixes.
    """
    mat = bpy.data.materials.new(name="OceanMat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    # Nodes
    node_out = nodes.new(type='ShaderNodeOutputMaterial')
    node_mix_shadow = nodes.new(type='ShaderNodeMixShader')
    node_mix_surface = nodes.new(type='ShaderNodeMixShader') # For Viewport transparency mix
    
    node_transparent = nodes.new(type='ShaderNodeBsdfTransparent')
    node_principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    node_lightpath = nodes.new(type='ShaderNodeLightPath')
    
    # Principled Settings (The Visible Water)
    # Use user-defined color
    node_principled.inputs['Base Color'].default_value = color
    node_principled.inputs['Roughness'].default_value = 0.02 # Very smooth/shiny
    node_principled.inputs['IOR'].default_value = 1.333
    
    # Handle Transmission inputs for different Blender versions
    if 'Transmission' in node_principled.inputs:
        node_principled.inputs['Transmission'].default_value = 1.0
    elif 'Transmission Weight' in node_principled.inputs:
        node_principled.inputs['Transmission Weight'].default_value = 1.0
    
    # --- SHADING LOGIC ---
    # 1. Shadow Ray Trick: If Shadow Ray, use Transparent BSDF (invisible shadows).
    # 2. Viewport Trick: If Camera Ray, use a mix of Transmission and pure Transparency 
    #    to ensure "see-through" even if Eevee Refraction fails or is off.
    
    # Mix 1: Surface Appearance (Transmission vs Transparency)
    # Mixing in 10% pure transparency guarantees some visibility even if refraction is opaque.
    # Adjust Factor: 0.0 = Fully Principled (Refractive), 1.0 = Fully Transparent (Invisible)
    # We use 0.2 to add a bit of "ghost" transparency to help Viewport.
    links.new(node_principled.outputs['BSDF'], node_mix_surface.inputs[1])
    
    # IMPORTANT: For the ghost transparency to carry color, we should actually 
    # mix with a Translucent or Glass, but Transparent BSDF is white (clear).
    # If we want tint, the Principled BSDF (Transmission) does the tinting.
    # The Transparent Node is purely for the "Hole" in the opacity.
    links.new(node_transparent.outputs['BSDF'], node_mix_surface.inputs[2])
    
    # Use a lighter mix (0.15) so it's mostly the colored water (85%) 
    # but with a 15% fail-safe hole for viewport visibility.
    node_mix_surface.inputs['Fac'].default_value = 0.15 
    
    # Mix 2: Shadow Trick
    # If Is Shadow Ray -> Transparent (Factor 1)
    # Else -> Surface Mix (Factor 0)
    links.new(node_lightpath.outputs['Is Shadow Ray'], node_mix_shadow.inputs['Fac'])
    links.new(node_mix_surface.outputs['Shader'], node_mix_shadow.inputs[1])
    links.new(node_transparent.outputs['BSDF'], node_mix_shadow.inputs[2])
    
    links.new(node_mix_shadow.outputs['Shader'], node_out.inputs['Surface'])
         
    water_obj.data.materials.append(mat)
    
    # VIEWPORT REALISM SETTINGS (EEVEE / Material Preview)
    # Essential for seeing transparency in the viewport
    
    # Blender 4.2+ Handling for Material Transparency
    try:
        # 4.2+ might use 'surface_render_method' instead of blend_method?
        # Actually 'blend_method' usually persists but for Eevee Next it might be different.
        mat.blend_method = 'BLEND'    # Alpha Blend
    except:
        pass

    try:
        mat.shadow_method = 'NONE'
    except:
        pass
        
    try:
        mat.use_screen_refraction = True
    except:
        pass
        
    # Extra safety: Set Alpha < 1.0 on Principled?
    # No, Transmission 1.0 is better, but the Mix Shader above handles the fallback.
    
    mat.use_backface_culling = False
