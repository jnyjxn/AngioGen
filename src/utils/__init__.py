import yaml
from pathlib import Path
from .Sampler import Sampler
try:
	from .ImageOps import get_plugin_image_operation
except ImportError:
	"""
	This import will fail when running via Blender for the generate_three_d script.
	"""

def update_recursive(dict1, dict2):
	''' Update two config dictionaries recursively.

	Args:
		dict1 (dict): first dictionary to be updated
		dict2 (dict): second dictionary which entries should be used

	'''
	if dict2 is None: return

	for k, v in dict2.items():
		if k not in dict1:
			dict1[k] = dict()
		if isinstance(v, dict):
			update_recursive(dict1[k], v)
		else:
			dict1[k] = v

def get_config(cfg_path, default_path):
	cfg_path = Path(cfg_path)
	default_path = Path(default_path)
	
	if not cfg_path.exists():
		raise FileNotFoundError(f"{cfg_path} does not exist.")
	if not default_path.exists():
		raise FileNotFoundError(f"{default_path} does not exist.")

	with open(cfg_path, 'r') as f:
		config_custom = yaml.safe_load(f)

	with open(default_path, 'r') as f:
		config = yaml.safe_load(f)

	update_recursive(config, config_custom)

	return Sampler(config)

def get_image_operations(cfg):
	image_processing_config = cfg.get_config("operation/image_processing")

	full_set = {}
	for group_name, group_operations in image_processing_config.items():
		op_functions = []
		op_cfgs = []
		for image_operation in group_operations:
			assert len(image_operation) == 1, f"image_processing group '{group_name}' item '{image_operation}' must have only one item, not {len(image_operation)}."
			image_operation_name, image_operation_cfg = list(image_operation.items()).pop()

			op_function = get_plugin_image_operation(image_operation_name)

			op_functions.append(op_function)
			op_cfgs.append(image_operation_cfg)

		full_set[group_name] = (
				op_functions,
				op_cfgs
			)

	return full_set

__all__ = [
	get_config,
	get_image_operations
]