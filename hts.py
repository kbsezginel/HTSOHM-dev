#!/usr/bin/env python3
from datetime import datetime
import os
from distutils.dir_util import copy_tree

import click
import yaml
import RASPA2

import htsohm
from htsohm.files import load_config_file
from htsohm.htsohm import worker_run_loop, calc_bin
from htsohm.db import session, Material

@click.group()
def hts():
    pass

@hts.command()
@click.argument('config_path',type=click.Path())
def start(config_path):
    """Create a new run.
    
    Args:
        config_path (str): path to config-file (ex: setting/htsohm.sample.yaml)

    Prints run_id, creates run-folder with config-file.

    """
    config = load_config_file(config_path)
    htsohm_dir = os.path.dirname(os.path.dirname(htsohm.__file__))
    run_id = datetime.now().isoformat()
    config['run_id'] = run_id
    config['raspa2_dir'] = os.path.dirname(RASPA2.__file__)
    config['htsohm_dir'] = htsohm_dir
    
    run_dir = os.path.join(htsohm_dir, run_id)
    os.makedirs(run_dir, exist_ok=True)
    file_name = os.path.join(run_dir, 'config.yaml')
    with open(file_name, 'w') as config_file:
        yaml.dump(config, config_file, default_flow_style=False)
    print('Run created with id: %s' % run_id)

@hts.command()
@click.argument('old_run_id')
@click.argument('generation')
@click.argument('config_path',type=click.Path())
def append(old_run_id, generation, config_path):
    """Create a new run, appending to previous dataset.
    
    Args:

    """
    config = load_config_file(config_path)
    htsohm_dir = os.path.dirname(os.path.dirname(htsohm.__file__))
    run_id = datetime.now().isoformat()
    config['run_id'] = run_id
    config['raspa2_dir'] = os.path.dirname(RASPA2.__file__)
    config['htsohm_dir'] = htsohm_dir
    
    run_dir = os.path.join(htsohm_dir, run_id)
    os.makedirs(run_dir, exist_ok=True)
    file_name = os.path.join(run_dir, 'config.yaml')
    with open(file_name, 'w') as config_file:
        yaml.dump(config, config_file, default_flow_style=False)
    print('Run created with id: %s' % run_id)

    print('Copying data from run : '.format(old_run_id))

    ids = [e[0] for e in session.query(Material.id).distinct() \
            .filter(Material.run_id==old_run_id,
                Material.generation<=generation).all()]

    properties = config['material_properties']

    for id in ids:
        old_material = session.query(Material).get(id)
        new_material = old_material.clone()
        new_material.id = None
        new_material.run_id = run_id

        if 'gas_adsorption_0' in properties and 'gas_adsorption_1' not in properties:
            new_material.gas_adsorption_bin = calc_bin(
                    new_material.ga0_absolute_volumetric_loading,
                    *config['gas_adsorption_0']['limits'],
                    config['number_of_convergence_bins'])

        if 'gas_adsorption_0' in properties and 'gas_adsorption_1' in properties:
            new_material.gas_adsorption_bin = calc_bin(
                    (new_material.ga0_absolute_volumetric_loading - new_material.ga1_absolute_volumetric_loading),
                    *config['gas_adsorption_1']['limits'],
                    config['number_of_convergence_bins'])

        if 'helium_void_fraction' in properties:
            new_material.void_fraction_bin = calc_bin(
                    new_material.vf_helium_void_fraction,
                    *config['helium_void_fraction']['limits'],
                    config['number_of_convergence_bins'])
        
        if 'surface_area' in properties:
            new_material.surface_area_bin = calc_bin(
                    new_material.sa_volumetric_surface_area,
                    *config['surface_area']['limits'],
                    config['number_of_convergence_bins'])
        
        session.add(new_material)
    session.commit()

    old_pseudo_materials_dir = os.path.join(old_run_id, 'pseudo_materials')
    pseudo_materials = [e[0] for e in session.query(Material.uuid) \
            .filter(Material.run_id == run_id,
                Material.generation <= generation).all()]
    for pseudo_material in pseudo_materials:
        file_path = os.path.join(old_pseudo_materials_dir,
                '{}.yaml'.format(pseudo_material))
        with open(file_path) as structure_file:
            pseudo_material = yaml.load(structure_file)
        pseudo_material.run_id = run_id
        pseudo_material.dump()

    print('...copy complete!')

@hts.command()
@click.argument('run_id')
def launch_worker(run_id):
    """Start process to manage run.

    Args:
        run_id (str): identification string for run.

    Runs HTSOHM-method in one process.

    """
    htsohm._init(run_id)
    worker_run_loop(run_id)

if __name__ == '__main__':
    hts()
