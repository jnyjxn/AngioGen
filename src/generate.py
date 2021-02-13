import os
import sys
import argparse
import subprocess
from pathlib import Path

def get_conda_python():
	return Path(sys.exec_prefix) / "bin" / "python"

def main(config_path, overwrite=False):
	root_dir = Path(__file__).parents[0]
	pyth = get_conda_python()

	overwrite_cmd = "-o" if overwrite else ""
	pyopengl_platform = os.getenv("PYOPENGL_PLATFORM")
	pyopengl_platform_cmd = f"PYOPENGL_PLATFORM={pyopengl_platform}" if pyopengl_platform else ""

	print("Generating Graph Data")
	subprocess.run(f"{pyth} {root_dir}/generate_graph.py {config_path} {overwrite_cmd}", shell=True, check=True)

	print("Generating 3D Data")
	subprocess.run(f"{pyth} {root_dir}/generate_three_d.py {config_path} {overwrite_cmd}", shell=True, check=True)

	print("Generating 2D Data")
	subprocess.run(f"{pyopengl_platform_cmd} {pyth} {root_dir}/generate_two_d.py {config_path} {overwrite_cmd}", shell=True, check=True)

if __name__ == "__main__":	
	parser = argparse.ArgumentParser(description='Generate a dataset of coronary angiograms.')
	parser.add_argument('config_path', type=str, help='Path to the generator config file.')
	parser.add_argument('-o','--overwrite', action='store_true', help='Overwrite existing files.')
	args = parser.parse_args()

	main(args.config_path, args.overwrite)