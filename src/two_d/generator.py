import io
import pyrender
import numpy as np
from tqdm import tqdm
from multiprocessing import Pool
import multiprocessing.pool as mpp

from .lib.ImageBuilder import ImageBuilder
from utils.PoolIStarMap import istarmap

def generate_images(cfg, overwrite=False):
	seed_start, seed_end = cfg.get_config("meta/random_seeds/start"), cfg.get_config("meta/random_seeds/end")
	seeds = range(seed_start, seed_end + 1)

	num_processes = cfg.get_config("meta/num_cpus")
	mpp.Pool.istarmap = istarmap

	with Pool(num_processes) as p:
		iterable = [(cfg, seed, overwrite) for seed in seeds]
		for _ in tqdm(p.istarmap(ImageBuilder.generate_one_imageset, iterable),
						   total=len(iterable)):
			pass
