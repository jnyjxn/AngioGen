import copy
import yaml
from pathlib import Path

class Config(object):  
    """Simple dict wrapper that adds a thin API allowing for slash-based retrieval of
    nested elements, e.g. cfg.get_config("meta/dataset_name")
    """      
    def __init__(self, raw_config_dict):
        self._data = raw_config_dict

    def get_config(self, path=None, default=None):
        recursive_dict = copy.deepcopy(self._data)

        if path is None:
            return recursive_dict

        path_items = path.split("/")[:-1]
        data_item = path.split("/")[-1]

        try:
            for path_item in path_items:
                recursive_dict = recursive_dict.get(path_item)

            value = recursive_dict.get(data_item, default)

            return value
        except (TypeError, AttributeError):
            return default
