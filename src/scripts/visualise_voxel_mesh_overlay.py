import argparse
import numpy as np
import trimesh as tm

parser = argparse.ArgumentParser(description='Visualise the generated voxel grid on top of the mesh.')
parser.add_argument('binvox_file', type=str, help='Path to the model.binvox file you want to visualise.')
parser.add_argument('mesh_file', type=str, help='Path to the (normalised) mesh file you want to visualise.')
args = parser.parse_args()

with open(args.binvox_file, 'rb') as f:
    v = tm.exchange.binvox.load_binvox(f)

colors = np.zeros((*v.shape, 4))
colors[:,:,:,3] = 0.2

v = v.as_boxes(colors=colors)

m = tm.load_mesh(args.mesh_file)

s = tm.scene.Scene(m)
s.add_geometry(v)
print(m.bounds)
print(v.bounds)
s.show()