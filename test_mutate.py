#!/usr/bin/env python3
import shutil
from datetime import datetime
import os

import click
import yaml
import RASPA2

import htsohm
from htsohm.files import load_config_file
from htsohm.material_files import mutate_material
from htsohm.material_files import load_material_from_yaml
from htsohm.material_files import dump_material_to_yaml

from htsohm import config
from htsohm.db.material import Material, session
from htsohm.htsohm import run_all_simulations

@click.group()
def test_mutate():
    pass

@test_mutate.command()
@click.argument('config_path')
def start(config_path):
    """
    Args:
        material_path
        number_of_mutations
        mutation_strength
    """

    config = load_config_file(config_path)
    htsohm_dir = os.path.dirname(os.path.dirname(htsohm.__file__))

    uuid                     = config['parent_uuid']
    children_per_generation  = config['children_per_generation']
    mutation_strength        = config['initial_mutation_strength']

    run_id = 'TM_%s' % (datetime.now().isoformat())
 
    config['run_id']         = run_id
    config['raspa2_dir']     = os.path.dirname(RASPA2.__file__)
    config['htsohm_dir']     = htsohm_dir

    run_dir = os.path.join(htsohm_dir, run_id)
    os.makedirs(run_dir, exist_ok=True)
    os.makedirs(os.path.join(run_dir, 'pseudo_materials'), exist_ok=True)
    file_name = os.path.join(run_dir, 'config.yaml')
    
    with open(file_name, 'w') as config_file:
        yaml.dump(config, config_file, default_flow_style=False)
    print('Run created with id: %s' % run_id)

    shutil.copy(
            os.path.join(htsohm_dir, '%s.yaml' % uuid),
            os.path.join(run_id, 'pseudo_materials'))

@test_mutate.command()
@click.argument('run_id')
def launch_worker(run_id):
    """Start process to manage run.

    Args:
        run_id (str): identification string for run.

    """
    htsohm._init(run_id)

    parent_uuid         = config['parent_uuid']
    size_of_generation  = config['children_per_generation']
    mutation_strength   = config['initial_mutation_strength']

    print('\nSIMULATING PARENT ...\n')

    parent_material = load_material_from_yaml(run_id, parent_uuid)
    
    parent_record = Material(parent_material.uuid, run_id)
    parent_record.generation = 0
    parent_id = parent_record.parent_id
    run_all_simulations(parent_record)
    session.add(parent_record)
    session.commit()

    for i in range(size_of_generation):

        print('\nMUTATING/SIMULATING MATERIAL %s / %s ...\n' % (i + 1,
            size_of_generation))

        material = mutate_material(parent_material, mutation_strength, config)
        dump_material_to_yaml(run_id, material)
        material_record = Material(material.uuid, run_id)
        material_record.generation = 1
        material_record.parent_id = parent_id
        run_all_simulations(material_record)
        session.add(material_record)
        session.commit()

    print('\n ... DONE!')

if __name__ == '__main__':
    test_mutate()
