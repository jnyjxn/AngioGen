import argparse

from utils import get_config
from two_d.generator import generate_images

def main(config_path, overwrite=False, debug=False):
	default_config_path = "config/default.yaml"
	cfg = get_config(config_path, default_config_path)

	generate_images(cfg, overwrite=overwrite, debug=debug)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Generate a set of image files representing angiographic projections.')
	parser.add_argument('config_path', type=str, help='Path to the generator config file.')
	parser.add_argument('-o','--overwrite', action="store_true", help='Overwrite existing files.')
	parser.add_argument('-d','--debug', action="store_true", help='Show debug info (XRay only).')
	args = parser.parse_args()

	main(args.config_path, args.overwrite, args.debug)