import yaml
from pathlib import Path
from .Sampler import Sampler

def update_recursive(dict1, dict2):
	''' Update two config dictionaries recursively.

	Args:
		dict1 (dict): first dictionary to be updated
		dict2 (dict): second dictionary which entries should be used

	'''
	for k, v in dict2.items():
		if k not in dict1:
			dict1[k] = dict()
		if isinstance(v, dict):
			update_recursive(dict1[k], v)
		else:
			dict1[k] = v

def get_config(path, default_path):
    path = Path(path)
    default_path = Path(default_path)
    
    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist.")
    if not default_path.exists():
        raise FileNotFoundError(f"{default_path} does not exist.")

    with open(path, 'r') as f:
        config_custom = yaml.safe_load(f)

    with open(default_path, 'r') as f:
        config = yaml.safe_load(f)

    update_recursive(config, config_custom)

    return Sampler(config)


__all__ = [
    get_config,
]