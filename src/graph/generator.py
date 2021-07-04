import os
import sys
import ray
import time
from tqdm import tqdm
from pathlib import Path

from .lib.NetworkBuilder import NetworkBuilder

def generate_networks(cfg, overwrite=False):
	seed_start, seed_end = cfg.get_config("meta/random_seeds/start"), cfg.get_config("meta/random_seeds/end")
	seeds = range(seed_start, seed_end + 1)

	initialise_ray(cfg)

	try:
		futures = [generate_one_network.remote(cfg, seed, overwrite) for seed in seeds]
		
		wait_for_completion(futures, len(seeds))
	except Exception as e:
		[ray.cancel(process) for process in futures]
		print(e)
	except KeyboardInterrupt as k:
		[ray.cancel(process) for process in futures]
		try:
			sys.exit(k)
		except SystemExit:
			os._exit(k)

def initialise_ray(cfg):
	ray_config={
		"num_cpus": cfg.get_config("meta/num_cpus"),
		"object_store_memory": 10**9
		}
	additional_ray_config = {
		"configure_logging": False
	}

	ray.init(**{**ray_config, **additional_ray_config})

@ray.remote
def generate_one_network(cfg, seed, overwrite=False):
	if not overwrite:
		pad = cfg.get_config("output/pad_zeros_to")
		output_path = Path(cfg.get_config('output/root_directory')) / f"{seed:0{pad}}" / "network.swc"

		if output_path.exists(): return NetworkBuilder.return_codes["SKIPPED_EXISTING_NETWORK"]
	
	network_cfg = cfg.generate(seed=seed)

	generator = NetworkBuilder(network_cfg, seed)
	try:
		result = generator.run()
	except Exception as e:
		print(e)
		return -1

	return result

def wait_for_completion(futures, total_seeds):
	progress_bar = tqdm(total=total_seeds)
	completed_items = 0

	while completed_items < total_seeds:
		results, _ = ray.wait(futures, num_returns=1+completed_items)
		completed_items += 1
		progress_bar.update()