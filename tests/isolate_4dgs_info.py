#!/usr/bin/env python3
"""
Isolate 4DGS PLY Info Reader

Reads Gaussian Splatting PLY files and extracts attribute information.
Works with both 3DGS and 4DGS formats.

Usage:
    python isolate_4dgs_info.py <path_to_ply>
    python isolate_4dgs_info.py /path/to/gaussian_splat.ply

Attributes in Gaussian Splatting PLY files:
- x, y, z: Position
- nx, ny, nz: Normal (optional)
- f_dc_0, f_dc_1, f_dc_2: Spherical harmonics (color, degree 0)
- f_rest_*: Higher order spherical harmonics (optional)
- opacity: Opacity value (logit space)
- scale_0, scale_1, scale_2: Log-scale values
- rot_0, rot_1, rot_2, rot_3: Rotation quaternion
"""

import sys
import os
import struct
from typing import Dict, List, Tuple, Any, Optional
import numpy as np

# Try to import plyfile, fall back to manual parsing
try:
    from plyfile import PlyData, PlyElement
    HAS_PLYFILE = True
except ImportError:
    HAS_PLYFILE = False
    print("Note: plyfile not installed. Using manual PLY parser.")
    print("Install with: pip install plyfile")


# =============================================================================
# Manual PLY Parser (fallback when plyfile not available)
# =============================================================================

def parse_ply_header(filepath: str) -> Tuple[Dict[str, Any], int]:
    """
    Parse PLY header and return element info and data offset.
    
    Returns:
        Tuple of (header_info, data_offset)
        header_info: {
            'format': 'ascii' | 'binary_little_endian' | 'binary_big_endian',
            'elements': [{'name': str, 'count': int, 'properties': [...]}],
        }
    """
    header_info = {
        'format': None,
        'elements': []
    }
    current_element = None
    
    with open(filepath, 'rb') as f:
        while True:
            line = f.readline().decode('utf-8').strip()
            
            if line == 'end_header':
                data_offset = f.tell()
                break
            
            parts = line.split()
            
            if parts[0] == 'ply':
                continue
            elif parts[0] == 'format':
                header_info['format'] = parts[1]
            elif parts[0] == 'element':
                if current_element:
                    header_info['elements'].append(current_element)
                current_element = {
                    'name': parts[1],
                    'count': int(parts[2]),
                    'properties': []
                }
            elif parts[0] == 'property':
                if current_element:
                    prop_type = parts[1]
                    prop_name = parts[-1]
                    current_element['properties'].append({
                        'type': prop_type,
                        'name': prop_name
                    })
            elif parts[0] == 'comment':
                continue
    
    if current_element:
        header_info['elements'].append(current_element)
    
    return header_info, data_offset


def get_numpy_dtype(ply_type: str) -> np.dtype:
    """Convert PLY type to numpy dtype."""
    type_map = {
        'float': np.float32,
        'float32': np.float32,
        'double': np.float64,
        'float64': np.float64,
        'int': np.int32,
        'int32': np.int32,
        'uint': np.uint32,
        'uint32': np.uint32,
        'short': np.int16,
        'int16': np.int16,
        'ushort': np.uint16,
        'uint16': np.uint16,
        'char': np.int8,
        'int8': np.int8,
        'uchar': np.uint8,
        'uint8': np.uint8,
    }
    return type_map.get(ply_type, np.float32)


def read_ply_data_binary(filepath: str, header_info: Dict, data_offset: int) -> Dict[str, np.ndarray]:
    """Read binary PLY data."""
    data = {}
    
    for element in header_info['elements']:
        if element['name'] != 'vertex':
            continue
        
        # Build dtype for this element
        dtype_list = []
        for prop in element['properties']:
            dtype_list.append((prop['name'], get_numpy_dtype(prop['type'])))
        
        dtype = np.dtype(dtype_list)
        
        with open(filepath, 'rb') as f:
            f.seek(data_offset)
            vertex_data = np.frombuffer(f.read(element['count'] * dtype.itemsize), dtype=dtype)
        
        # Extract each property
        for prop in element['properties']:
            data[prop['name']] = vertex_data[prop['name']]
    
    return data


def read_ply_manual(filepath: str) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
    """
    Read PLY file without plyfile library.
    
    Returns:
        Tuple of (data_dict, info_dict)
    """
    header_info, data_offset = parse_ply_header(filepath)
    
    if header_info['format'] == 'ascii':
        raise NotImplementedError("ASCII PLY format not supported in manual parser. Install plyfile.")
    
    data = read_ply_data_binary(filepath, header_info, data_offset)
    
    info = {
        'format': header_info['format'],
        'elements': header_info['elements']
    }
    
    return data, info


# =============================================================================
# PLY Info Extraction
# =============================================================================

