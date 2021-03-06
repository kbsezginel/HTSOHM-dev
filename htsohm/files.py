# standard imports
import os

# related third party imports
import yaml

# local application/library specific imports
import htsohm

def load_config_file(file_name):
    """Reads input file.

    Args:
        file_name (str): auto-created config filename (ex. htsohm.sample.yaml).

    Returns:
        config (dict): parameters specified in config.

    """
    with open(file_name) as config_file:
         config = yaml.load(config_file)
    return config
