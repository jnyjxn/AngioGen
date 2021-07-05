import trimesh
import pyrender
import numpy as np
from PIL import Image
from pathlib import Path
from copy import deepcopy

from .Renderer import OpticalRenderer, XRayRenderer
from utils import get_image_operations


def save_np_to_pfm(np_array,filepath):
	np_array = np_array.astype(np.float32)

	color = None

	if np_array.dtype.name != 'float32':
		raise Exception('Image dtype must be float32.')

	if len(np_array.shape) == 3 and np_array.shape[2] == 3: # color image
		color = True
	elif len(np_array.shape) == 2 or len(np_array.shape) == 3 and np_array.shape[2] == 1: # greyscale
		color = False
	else:
		raise Exception('Image must have H x W x 3, H x W x 1 or H x W dimensions.')

	with open(filepath, "w") as file:
		file.write('PF\n' if color else 'Pf\n')
		file.write('%d %d\n' % (np_array.shape[1], np_array.shape[0]))

		endian = np_array.dtype.byteorder

		file.write('%f\n' % 1)

		np_array.tofile(file)

class ImageBuilder(object):
	@classmethod
	def generate_one_imageset(cls, cfg, seed, overwrite=False, debug=False):
		root_dir = cfg.get_config("output/root_directory")
		root_dir = Path(root_dir)
		pad = cfg.get_config("output/pad_zeros_to")
		out_dir = Path(cfg.get_config('output/root_directory')) / f"{seed:0{pad}}" / "images"
		pad = cfg.get_config('output/pad_zeros_to')

		image_operations = get_image_operations(cfg)
		mesh_npz_filepath = root_dir / f"{seed:0{pad}}" / "mesh.npz"
		mesh_stl_filepath = root_dir / f"{seed:0{pad}}" / "mesh.stl"
		mesh_ply_filepath = root_dir / f"{seed:0{pad}}" / "mesh.ply"
		mesh = cls.load_mesh(mesh_npz_filepath)

		if not overwrite:
			everything_exists = True
			for item in image_operations:
				for sub_item in ["images.npy", "depths.npy", "matrices.npz"]:
					if not (out_dir / item / sub_item).exists():
						everything_exists = False

			if everything_exists:
				return True

		image_cfg = cfg.generate(seed=seed)

		render_type = cfg.get_config("meta/renderer")

		if render_type == "optical":
			renderer = OpticalRenderer(image_cfg)
		elif render_type == "xray":
			renderer = XRayRenderer(image_cfg, debug=debug)
		else:
			raise NotImplementedError(f"Value '{render_type}' for config 'meta/renderer' is not valid. Must be one of: 'optical', 'xray'")

		raw_images, raw_depths, raw_matrices = renderer.generate_data(mesh=mesh, stl_filepath=str(mesh_stl_filepath.resolve()))

		processed_images = cls.process_images(raw_images, raw_depths, raw_matrices, image_operations)

		save_as_png = cfg.get_config("output/save/images_as_png")
		save_as_pfm = cfg.get_config("output/save/depths_as_pfm")

		for imageset_name, imageset_data in processed_images.items():
			imageset_images, imageset_depths, imageset_matrices = imageset_data

			save_to = out_dir / imageset_name
			save_to.mkdir(parents=True, exist_ok=True)

			np.save(save_to / "images.npy", imageset_images)
			np.save(save_to / "depths.npy", imageset_depths)
			np.savez_compressed(save_to / "matrices.npz", **imageset_matrices)

			if save_as_png:
				png_folder = save_to / "images"
				png_folder.mkdir(parents=True, exist_ok=True)

				for i in range(imageset_images.shape[2]):
					arr = imageset_images[:,:,i]
					rgb_image = np.zeros((arr.shape[0], arr.shape[1], 3))
					rgb_image[:, :, 0] = arr
					rgb_image[:, :, 1] = arr
					rgb_image[:, :, 2] = arr

					im = Image.fromarray(rgb_image.astype(np.uint8))

					im.save(png_folder / f"image_{i}.png")
			if save_as_pfm:
				pfm_folder = save_to / "depths"
				pfm_folder.mkdir(parents=True, exist_ok=True)

				for i in range(imageset_depths.shape[2]):
					arr = imageset_depths[:,:,i]

					save_np_to_pfm(arr, pfm_folder / f"depth_{i}.pfm")

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