import os
import sys
import argparse
import subprocess
from pathlib import Path

try:
	import bpy
	dir = os.path.dirname(bpy.data.filepath)
	if not dir in sys.path:
		sys.path.append(dir)

	from src.utils import get_config
	from src.three_d.generator import generate_meshes
except ImportError:
	from utils import get_config
	from three_d.generator import generate_samplesets

def run_blender_process(n_meshes, config_path, overwrite=False, debug=False):
	# TODO: Make this not hard-coded

	blender_exe = './src/external/blender-2.91.2-linux64/blender'
	blender_process_args = [
		'--background',
		'-P',
		__file__, # The script to run is this one
		'--',
		config_path,
		'--blendermode'
	]

	process_string = " ".join(str(i) for i in [blender_exe] + blender_process_args)
	
	from tqdm import tqdm
	progress_bar = tqdm(total=n_meshes)
	
	proc = subprocess.Popen(process_string, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	
	while True:
		line = proc.stdout.readline().decode("utf-8")
		if not line:
			break

		if "Export completed" in line:
			progress_bar.update(1)

def main(config_path, overwrite=False, blendermode=False, debug=False):
	default_config_path = "config/default.yaml"
	cfg = get_config(config_path, default_config_path)

	# generate_meshes can only be called via Blender. If this is a user-initiated script, it will be in Python mode,
	# so we open a subprocess that runs generate_meshes via Blender
	if blendermode:
		generate_meshes(cfg, overwrite, debug)
		return

	if not cfg.get_config("patient/use_existing_meshes"):
		n_meshes = 1 + int(cfg.get_config("meta/random_seeds/end")) - int(cfg.get_config("meta/random_seeds/start"))
		print("Generating Meshes")
		run_blender_process(n_meshes, config_path, overwrite, debug)

	print("Generating Samples")
	generate_samplesets(cfg, overwrite, debug)

if __name__ == "__main__":	
	parser = argparse.ArgumentParser(description='Turn a set of SWC files into mesh files.')
	parser.add_argument('config_path', type=str, help='Path to the generator config file.')
	parser.add_argument('-o','--overwrite', action='store_true', help='Overwrite existing files.')
	parser.add_argument('--blendermode', action='store_true', help='Used by the automatic Blender script only.')
	parser.add_argument('-d','--debug', action='store_true', help='Show output of script processes.')

	try:
		python_commands_index = sys.argv.index("--")
		parse_arguments = sys.argv[python_commands_index+1:]
	except ValueError:
		parse_arguments = sys.argv[1:]

	args, unknown = parser.parse_known_args(parse_arguments)

	main(args.config_path, args.overwrite, args.blendermode, args.debug)