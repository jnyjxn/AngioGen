import pyrender
import numpy as np
from pathlib import Path
from copy import deepcopy

from .Renderer import Renderer
from utils import get_image_operations

class ImageBuilder(object):
	@classmethod
	def generate_one_imageset(cls, cfg, seed):
		root_dir = cfg.get_config("output/root_directory")
		root_dir = Path(root_dir)

		image_operations = get_image_operations(cfg)
		mesh_filepath = root_dir / f"{seed:04}" / "mesh.npz"
		mesh = cls.load_mesh(mesh_filepath)

		image_cfg = cfg.generate(seed=seed)
		renderer = Renderer(image_cfg)
		raw_images, raw_depths, raw_matrices = renderer.generate_data(mesh)

		processed_images = cls.process_images(raw_images, raw_depths, raw_matrices, image_operations)
		out_dir = root_dir / f"{seed:04}" / "images"

		for imageset_name, imageset_data in processed_images.items():
			imageset_images, imageset_depths, imageset_matrices = imageset_data

			save_to = out_dir / imageset_name
			save_to.mkdir(parents=True, exist_ok=True)

			np.save(save_to / "images.npy", imageset_images)
			np.save(save_to / "depths.npy", imageset_depths)
			np.savez_compressed(save_to / "matrices.npz", **imageset_matrices)

		return True

	@staticmethod
	def load_mesh(path):
		dat = np.load(path)

		verts = dat["verts"]
		faces = dat["faces"]

		return pyrender.Mesh([pyrender.Primitive(positions=verts, indices=faces)])

	@staticmethod
	def process_images(images, depths, matrices, process_groups_cfg):
		processed_images = {}
		for process_group_name, process_group_ops in process_groups_cfg.items():
			processed_data = (
				deepcopy(images),
				deepcopy(depths),
				deepcopy(matrices)
			)

			funcs, cfgs = process_group_ops
			while funcs:
				func = funcs.pop(0)
				cfg = cfgs.pop(0)

				processed_data = func(*processed_data, **cfg)

			processed_images[process_group_name] = processed_data

		return processed_images