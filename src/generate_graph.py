import argparse
from pathlib import Path

from utils import get_config
from graph.generator import generate_networks

def main(config_path, overwrite=False):
	default_config_path = (Path(__file__) / '../../config/default.yaml').resolve()
	cfg = get_config(config_path, default_config_path)

	if cfg.get_config("patient/use_existing_meshes"):
		return

	generate_networks(cfg, overwrite=overwrite)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Generate a set of SWC files representing vascular networks.')
	parser.add_argument('config_path', type=str, help='Path to the generator config file.')
	parser.add_argument('-o','--overwrite', action="store_true", help='Overwrite existing files.')
	args = parser.parse_args()

	main(args.config_path, args.overwrite)