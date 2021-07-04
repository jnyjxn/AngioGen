import numpy as np
from pathlib import Path
from multiprocessing import Pool
import multiprocessing.pool as mpp


try:
	from src.three_d.lib.MeshBuilder import MeshBuilder
except ImportError:
	"""
	It means we are not running in Blender mode and hence don't need
	this module
	"""


try:
	from .lib.MeshSampler import MeshSampler
	from utils.PoolIStarMap import istarmap
except ImportError:
	"""
	It means we are running in Blender mode and hence don't need
	this module
	"""

def generate_meshes(cfg, overwrite=False, debug=False):
	root_dir = cfg.get_config("output/root_directory")
	root_dir = Path(root_dir)

	seed_start, seed_end = cfg.get_config("meta/random_seeds/start"), cfg.get_config("meta/random_seeds/end")
	seeds = range(seed_start, seed_end + 1)
	pad = cfg.get_config("output/pad_zeros_to")

	mesh_resolution = cfg.get_config("patient/blood_vessels/mesh/resolution")
	num_processes = cfg.get_config("meta/num_cpus")

	with Pool(num_processes) as p:
		results = p.starmap(generate_one_mesh, [(root_dir, f"{seed:0{pad}}", 0.8, overwrite) for seed in seeds])

def generate_one_mesh(path, mesh_id, mesh_resolution, overwrite=False):
	if not overwrite:
		mesh_path = Path(path / mesh_id / "mesh.ply")
		if mesh_path.exists():
			print("Export completed")
			return


	print("Building")

	builder = MeshBuilder(path, mesh_id, mesh_resolution)
	obj = builder.get_one_mesh_obj()
	builder.save_one_mesh(obj)


def generate_samplesets(cfg, overwrite=False, debug=False):
	root_dir = cfg.get_config("output/root_directory")
	root_dir = Path(root_dir)

	get_points = cfg.get_config("output/save/points")
	get_pointcloud = cfg.get_config("output/save/pointcloud")
	get_voxels = cfg.get_config("output/save/voxels")

	points_size = cfg.get_config("patient/blood_vessels/points/number")
	points_uniform_ratio = cfg.get_config("patient/blood_vessels/points/uniform_ratio")
	pointcloud_size = cfg.get_config("patient/blood_vessels/pointcloud/number")
	voxels_res = cfg.get_config("patient/blood_vessels/voxels/resolution")

	resize = cfg.get_config("patient/blood_vessels/normalise")

	num_processes = cfg.get_config("meta/num_cpus")
	mpp.Pool.istarmap = istarmap

	from tqdm import tqdm

	with Pool(num_processes) as p:
		iterable = [(item.parents[0], get_points, get_pointcloud, get_voxels, points_size, points_uniform_ratio, pointcloud_size, voxels_res, resize, overwrite) for item in root_dir.rglob("**/*.ply")]
		for _ in tqdm(p.istarmap(generate_one_sampleset, iterable),
						   total=len(iterable)):
			pass

def generate_one_sampleset(path, get_points, get_pointcloud, get_voxels, points_size, points_uniform_ratio, pointcloud_size, voxels_res, resize, overwrite=False):
	MeshSampler.sample(
		path, 
		get_points=get_points, 
		get_pointcloud=get_pointcloud, 
		get_voxels=get_voxels,
		points_size=points_size, 
		points_uniform_ratio=points_uniform_ratio,
		pointcloud_size=pointcloud_size,
		voxels_res=voxels_res,
		resize=resize,
		overwrite=overwrite
	)