import os
import sys
import argparse
import subprocess

import bpy
dir = os.path.dirname(bpy.data.filepath)
if not dir in sys.path:
	sys.path.append(dir)

from utils import get_config
from generators.meshes import generate_meshes

def main(config_path, overwrite=False):
	default_config_path = "config/default.yaml"
	cfg = get_config(config_path, default_config_path)

	generate_meshes(cfg, overwrite=overwrite)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Turn a set of SWC files into mesh files.')
	parser.add_argument('config_path', type=str, help='Path to the generator config file.')
	parser.add_argument('-o','--overwrite', action="store_true", help='Overwrite existing files.')

	try:
		python_commands_index = sys.argv.index("--")
		parse_arguments = sys.argv[python_commands_index+1:]
	except ValueError:
		parse_arguments = sys.argv[1:]

	args, unknown = parser.parse_known_args(parse_arguments)

	main(args.config_path, args.overwrite)