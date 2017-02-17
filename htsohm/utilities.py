import os

import yaml

import htsohm
from htsohm.db.__init__ import materials, mutation_strengths

def load_config_file(run_id):
    """Reads input file.
    Input files must be in .yaml format, see htsohm.sample.yaml
    """
    HTSOHM_path = os.path.dirname(os.path.dirname(htsohm.__file__))
    config_path = os.path.join(HTSOHM_path, run_id, 'config.yaml')
    with open(config_path) as file:
        config = yaml.load(file)
    return config

def get_limits(x, config):
    if 'ga' in x:
        limits = config['gas_adsorption_0']['limits']
    elif 'sa' in x:
        limits = config['surface_area']['limits']
    elif 'vf' in x:
        limits = config['helium_void_fraction']['limits']
    return limits

def get_attr(x):
    if x == 'ga_mutation_strength':
        attr = getattr(mutation_strengths.c, 'gas_adsorption_bin')
    elif x == 'sa_mutation_strength':
        attr = getattr(mutation_strengths.c, 'surface_area_bin')
    elif x == 'vf_mutation_strength':
        attr = getattr(mutation_strengths.c, 'void_fraction_bin')
    elif x == 'ga_bin':
        attr = getattr(materials.c, 'gas_adsorption_bin')
    elif x == 'sa_bin':
        attr = getattr(materials.c, 'surface_area_bin')
    elif x == 'vf_bin':
        attr = getattr(materials.c, 'void_fraction_bin')
    else:
        print('--flag not understood--')

    return attr

def get_width(x, config):
    x_limits = get_limits(x, config)
    return (x_limits[1] - x_limits[0]) / config['number_of_convergence_bins']

def get_z_attr(x, y):
    if x[:2] in ['ga', 'sa'] and y[:2] in ['ga', 'sa']:
        z_attr = getattr(materials.c, 'void_fraction_bin')
    elif x[:2] in ['sa', 'vf'] and y[:2] in ['sa', 'vf']:
        z_attr = getattr(materials.c, 'gas_adsorption_bin')
    elif x[:2] in ['ga', 'vf'] and y[:2] in ['ga', 'vf']:
        z_attr = getattr(materials.c, 'surface_area_bin')
    else:
        print('--flag not understood')
    return z_attr

def make_list(x):
    if type(x) != type([]):
            x = [x]
    return x