def read_ply_info(filepath: str) -> Dict[str, Any]:
    """
    Read PLY file and extract all attribute information.
    
    Args:
        filepath: Path to PLY file
    
    Returns:
        Dictionary with PLY info:
        {
            'filepath': str,
            'filesize_mb': float,
            'num_points': int,
            'format': str,
            'attributes': {
                'name': {
                    'dtype': str,
                    'min': float,
                    'max': float,
                    'mean': float,
                    'std': float,
                }
            },
            'is_gaussian_splat': bool,
            'has_sh': bool,
            'sh_degree': int,
            'has_4d': bool,
        }
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"PLY file not found: {filepath}")
    
    info = {
        'filepath': filepath,
        'filename': os.path.basename(filepath),
        'filesize_mb': os.path.getsize(filepath) / (1024 * 1024),
        'num_points': 0,
        'format': None,
        'attributes': {},
        'is_gaussian_splat': False,
        'has_sh': False,
        'sh_degree': 0,
        'has_4d': False,
    }
    
    # Read PLY data
    if HAS_PLYFILE:
        plydata = PlyData.read(filepath)
        vertex = plydata['vertex']
        info['num_points'] = len(vertex)
        info['format'] = str(plydata.header).split('\n')[1].replace('format ', '')
        
        # Extract properties
        for prop in vertex.properties:
            name = prop.name
            data = np.array(vertex[name])
            info['attributes'][name] = {
                'dtype': str(data.dtype),
                'min': float(np.min(data)),
                'max': float(np.max(data)),
                'mean': float(np.mean(data)),
                'std': float(np.std(data)),
            }
    else:
        data, ply_info = read_ply_manual(filepath)
        info['format'] = ply_info['format']
        
        for element in ply_info['elements']:
            if element['name'] == 'vertex':
                info['num_points'] = element['count']
        
        for name, values in data.items():
            info['attributes'][name] = {
                'dtype': str(values.dtype),
                'min': float(np.min(values)),
                'max': float(np.max(values)),
                'mean': float(np.mean(values)),
                'std': float(np.std(values)),
            }
    
    # Check if Gaussian Splat format
    attr_names = set(info['attributes'].keys())
    
    # Required for Gaussian Splat
    gs_required = {'x', 'y', 'z', 'opacity'}
    sh_required = {'f_dc_0', 'f_dc_1', 'f_dc_2'}
    scale_required = {'scale_0', 'scale_1', 'scale_2'}
    rot_required = {'rot_0', 'rot_1', 'rot_2', 'rot_3'}
    
    info['has_position'] = {'x', 'y', 'z'}.issubset(attr_names)
    info['has_opacity'] = 'opacity' in attr_names
    info['has_sh'] = sh_required.issubset(attr_names)
    info['has_scale'] = scale_required.issubset(attr_names)
    info['has_rotation'] = rot_required.issubset(attr_names)
    
    # Check for higher order SH
    sh_attrs = [a for a in attr_names if a.startswith('f_rest_')]
    if sh_attrs:
        # Number of SH coefficients: 3 * (degree+1)^2 - 3 for f_rest
        # f_rest count: 3 * ((degree+1)^2 - 1)
        n_rest = len(sh_attrs)
        # Solve for degree: 3 * ((d+1)^2 - 1) = n_rest
        # (d+1)^2 = n_rest/3 + 1
        import math
        d_plus_1_sq = n_rest / 3 + 1
        d_plus_1 = math.sqrt(d_plus_1_sq)
        info['sh_degree'] = int(d_plus_1) - 1 if d_plus_1 == int(d_plus_1) else 0
    elif info['has_sh']:
        info['sh_degree'] = 0
    
    # Check if Gaussian Splat
    info['is_gaussian_splat'] = (
        info['has_position'] and 
        info['has_sh'] and 
        info['has_scale'] and 
        info['has_rotation']
    )
    
    # Check for 4D Gaussian Splat attributes
    _4d_attrs = {'t_scale', 'motion_0', 'motion_1', 'motion_2'}
    info['has_4d'] = bool(_4d_attrs.intersection(attr_names))
    
    return info


def convert_sh_to_rgb_sample(f_dc_0: float, f_dc_1: float, f_dc_2: float) -> Tuple[float, float, float]:
    """
    Convert spherical harmonics to RGB color.
    
    Formula: RGB = SH_C0 * f_dc + 0.5
    where SH_C0 = 0.28209479177387814
    """
    SH_C0 = 0.28209479177387814
    r = SH_C0 * f_dc_0 + 0.5
    g = SH_C0 * f_dc_1 + 0.5
    b = SH_C0 * f_dc_2 + 0.5
    return (
        max(0.0, min(1.0, r)),
        max(0.0, min(1.0, g)),
        max(0.0, min(1.0, b))
    )


def sigmoid(x: float) -> float:
    """Sigmoid function for opacity conversion."""
    return 1.0 / (1.0 + np.exp(-x))


def print_ply_info(info: Dict[str, Any], verbose: bool = True):
    """Print PLY info in a formatted way."""
    print("\n" + "=" * 60)
    print("  PLY FILE INFORMATION")
    print("=" * 60)
    
    print(f"\n📁 File: {info['filename']}")
    print(f"   Path: {info['filepath']}")
    print(f"   Size: {info['filesize_mb']:.2f} MB")
    print(f"   Format: {info['format']}")
    
    print(f"\n📊 Points: {info['num_points']:,}")
    
    # Type detection
    print("\n🔍 Type Detection:")
    if info['is_gaussian_splat']:
        gs_type = "4D Gaussian Splat" if info['has_4d'] else "3D Gaussian Splat"
        print(f"   ✅ {gs_type}")
        if info['sh_degree'] > 0:
            print(f"   ✅ Spherical Harmonics Degree: {info['sh_degree']}")
        else:
            print(f"   ✅ Spherical Harmonics: DC only (degree 0)")
    else:
        print(f"   ⚠️ Not a standard Gaussian Splat format")
        print(f"   - Has Position: {'✅' if info['has_position'] else '❌'}")
        print(f"   - Has SH (f_dc_*): {'✅' if info['has_sh'] else '❌'}")
        print(f"   - Has Scale: {'✅' if info['has_scale'] else '❌'}")
        print(f"   - Has Rotation: {'✅' if info['has_rotation'] else '❌'}")
        print(f"   - Has Opacity: {'✅' if info['has_opacity'] else '❌'}")
    
    # Attribute summary
    print(f"\n📋 Attributes ({len(info['attributes'])} total):")
    
    # Group attributes by category
    categories = {
        'Position': ['x', 'y', 'z'],
        'Normal': ['nx', 'ny', 'nz'],
        'Color (SH DC)': ['f_dc_0', 'f_dc_1', 'f_dc_2'],
        'Scale': ['scale_0', 'scale_1', 'scale_2'],
        'Rotation': ['rot_0', 'rot_1', 'rot_2', 'rot_3'],
        'Opacity': ['opacity'],
        '4D Motion': ['motion_0', 'motion_1', 'motion_2', 't_scale'],
    }
    
    categorized = set()
    for cat_name, cat_attrs in categories.items():
        present_attrs = [a for a in cat_attrs if a in info['attributes']]
        if present_attrs:
            print(f"\n   {cat_name}:")
            for attr in present_attrs:
                attr_info = info['attributes'][attr]
                print(f"      {attr}: [{attr_info['min']:.4f}, {attr_info['max']:.4f}] "
                      f"(mean: {attr_info['mean']:.4f}, std: {attr_info['std']:.4f})")
                categorized.add(attr)
    
    # Higher order SH
    sh_rest = sorted([a for a in info['attributes'] if a.startswith('f_rest_')])
    if sh_rest:
        print(f"\n   Color (SH Higher Order): {len(sh_rest)} attributes")
        if verbose and len(sh_rest) <= 10:
            for attr in sh_rest:
                attr_info = info['attributes'][attr]
                print(f"      {attr}: [{attr_info['min']:.4f}, {attr_info['max']:.4f}]")
        else:
            print(f"      {sh_rest[0]} ... {sh_rest[-1]}")
        categorized.update(sh_rest)
    
    # Uncategorized
    uncategorized = set(info['attributes'].keys()) - categorized
    if uncategorized:
        print(f"\n   Other Attributes:")
        for attr in sorted(uncategorized):
            attr_info = info['attributes'][attr]
            print(f"      {attr}: [{attr_info['min']:.4f}, {attr_info['max']:.4f}] "
                  f"(dtype: {attr_info['dtype']})")
    
    # Sample color conversion
    if info['has_sh']:
        print("\n🎨 Sample Color Conversion (SH to RGB):")
        f_dc_0_mean = info['attributes']['f_dc_0']['mean']
        f_dc_1_mean = info['attributes']['f_dc_1']['mean']
        f_dc_2_mean = info['attributes']['f_dc_2']['mean']
        r, g, b = convert_sh_to_rgb_sample(f_dc_0_mean, f_dc_1_mean, f_dc_2_mean)
        print(f"   Mean SH: ({f_dc_0_mean:.4f}, {f_dc_1_mean:.4f}, {f_dc_2_mean:.4f})")
        print(f"   → RGB: ({r:.3f}, {g:.3f}, {b:.3f})")
    
    # Opacity info
    if info['has_opacity']:
        print("\n🔍 Opacity Info:")
        opacity_info = info['attributes']['opacity']
        # Opacity is stored in logit space, need sigmoid to get actual value
        mean_opacity = sigmoid(opacity_info['mean'])
        min_opacity = sigmoid(opacity_info['min'])
        max_opacity = sigmoid(opacity_info['max'])
        print(f"   Raw (logit space): [{opacity_info['min']:.4f}, {opacity_info['max']:.4f}]")
        print(f"   After sigmoid: [{min_opacity:.4f}, {max_opacity:.4f}] (mean: {mean_opacity:.4f})")
    
    print("\n" + "=" * 60)


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python isolate_4dgs_info.py <path_to_ply>")
        print("\nExample:")
        print("  python isolate_4dgs_info.py /path/to/gaussian_splat.ply")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    try:
        info = read_ply_info(filepath)
        print_ply_info(info)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading PLY file: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
