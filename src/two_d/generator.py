import io
import pyrender
import numpy as np
from tqdm import tqdm
from multiprocessing import Pool
import multiprocessing.pool as mpp

from .lib.ImageBuilder import ImageBuilder

def generate_images(cfg, overwrite=False):
	seed_start, seed_end = cfg.get_config("meta/random_seeds/start"), cfg.get_config("meta/random_seeds/end")
	seeds = range(seed_start, seed_end + 1)

	num_processes = cfg.get_config("meta/num_cpus")
	mpp.Pool.istarmap = istarmap

	with Pool(num_processes) as p:
		iterable = [(cfg, seed) for seed in seeds]
		for _ in tqdm(p.istarmap(ImageBuilder.generate_one_imageset, iterable),
						   total=len(iterable)):
			pass

# This function is purely to allow a tqdm progress bar
def istarmap(self, func, iterable, chunksize=1):
	"""starmap-version of imap
	"""
	self._check_running()
	if chunksize < 1:
		raise ValueError(
			"Chunksize must be 1+, not {0:n}".format(
				chunksize))

	task_batches = mpp.Pool._get_tasks(func, iterable, chunksize)
	result = mpp.IMapIterator(self)
	self._taskqueue.put(
		(
			self._guarded_task_generation(result._job,
										  mpp.starmapstar,
										  task_batches),
			result._set_length
		))
	return (item for chunk in result for item in chunk)

