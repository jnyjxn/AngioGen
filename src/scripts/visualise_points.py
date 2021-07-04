import argparse
import numpy as np
import open3d as o3d

parser = argparse.ArgumentParser(description='Visualise the generated points.')
parser.add_argument('npz_file', type=str, help='Path to the points.npz file you want to visualise.')
parser.add_argument('--unpack_bits', action="store_true", help='Use this flag if the occupancies are not packed into bits.')
args = parser.parse_args()

data = np.load(args.npz_file)
points = data['points'].astype(np.float32)

occupancies = data['occupancies']
if args.unpack_bits:
        occupancies = np.unpackbits(occupancies)[:points.shape[0]]
occupancies = occupancies.astype(np.uint8)

colors = np.zeros((occupancies.shape[0], 3))
colors[occupancies == 0] = np.array([0, 0, 255])
colors[occupancies == 1] = np.array([255, 0, 255])

pcd = o3d.geometry.PointCloud()
pcd.points = o3d.utility.Vector3dVector(points)
pcd.colors = o3d.utility.Vector3dVector(colors)
o3d.visualization.draw_geometries_with_editing([pcd])