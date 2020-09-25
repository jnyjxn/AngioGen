import argparse

from utils import get_config

from generators.networks import generate_networks

def main(mode, config_path):
    default_config_path = "config/default.yaml"
    cfg = get_config(config_path, default_config_path)

    generate_networks(cfg)

    # if mode == "mesh":
    #     generate_meshes(cfg)

if __name__ == "__main__":
    # Arguments
    parser = argparse.ArgumentParser(
        description='Train the ONet part of MultiviewOccNet.'
    )
    parser.add_argument('mode', choices=['mesh', 'image'], help='Specify which type of data to generate.')
    parser.add_argument('config_path', type=str, help='Path to the generator config file.')

    args = parser.parse_args()

    main(args.mode, args.config_path)