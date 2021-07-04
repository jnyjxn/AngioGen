import argparse
import numpy as np
import open3d as o3d

parser = argparse.ArgumentParser(description='Visualise the generated pointcloud.')
parser.add_argument('npy_file', type=str, help='Path to the pointcloud.npy file you want to visualise.')
args = parser.parse_args()

p = np.load(args.npy_file)

print(p.shape)

pcd = o3d.geometry.PointCloud()
pcd.points = o3d.utility.Vector3dVector(p)
pcd.paint_uniform_color([0, 0, 0])
o3d.visualization.draw_geometries_with_editing([pcd])