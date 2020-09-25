import ray
import time
import subprocess
from pathlib import Path

def generate_networks(cfg):
	seed_start, seed_end = cfg.get_config("meta/random_seeds/start"), cfg.get_config("meta/random_seeds/end")
	seeds = range(seed_start, seed_end + 1)

	ray.init()

	futures = [generate_one_network.remote(cfg, seed) for seed in seeds]
	print(ray.get(futures))

@ray.remote
def generate_one_network(cfg, seed):
	network_cfg = cfg.generate(seed=seed)
	generator = Generator(network_cfg, seed)
	try:
		result = generator.run()
	except Exception as e:
		print(e)
		return -1
	
	return result

class Generator(object):
	return_codes = {
		"SUCCESSFULLY_CREATED_NETWORK": 0b00,
		"SKIPPED_EXISTING_NETWORK": 0b01,
		"FAILED_CREATING_NETWORK": 0b10,
		"KEYBOARD_INTERRUPT": 0b11
	}
	
	def __init__(self, cfg, seed):
		self.config = cfg
		self.seed = seed

	def run(self):
		vascusynth_path = (Path(__file__) / '../..' / self.config.get_config('meta/vascusynth_path')).resolve()
		assert vascusynth_path.exists(), f"{vascusynth_path} is not a valid VascuSynth path"

		output_path = Path(self.config.get_config('output/root_directory')) / f"{self.seed:04}"
		output_path.mkdir(parents=True, exist_ok=True)
		output_path /= "network.swc"

		vascusynth_args = [
			str(vascusynth_path),
			'--rr', self.config.get_config('patient/heart/size/ostium_diameter')*0.5,
			'--am', self.config.get_config('patient/heart/rotation/mode'),
			'--bb', f"'{self.config.get_config('patient/heart/size/width')} {self.config.get_config('patient/heart/size/depth')} {self.config.get_config('patient/heart/size/height')}'",
			'--mr', f"'{self.config.get_config('patient/heart/rotation/x')} {self.config.get_config('patient/heart/rotation/y')} {self.config.get_config('patient/heart/rotation/z')}'",
			'--mt', self.config.get_config('patient/heart/size/thickness'),
			'--pp', self.config.get_config('patient/blood_vessels/mesh/perforation_pressure'),
			'--tp', self.config.get_config('patient/blood_vessels/mesh/terminal_pressure'),
			'--pf', self.config.get_config('patient/blood_vessels/mesh/perforation_flow'),
			'--r', self.config.get_config('patient/blood_vessels/mesh/rho'),
			'--g', self.config.get_config('patient/blood_vessels/mesh/gamma'),
			'--l', self.config.get_config('patient/blood_vessels/mesh/lambda'),
			'--m', self.config.get_config('patient/blood_vessels/mesh/mu'),
			'--md', self.config.get_config('patient/blood_vessels/mesh/minimum_distance'),
			'--nn', self.config.get_config('patient/blood_vessels/mesh/number_of_nodes'),
			'--cn', self.config.get_config('patient/blood_vessels/mesh/closest_neighbours'),
			'--ar', self.config.get_config('patient/blood_vessels/mesh/axial_refinement'),
			'--op', str(output_path.resolve()),
			'--rs', self.seed,
		]

		process = subprocess.Popen([str(arg) for arg in vascusynth_args], stdout=subprocess.DEVNULL)

		while process.poll() is None:
			try:
				time.sleep(1)
			except KeyboardInterrupt:
				process.terminate()
				return self.return_codes["KEYBOARD_INTERRUPT"]

		if process.poll() != 0:
			return self.return_codes["FAILED_CREATING_NETWORK"]

		return self.return_codes["SUCCESSFULLY_CREATED_NETWORK"]
		