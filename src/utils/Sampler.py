import numpy as np
import scipy.stats

from .Config import Config

# Ensure each sampler behaves differently when sampling by giving them different codes
existing_samplers_so_far = 0

class Sampler(Config):
    def __init__(self, raw_config_dict):
        self._data = raw_config_dict
        self._random_obj = np.random.RandomState()

        global existing_samplers_so_far
        existing_samplers_so_far += 1


    def generate(self, seed=0, sampler_id=0):
        if seed > 0:
            self._random_obj = np.random.RandomState(10000*seed+sampler_id)

        evaluated_dict = {}
        self._recursive_evaluate(self._data, evaluated_dict, seed)

        return Config(evaluated_dict)

    def _recursive_evaluate(self, parent_dict, evaluated_dict, seed):
        for k,v in parent_dict.items():
            if isinstance(v, dict):
                if k == "protocol":
                    evaluated_dict[k] = self._evaluate_protocol(v, seed)
                    continue

                distribution = v.get("distribution")

                if distribution == "uniform":
                    evaluated_dict[k] = self._evaluate_uniform(v)
                elif distribution == "normal":
                    evaluated_dict[k] = self._evaluate_normal(v)
                else:
                    evaluated_dict[k] = {}
                    self._recursive_evaluate(v, evaluated_dict[k], seed)
            else:
                evaluated_dict[k] = v

    def _evaluate_uniform(self, generation_dict):
        assert "min" in generation_dict and "max" in generation_dict, f"Configuration for {path} must have a 'min' and 'max' specified"
        min, max = generation_dict.get("min"), generation_dict.get("max")
        value = self._random_obj.uniform(min, max)
        return value

    def _evaluate_normal(self, generation_dict):
        assert "mean" in generation_dict and "std" in generation_dict, f"Configuration for {path} must have a 'mean' and 'std' specified"

        mean, std = generation_dict.get("mean"), generation_dict.get("std")
        min, max = generation_dict.get("min"), generation_dict.get("max")

        if min is not None or max is not None:
            min = min if min is not None else -np.inf
            max = max if max is not None else np.inf
            value = self._evaluate_truncated_normal(mean, std, min, max)
        else:
            value = self._random_obj.normal(mean, std)

        return value

    def _evaluate_truncated_normal(self, mean, sd, low, upp):
        stats_obj = scipy.stats.truncnorm(
            (low - mean) / sd, (upp - mean) / sd, loc=mean, scale=sd
        )

        stats_obj.random_state = self._random_obj
        return stats_obj.rvs()

    def _evaluate_protocol(self, config, seed):

        if isinstance(config, dict):
            config = Sampler(config).generate(seed)

        instructions = []

        assert len(config.get_config()) == 1, f"Exactly one operation protocol must be specified (you have specified {', '.join(config.get_config().keys())})."
        if config.get_config("rotational"):
            num_capture_points = int(config.get_config("rotational/sequence_timespan")*config.get_config("rotational/framerate"))
            ppa_vals = np.linspace(config.get_config("rotational/ppa_start"),config.get_config("rotational/ppa_end"),num_capture_points)
            psa_vals = np.linspace(config.get_config("rotational/psa_start"),config.get_config("rotational/psa_end"),num_capture_points)

            instructions.append({"reset": "table"})

            for i in range(num_capture_points):
                instructions.append({
                    "set": {
                        "fluoroscope": {
                            "ppa": f"{ppa_vals[i]:.4f}",
                            "psa": f"{psa_vals[i]:.4f}"
                        }
                    }
                })
                instructions.append({"capture"})

        elif config.get_config("sequence"):
            num_capture_points = config.get_config("sequence/num_images")
            instructions.append({"reset": "table"})

            instructions.append({
                "set": {
                    "fluoroscope": {
                        "ppa": config.get_config("sequence/ppa_start"),
                        "psa": config.get_config("sequence/psa_start")
                    }
                }
            })
            instructions.append({"capture"})

            for i in range(num_capture_points-1):
                instructions.append({
                    "change": {
                        "fluoroscope": {
                            "ppa": config.get_config("sequence/ppa_change"),
                            "psa": config.get_config("sequence/psa_change")
                        }
                    }
                })
                instructions.append({"capture"})

        else:
            requested_instruction = list(config.get_config().keys())[0]
            raise NotImplementedError(f"{requested_instruction} is not a valid operation/protocol")

        return instructions
