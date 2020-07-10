import yaml
import itertools


def get_experiment_config(file: str):
    with open(file, "r") as f:
        return yaml.load(f, yaml.SafeLoader)


def load_experiment(file: str):
    experiments = get_experiment_config(file)
    for index_type, params in experiments['experiments'].items():
        param_names = params.keys()
        for param_values in itertools.product(*params.values()):
            assert (len(param_values) == len(param_names))
            yield index_type, dict(zip(param_names, param_values))
