from .SimpleOps import *

def get_plugin_image_operation(op_name):
	ops = {
		"crop": crop,
		"resize": resize
	}

	op = ops.get(op_name)

	if op is None:
		raise KeyError(f"{op_name} is not a valid image operation. Choose from {', '.join(ops.keys())}")

	return op

__all__ = [
	get_plugin_image_operation
]