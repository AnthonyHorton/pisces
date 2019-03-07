import os

import yaml

def load_config(config_path, path_root=None):
    if not os.path.isabs(config_path) and path_root:
        config_path = os.path.join(path_root, config_path)

    try:
        with open(config_path) as config_file:
            config = yaml.load(config_file)
    except OSError as err:
        msg = "Error opening config {}: {}".format(config_path, err)
        raise OSError(msg)
    except yaml.YAMLError as err:
        msg = "Error loading config {}: {}".format(config_path, err)
        raise yaml.YAMLError(msg)

    return config
