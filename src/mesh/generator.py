import io
from pathlib import Path
from multiprocessing import Pool
from contextlib import redirect_stdout, redirect_stderr

from src.mesh.lib.MeshBuilder import MeshBuilder

def generate_meshes(cfg, overwrite=False):
	root_dir = cfg.get_config("output/root_directory")
	root_dir = Path(root_dir)

	seed_start, seed_end = cfg.get_config("meta/random_seeds/start"), cfg.get_config("meta/random_seeds/end")
	seeds = range(seed_start, seed_end + 1)

	mesh_resolution = cfg.get_config("patient/blood_vessels/mesh/resolution")
	num_processes = cfg.get_config("meta/num_cpus")

	with Pool(num_processes) as p:
		results = p.starmap(generate_one_mesh, [(root_dir, seed, 0.8) for seed in seeds])

	print(results)

def generate_one_mesh(path, i, mesh_resolution):
	stdout = io.StringIO()
	with redirect_stdout(stdout), redirect_stderr(stdout):
		builder = MeshBuilder(path, i, mesh_resolution)
		obj = builder.get_one_mesh_obj()
		builder.save_one_mesh(obj)
