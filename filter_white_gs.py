import argparse
import os
import numpy as np
from plyfile import PlyData, PlyElement

def filter_white_gaussians(input_path, threshold=0.9):
    print(f"Loading {input_path}...")
    plydata = PlyData.read(input_path)
    
    # 3DGS colors are typically stored in f_dc_0, f_dc_1, f_dc_2
    # SH_C0 = 0.28209479177387814
    # RGB = SH_C0 * f_dc + 0.5
    
    SH_C0 = 0.28209479177387814
    
    vertex = plydata['vertex']
    
    # Check if required attributes exist
    has_dc = all(name in vertex.data.dtype.names for name in ['f_dc_0', 'f_dc_1', 'f_dc_2'])
    
    if not has_dc:
        print("Error: Input PLY does not appear to be a standard Gaussian Splat (missing f_dc_0, f_dc_1, f_dc_2)")
        return
    
    f_dc_0 = vertex.data['f_dc_0']
    f_dc_1 = vertex.data['f_dc_1']
    f_dc_2 = vertex.data['f_dc_2']
    
    # Calculate RGB
    r = SH_C0 * f_dc_0 + 0.5
    g = SH_C0 * f_dc_1 + 0.5
    b = SH_C0 * f_dc_2 + 0.5
    
    # Filter condition: Splat is "white" if R, G, and B are all above threshold
    # We want to KEEP splats that are NOT white
    is_white = (r > threshold) & (g > threshold) & (b > threshold)
    keep_mask = ~is_white
    
    num_original = len(vertex.data)
    num_filtered = np.sum(keep_mask)
    
    print(f"Original points: {num_original}")
    print(f"Filtered points: {num_filtered} (Removed {num_original - num_filtered} white points)")
    
    # Create new vertex data with filtered points
    filtered_vertex_data = vertex.data[keep_mask].copy()
    
    # Calculate average center and offset
    x_mean = np.mean(filtered_vertex_data['x'])
    y_mean = np.mean(filtered_vertex_data['y'])
    z_mean = np.mean(filtered_vertex_data['z'])
    
    print(f"Original center: ({x_mean:.4f}, {y_mean:.4f}, {z_mean:.4f})")
    print("Centering and rotating point cloud (-y -> +z)...")
    
    # 1. Center at origin first
    x_centered = filtered_vertex_data['x'] - x_mean
    y_centered = filtered_vertex_data['y'] - y_mean
    z_centered = filtered_vertex_data['z'] - z_mean
    
    # 2. Apply rotation: -y -> +z (which is a -90 deg rotation around X)
    # New X = old X
    # New Y = old Z
    # New Z = -old Y
    filtered_vertex_data['x'] = x_centered
    filtered_vertex_data['y'] = z_centered
    filtered_vertex_data['z'] = -y_centered
    
    # 3. Rotate Quaternions (rot_0, rot_1, rot_2, rot_3 is typically w, x, y, z)
    # Rotation q_g = (cos(-45), sin(-45), 0, 0) = (0.7071, -0.7071, 0, 0)
    # q_new = q_g * q_old
    if all(name in filtered_vertex_data.dtype.names for name in ['rot_0', 'rot_1', 'rot_2', 'rot_3']):
        r0 = filtered_vertex_data['rot_0']
        r1 = filtered_vertex_data['rot_1']
        r2 = filtered_vertex_data['rot_2']
        r3 = filtered_vertex_data['rot_3']
        
        sq2 = 0.70710678118
        # Multiplication q_g * q_old:
        # w' = wg*w - xg*x
        # x' = wg*x + xg*w
        # y' = wg*y - xg*z
        # z' = wg*z + xg*y
        filtered_vertex_data['rot_0'] = sq2 * (r0 + r1)
        filtered_vertex_data['rot_1'] = sq2 * (r1 - r0)
        filtered_vertex_data['rot_2'] = sq2 * (r2 + r3)
        filtered_vertex_data['rot_3'] = sq2 * (r3 - r2)
        print("Rotated Gaussian splat orientations.")

    # Create new PlyData
    new_vertex_element = PlyElement.describe(filtered_vertex_data, 'vertex')
    new_plydata = PlyData([new_vertex_element], text=plydata.text)
    
    # Determine output path
    base, ext = os.path.splitext(input_path)
    output_path = f"{base}_filtered{ext}"
    
    print(f"Saving to {output_path}...")
    new_plydata.write(output_path)
    print("Done!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Filter out white Gaussian splats from a PLY file.")
    parser.add_argument("input", help="Path to the input .ply file")
    parser.add_argument("-t", "--threshold", type=float, default=0.8, 
                        help="Threshold for whiteness (0.0 to 1.0). Splats with R, G, B > threshold are removed. Default: 0.9")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: File {args.input} does not exist.")
    else:
        filter_white_gaussians(args.input, args.threshold)
