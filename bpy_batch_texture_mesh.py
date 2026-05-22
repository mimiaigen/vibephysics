import bpy
import argparse
import os
import sys
from pathlib import Path
try:
    from tqdm import tqdm
except ImportError:
    # Fallback if tqdm is not installed
    def tqdm(iterable, **kwargs):
        return iterable

def clean_scene():
    """Clear all data from the scene to ensure a clean slate for each import."""
    # Reset to factory settings (empty scene)
    try:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    except Exception:
        # Fallback for environments where read_factory_settings might behave differently
        for block_type in [bpy.data.meshes, bpy.data.materials, bpy.data.textures, bpy.data.images, bpy.data.objects, bpy.data.collections]:
            for block in block_type:
                block_type.remove(block)

def convert_glb_textures_to_jpg(input_path, quality=100):
    """
    Imports a GLB, converts all its textures to JPEG format using Blender's 
    glTF exporter, and replaces the original file.
    """
    input_path = Path(input_path).resolve()
    if not input_path.exists():
        print(f"❌ Error: {input_path} does not exist.")
        return False

    original_size = input_path.stat().st_size
    
    # 1. Clear the scene
    clean_scene()
    
    # 2. Import the GLB
    try:
        # We use str(input_path) for compatibility with older bpy versions
        bpy.ops.import_scene.gltf(filepath=str(input_path))
    except Exception as e:
        print(f"❌ Failed to import {input_path.name}: {e}")
        return False

    # 3. Export back to GLB with JPEG conversion
    # We export to a temporary file first to ensure success before replacing the original
    temp_output = input_path.with_suffix(".tmp.glb")
    
    try:
        # Ensure the glTF addon is enabled
        if "io_scene_gltf2" not in bpy.context.preferences.addons:
            try:
                bpy.ops.preferences.addon_enable(module="io_scene_gltf2")
            except:
                pass 

        # Export settings:
        # We target maximum compatibility for Unreal Engine / Game Engines.
        # In bpy 5.0+, parameter names often lose the 'export_' prefix or change.
        # We will use a dictionary of common fallback names.
        
        export_params = {
            "filepath": str(temp_output),
            "export_format": 'GLB',
            "export_image_format": 'JPEG',
            "export_jpeg_quality": quality,
            "export_materials": 'EXPORT',
            "export_animations": True,
            "export_skins": True,
            "export_morph": True,
        }

        # Attempt export with standard keywords
        try:
            bpy.ops.export_scene.gltf(**export_params)
        except TypeError as e:
            err_msg = str(e)
            print(f"⚠️ Export failed with current params: {err_msg}")
            
            # Identify the offending keyword if possible and retry
            # Common changes in 4.x/5.x involve names like 'use_selection', etc.
            # For now, let's try the most "barebones" version that should work on any 4.x+
            minimal_params = {
                "filepath": str(temp_output),
                "export_format": 'GLB',
                "export_image_format": 'JPEG',
                "export_jpeg_quality": quality
            }
            print("🔄 Retrying with minimal parameters...")
            bpy.ops.export_scene.gltf(**minimal_params)


        
        # 4. Replace original with the new version
        if temp_output.exists():
            new_size = temp_output.stat().st_size
            os.replace(temp_output, input_path)
            reduction = (1 - new_size / original_size) * 100 if original_size > 0 else 0
            print(f"✅ {input_path.name}: {original_size/1024/1024:.2f}MB -> {new_size/1024/1024:.2f}MB ({reduction:.1f}% reduction)")
            return True
        else:
            print(f"❌ Export failed: Temporary file was not created for {input_path.name}")
            return False
            
    except Exception as e:
        print(f"❌ Error during export of {input_path.name}: {e}")
        if temp_output.exists():
            os.remove(temp_output)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Batch convert GLB textures to JPEG using Blender's Python API."
    )
    parser.add_argument(
        "input", 
        help="Path to a single .glb file or a folder containing multiple .glb files"
    )
    parser.add_argument(
        "--quality", 
        type=int, 
        default=100, 
        help="JPEG quality (0-100), default: 90"
    )
    
    # Handle arguments when running via 'blender -P script.py -- args'
    if "--" in sys.argv:
        argv = sys.argv[sys.argv.index("--") + 1:]
    else:
        argv = sys.argv[1:]
        
    args = parser.parse_args(argv)
    
    target_path = Path(args.input)
    
    if not target_path.exists():
        print(f"❌ Error: Input path '{target_path}' not found.")
        sys.exit(1)
        
    # Collect GLB files
    if target_path.is_file():
        if target_path.suffix.lower() == ".glb":
            files_to_process = [target_path]
        else:
            print(f"❌ Error: '{target_path}' is not a .glb file.")
            sys.exit(1)
    else:
        files_to_process = list(target_path.glob("*.glb"))
        if not files_to_process:
            print(f"❓ No .glb files found in directory '{target_path}'")
            return

    print(f"🚀 Found {len(files_to_process)} GLB file(s). Starting conversion...")
    
    successes = 0
    for glb_file in tqdm(files_to_process, desc="Converting"):
        if convert_glb_textures_to_jpg(glb_file, quality=args.quality):
            successes += 1
            
    print(f"\n✨ Process complete! {successes}/{len(files_to_process)} files updated.")

if __name__ == "__main__":
    main()
