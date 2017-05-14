import os
import sys
from math import sqrt
from datetime import datetime

import numpy as np
from sqlalchemy.sql import func, or_
from sqlalchemy.orm.exc import FlushError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import text
import yaml
import RASPA2

import htsohm
from htsohm import config
from htsohm.db import engine, session, Material, MutationStrength
from htsohm.material_files import generate_pseudo_material, mutate_pseudo_material
from htsohm.material_files import write_cif_file, write_mixing_rules
from htsohm import simulation

def materials_in_generation(run_id, generation):
    """Count number of materials in a generation.

    Args:
        run_id (str): identification string for run.
        generation (int): iteration in overall bin-mutate-simulate rountine.

    Returns:
        Number(int) of materials in a particular generation that are present in
        the database (the final step in bin-mutate-simulate routine).

    """
    return session.query(Material).filter(
        Material.run_id == run_id,
        Material.generation == generation
    ).count()

def last_generation(run_id):
    """Finds latest generation present in database.

    Args:
        run_id (str): identification string for run.

    Returns:
        Last generation(int) to be included in database.

    """
    return session.query(func.max(Material.generation)).filter(
        Material.run_id == run_id,
    )[0][0]

def calc_bin(value, bound_min, bound_max, bins):
    """Find bin in parameter range.

    Args:
        value (float): some value, the result of a simulation.
        bound_min (float): lower limit, defining the parameter-space.
        bound_max (float): upper limit, defining the parameter-space.
        bins (int): number of bins used to subdivide parameter-space.

    Returns:
        Bin(int) corresponding to the input-value.

    """
    step = (bound_max - bound_min) / bins
    assigned_bin = (value - bound_min) // step
    assigned_bin = min(assigned_bin, bins-1)
    assigned_bin = max(assigned_bin, 0)
    return int(assigned_bin)

def select_parent(run_id, max_generation, generation_limit):
    """Use bin-counts to preferentially select a list of 'rare' parents.

    Args:
        run_id (str): identification string for run.
        max_generation (int): latest generation to include when counting number
            of materials ub each bin.
        generation_limit (int): number of materials to query in each generation
            (as materials are added to database they are assigned an index
            within the generation to bound the number of materials in each
            generation).

    Returns:
        The material id(int) corresponding to some parent-material selected
        from database with a bias favoring materials in bins with the lowest
        counts.

    """
    simulations = config['material_properties']
    queries = []
    if 'gas_adsorption_0' in simulations or 'gas_adsorption_1' in simulations:
        queries.append( getattr(Material, 'gas_adsorption_bin') )
    if 'surface_area' in simulations:
        queries.append( getattr(Material, 'surface_area_bin') )
    if 'helium_void_fraction' in simulations:
        queries.append( getattr(Material, 'void_fraction_bin') )

    # Each bin is counted...
    bins_and_counts = session \
        .query(
            func.count(Material.id),
            *queries
        ) \
        .filter(
            Material.run_id == run_id,
            or_(Material.retest_passed == True, Material.retest_passed == None),
            Material.generation <= max_generation,
            Material.generation_index < generation_limit,
        ) \
        .group_by(*queries).all()[1:]

    bins = []
    for i in bins_and_counts:
        some_bin = {}
        for j in range(len(queries)):
            some_bin[queries[j]] = i[j + 1]
        bins.append(some_bin)
    total = sum([i[0] for i in bins_and_counts])
    # ...then assigned a weight.
    weights = [ total / float(i[0]) for i in bins_and_counts ]
    normalized_weights = [ weight / sum(weights) for weight in weights ]
    parent_bin = np.random.choice(bins, p = normalized_weights)
    
    parent_queries = [i == parent_bin[i] for i in queries]
    parent_query = session \
        .query(Material.id) \
        .filter(
            Material.run_id == run_id,
            or_(Material.retest_passed == True, Material.retest_passed == None),
            *parent_queries,
            Material.generation <= max_generation,
            Material.generation_index < generation_limit,
        ).all()
    potential_parents = [i[0] for i in parent_query]
    return int(np.random.choice(potential_parents))

def select_parent_interactive(run_id, max_generation, generation_limit):
    """"""
    simulations = config['material_properties']
    queries = []
    if 'gas_adsorption_0' in simulations or 'gas_adsorption_1' in simulations:
        queries.append( getattr(Material, 'gas_adsorption_bin') )
    if 'surface_area' in simulations:
        queries.append( getattr(Material, 'surface_area_bin') )
    if 'helium_void_fraction' in simulations:
        queries.append( getattr(Material, 'void_fraction_bin') )

    # Each bin is counted...
    bins_and_counts = session \
        .query(
            func.count(Material.id),
            *queries
        ) \
        .filter(
            Material.run_id == run_id,
            or_(Material.retest_passed == True, Material.retest_passed == None),
            Material.generation <= max_generation,
            Material.generation_index < generation_limit,
        ) \
        .group_by(*queries).all()[1:]

    bins = []
    for i in bins_and_counts:
        some_bin = {}
        for j in range(len(queries)):
            some_bin[queries[j]] = i[j + 1]
        bins.append(some_bin)
    total = sum([i[0] for i in bins_and_counts])
    # ...then assigned a weight.
    weights = [ total / float(i[0]) for i in bins_and_counts ]
    normalized_weights = [ weight / sum(weights) for weight in weights ]

    print('\n  BIN\t\t|  COUNT\t|  WEIGHT\t\t|  NORMALIZED-WEIGHT')
    print('----------------+---------------+-----------------------+---------------------')
    for i in range(len(bins_and_counts)):
        print('  {}\t|  {}\t\t|  {}\t\t|  {}'.format(
            bins_and_counts[i][1:len(queries) + 1], bins_and_counts[i][0],
            round(weights[i], 6), round(normalized_weights[i], 6)))
    print('\n')

    ga_bin = input('Press select a gas adsorption bin :\t')
    sa_bin = input('Press select a surface area bin :\t')
    vf_bin = input('Press select a void fraction bin :\t')

    parent_query = session \
        .query(Material.uuid) \
        .filter(
            Material.run_id == run_id,
            or_(Material.retest_passed == True, Material.retest_passed == None),
            Material.gas_adsorption_bin == ga_bin,
            Material.surface_area_bin == sa_bin,
            Material.void_fraction_bin == vf_bin,
            Material.generation <= max_generation,
            Material.generation_index < generation_limit,
        ).all()
    potential_parents = [i[0] for i in parent_query]

    print('Potential parents :')
    for i in potential_parents:
        print('\t{}'.format(i))

    while True:
        parent_uuid = input('Please select a parent UUID :\t')
        proceed = input('Are you sure you want select {} as a parent? (y/n) :\t'.format(parent_uuid))
        if proceed in ['n', 'N']:
            continue
        elif proceed in ['y', 'Y']:
            break
        else:
            print('Please enter y/n.')

    return session.query(Material.id).filter(Material.run_id == run_id, Material.uuid == parent_uuid).one()[0]

def run_all_simulations(material, pseudo_material):
    """Simulate helium void fraction, gas loading, and surface area.

    Args:
        material (sqlalchemy.orm.query.Query): material to be analyzed.

    Depending on properties specified in config, adds simulated data for helium
    void fraction, gas loading, heat of adsorption, surface area, and
    corresponding bins to row in database corresponding to the input-material.
        
    """
    simulations = config['material_properties']

    print('\n==============================================|')
    print('UUID :\t{}  |'.format(material.uuid))
    print('----------------+---------------+-------------|')
    print('  PROPERTY\t|  VALUE\t|  BIN\t      |')
    print('----------------+---------------+-------------|')

    ############################################################################
    # run helium void fraction simulation
    if 'helium_void_fraction' in simulations:
        if config['artificial_data'] == 'off':
            results = simulation.helium_void_fraction.run(
                material.run_id, pseudo_material)
            material.update_from_dict(results)
            material.void_fraction_bin = calc_bin(
                material.vf_helium_void_fraction,
                *config['helium_void_fraction']['limits'],
                config['number_of_convergence_bins']
            )
        else:
            results = {}
            results['vf_helium_void_fraction'] = pseudo_material.artificial_void_fraction()
            material.update_from_dict(results)
            material.void_fraction_bin = calc_bin(
                material.vf_helium_void_fraction,
                *config['helium_void_fraction']['limits'],
                config['number_of_convergence_bins']
            )
            print('void fraction\t|  {}\t|  {}\t      |'.format(
                round(results['vf_helium_void_fraction'], 4),
                material.void_fraction_bin))

    else:
        material.void_fraction_bin = 0
    ############################################################################
    # run gas loading simulation
    if 'gas_adsorption_0' in simulations and 'gas_adsorption_1' not in simulations:
        if config['artificial_data'] == 'off':
            arguments = [material.run_id, pseudo_material]
            if 'helium_void_fraction' in simulations:
                arguments.append(material.vf_helium_void_fraction)
            results = simulation.gas_adsorption_0.run(*arguments)
            material.update_from_dict(results)
            material.gas_adsorption_bin = calc_bin(
                material.ga0_absolute_volumetric_loading,
                *config['gas_adsorption_0']['limits'],
                config['number_of_convergence_bins']
            )
        else:
            results = {}
            results['ga0_absolute_volumetric_loading'] = pseudo_material.artificial_gas_adsorption()
            material.update_from_dict(results)
            material.gas_adsorption_bin = calc_bin(
                material.ga0_absolute_volumetric_loading,
                *config['gas_adsorption_0']['limits'],
                config['number_of_convergence_bins']
            )
            print('gas adsorption\t|  {}\t|  {}\t      |'.format(
                round(results['ga0_absolute_volumetric_loading'], 4),
                material.gas_adsorption_bin))

    elif 'gas_adsorption_0' in simulations and 'gas_adsorption_1' in simulations:
        if config['artificial_data'] == 'off':
            arguments = [material.run_id, pseudo_material]
            if 'helium_void_fraction' in simulations:
                arguments.append(material.vf_helium_void_fraction)
            results = simulation.gas_adsorption_0.run(*arguments)
            material.update_from_dict(results)
            results = simulation.gas_adsorption_1.run(*arguments)
            material.update_from_dict(results)
            material.gas_adsorption_bin = calc_bin(
                abs(material.ga0_absolute_volumetric_loading - material.ga1_absolute_volumetric_loading),
                *config['gas_adsorption_0']['limits'],
                config['number_of_convergence_bins']
            )
        else:
            results = {}
            results['ga0_absolute_volumetric_loading'] = pseudo_material.artificial_gas_adsorption()
            results['ga1_absolute_volumetric_loading'] = pseudo_material.artificial_gas_adsorption()
            material.update_from_dict(results)
            material.gas_adsorption_bin = calc_bin(
                material.ga0_absolute_volumetric_loading,
                *config['gas_adsorption_0']['limits'],
                config['number_of_convergence_bins']
            )
            print('gas adsorption\t|  {}\t|  {}\t      |'.format(
                round(results['ga0_absolute_volumetric_loading'], 4),
                material.gas_adsorption_bin))

    elif 'gas_adsorption_0' not in simulations:
        material.gas_adsorption_bin = 0
    ############################################################################
    # run surface area simulation
    if 'surface_area' in simulations:
        if config['artificial_data'] == 'off':
            results = simulation.surface_area.run(
                    material.run_id, pseudo_material)
            material.update_from_dict(results)
            material.surface_area_bin = calc_bin(
                material.sa_volumetric_surface_area,
                *config['surface_area']['limits'],
                config['number_of_convergence_bins']
            )
        else:
            results = {}
            results['sa_volumetric_surface_area'] = pseudo_material.artificial_surface_area()
            material.update_from_dict(results)
            material.surface_area_bin = calc_bin(
                material.sa_volumetric_surface_area,
                *config['surface_area']['limits'],
                config['number_of_convergence_bins']
            )
            print('surface area\t|  {}\t|  {}\t      |'.format(
                round(results['sa_volumetric_surface_area'], 4),
                material.surface_area_bin))

    else:
        material.surface_area_bin = 0

def retest(m_orig, retests, tolerance, pseudo_material):
    """Reproduce simulations  to prevent statistical errors.

    Args:
        m_orig (sqlalchemy.orm.query.Query): material to retest.
        retests (int): number of times to reproduce each simulation.
        tolerance (float): acceptance criteria as percent deviation from
            originally calculated value.

    Queries database to determine if there are remained retests to  be run.
    Updates row in database with total number of retests and results.

    """
    m = m_orig.clone()
    print('Retest {} / {}'.format(m_orig.retest_num + 1, retests))
    run_all_simulations(m, pseudo_material)

    simulations = config['material_properties']

    # requery row from database, in case someone else has changed it, and lock it
    # if the row is presently locked, this method blocks until the row lock is released
    session.refresh(m_orig, lockmode='update')

    if config['interactive_mode'] == 'on':
        x0 = m_orig.retest_gas_adsorption_0_sum
        x1 = m_orig.retest_gas_adsorption_1_sum
        y = m_orig.retest_surface_area_sum
        z = m_orig.retest_void_fraction_sum
            
    if m_orig.retest_num < retests:
        if 'gas_adsorption_0' in simulations:
            m_orig.retest_gas_adsorption_0_sum += m.ga0_absolute_volumetric_loading
        if 'gas_adsorption_1' in simulations:
            m_orig.retest_gas_adsorption_1_sum += m.ga1_absolute_volumetric_loading
        if 'surface_area' in simulations:
            m_orig.retest_surface_area_sum += m.sa_volumetric_surface_area
        if 'helium_void_fraction' in simulations:
            m_orig.retest_void_fraction_sum += m.vf_helium_void_fraction
        m_orig.retest_num += 1
        session.commit()        

    if config['interactive_mode'] == 'on':
        print('\n  PROPERTY\t\t|  OLD SUM\t|  NEW VALUE\t|  NEW SUM')
        print('------------------------+---------------+---------------+-----------')
        if 'gas_adsorption_0' in config['material_properties']:
            print('  gas-0 adsorption\t|  {}\t|  {}\t|  {}'.format(
                round(x0, 4),
                round(m.ga0_absolute_volumetric_loading, 4),
                round(m_orig.retest_gas_adsorption_0_sum, 4)))
        if 'gas_adsorption_1' in config['material_properties']:
            print('  gas-1 adsorption\t|  {}\t|  {}\t|  {}'.format(
                round(x1, 4),
                round(m.ga1_absolute_volumetric_loading, 4),
                round(m_orig.retest_gas_adsorption_1_sum, 4)))
        if 'surface_area' in config['material_properties']:
            print('  surface area\t\t|  {}\t|  {}\t|  {}'.format(
                round(y, 4),
                round(m.sa_volumetric_surface_area, 4),
                round(m_orig.retest_surface_area_sum, 4)))
        if 'helium_void_fraction' in config['material_properties']:
            print('  void fraction\t\t|  {}\t|  {}\t|  {}'.format(
                round(z, 4),
                round(m.vf_helium_void_fraction, 4),
                round(m_orig.retest_void_fraction_sum, 4)))


    if m_orig.retest_num >= retests:
        if config['interactive_mode'] != 'on':
            try:
                m_orig.retest_passed = m.calculate_retest_result(tolerance)
                print('\nRETEST_PASSED :\t%s' % m_orig.retest_passed)
                session.commit()
            except ZeroDivisionError as e:
                print('WARNING: ZeroDivisionError - material.calculate_retest_result(tolerance)')
        elif config['interactive_mode'] == 'on':
            print('\tPlease check, using the values below, that the difference\n' +
                    '\tbetween the original value and averaged retest values is\n' +
                    '\tnot greater than the tolerance times bin-width.')
            print('==============================================================================')
            print('  TOLERANCE\t|  {}'.format(config['retests']['tolerance']))
            print('==============================================================================')
            print('  NUM. TESTS\t|  {}'.format(config['retests']['number']))
            print('==============================================================================')
            print('  PROPERTY\t\t| ORIGINAL VALUE\t|  RETEST SUM\t|  BIN-WIDTH')
            print('------------------------+-----------------------+---------------+-------------')

            if 'gas_adsorption_0' in config['material_properties']:
                print('  gas-0 adsorption\t|  {}\t\t|  {}\t|  {}'.format(
                    round(m_orig.ga0_absolute_volumetric_loading, 4),
                    round(m_orig.retest_gas_adsorption_0_sum, 4),
                    (config['gas_adsorption_0']['limits'][1] - config['gas_adsorption_0']['limits'][0]) / config['number_of_convergence_bins']))
            if 'gas_adsorption_1' in config['material_properties']:
                print('  gas-1 adsorption\t|  {}\t\t|  {}\t|  {}'.format(
                    round(m_orig.ga1_absolute_volumetric_loading, 4),
                    round(m_orig.retest_gas_adsorption_1_sum, 4),
                    (config['gas_adsorption_0']['limits'][1] - config['gas_adsorption_0']['limits'][0]) / config['number_of_convergence_bins']))
            if 'surface_area' in config['material_properties']:
                print('  surface area\t\t|  {}\t\t|  {}\t|  {}'.format(
                    round(m_orig.sa_volumetric_surface_area, 4),
                    round(m_orig.retest_surface_area_sum, 4),
                    (config['surface_area']['limits'][1] - config['surface_area']['limits'][0]) / config['number_of_convergence_bins']))
            if 'helium_void_fraction' in config['material_properties']:
                print('  void fraction\t\t|  {}\t\t|  {}\t|  {}'.format(
                    round(m_orig.vf_helium_void_fraction, 4),
                    round(m_orig.retest_void_fraction_sum, 4),
                    (config['helium_void_fraction']['limits'][1] - config['helium_void_fraction']['limits'][0]) / config['number_of_convergence_bins']))

            while True:
                while True:
                    pass_fail = input('Does {} pass the retest? (y/n) :\t'.format(m_orig.uuid))
                    if pass_fail in ['n', 'N', 'y', 'Y']:
                        break
                    else:
                        print('Please enter (y/n).')
                double_check = input('Are you sure? (y/n) :\t')
                if double_check in ['y', 'Y']:
                    break
                elif double_check in ['n', 'N']:
                    continue
                else:
                    print('Please enter (y/n).')
            if pass_fail in ['y', 'Y']:
                m_orig.retest_passed = True
            elif pass_fail in ['n', 'N']:
                m_orig.retest_passed = False
            session.commit()

def get_all_parent_ids(run_id, generation):
    return [e[0] for e in session.query(Material.parent_id) \
            .filter(Material.run_id == run_id, Material.generation == generation) \
            .distinct() if e[0] != None]

def calculate_percent_children_in_bin(run_id, generation, bin_coordinate):
    """Find the fraction of children generated by all parents from a particular
    bin who also belong in the same bin as their parent.

    Args:
        run_id (str): run identification string.
        generation (int): interation in overall process.
        bin (list int): [gas_adsorption_bin, surface_area_bin, void_fraction_bin].

    Returns:
        Fraction of children in the same bin as their parent for all parents in
        a particular bin.
    """
    sql = text("""
        select
            m.gas_adsorption_bin,
            m.surface_area_bin,
            m.void_fraction_bin,
            (
                m.gas_adsorption_bin = p.gas_adsorption_bin and
                m.surface_area_bin = p.surface_area_bin and
                m.void_fraction_bin = p.void_fraction_bin
            ) as in_bin
        from materials m
        join materials p on (m.parent_id = p.id)
        where m.generation = :gen
            and m.run_id = :run_id
            and p.gas_adsorption_bin = :ga_bin
            and p.surface_area_bin = :sa_bin
            and p.void_fraction_bin = :vf_bin
        """)

    rows = engine.connect().execute(
        sql,
        gen=generation,
        run_id=run_id,
        ga_bin=bin_coordinate[0],
        sa_bin=bin_coordinate[1],
        vf_bin=bin_coordinate[2]
    ).fetchall()

    if (config['interactive_mode'] == 'on' and 
            len([r for r in rows if r.in_bin]) != 0):
        print('Number of children in the parent-bin :\t{}' \
                .format(len([r for r in rows if r.in_bin])))
        print('Total number of children :\t\t{}'.format(len(rows)))

    return len([ r for r in rows if r.in_bin ]) / len(rows)

def calculate_mutation_strength(run_id, generation, mutation_strength_bin):
    """Query mutation_strength for bin and adjust as necessary.

    Args:
        run_id (str): identification string for run.
        generation (int): iteration in bin-mutate-/workersimulate routine.
        parent (sqlalchemy.orm.query.Query): parent-material corresponding to
            the bin being queried.

    Returns:
        mutation_strength.strength (float): mutation strength to be used for
        parents in the bin being queried. If the fraction of children from
        previous generation which populate the SAME bin as their parent is LESS
        THAN 10% then the mutation strength is REDUCED BY 5%. If the fraction
        of these children populating the SAME bin as their parent is GREATER
        THAN 50% then the mutation strength is INCREASED BY 5%.

    """
    mutation_strength_key = [run_id, generation] + mutation_strength_bin
    mutation_strength = session.query(MutationStrength).get(mutation_strength_key)

    if mutation_strength:
        print("Mutation strength already calculated for this bin and generation.")
    else:
        print("Calculating mutation strength...")
        mutation_strength = MutationStrength.get_prior(*mutation_strength_key).clone()
        if config['interactive_mode'] == 'on':
            print('Prior mutation strength :\t{}'.format(mutation_strength.strength))
        mutation_strength.generation = generation

        try:
            fraction_in_parent_bin = calculate_percent_children_in_bin(run_id, generation, mutation_strength_bin)

            if config['interactive_mode'] != 'on':
                if fraction_in_parent_bin < 0.1 and mutation_strength.strength - 0.05 > 0:
                    mutation_strength.strength -= 0.05
                elif fraction_in_parent_bin > 0.5 and mutation_strength.strength + 0.05 < 1:
                    mutation_strength.strength += 0.05

            elif config['interactive_mode'] == 'on':
                print('\tFor adaptive mutation strength(s), DECREASE strength \n' +
                        '\tby 5% if the fraction of children in parent-bin is \n' +
                        '\tLESS THAN 0.1; INCREASE strength by 5% if the \n' +
                        '\tfraction of children in parent-bin is GREATER THAN \n' +
                        '\t0.5.')
                while True:
                    mutation_strength.strength = input('Please Enter new mutation strength :\t')
                    proceed = input('Are you sure you want to assign {} to bin {} ? (y/n) :\t'.format(
                        mutation_strength.strength, mutation_strength_bin))
                    if proceed in ['n', 'N']:
                        continue
                    elif proceed in ['y', 'Y']:
                        break
                    else:
                        print('Please Enter y/n.')
        except ZeroDivisionError:
            print("No prior generation materials in this bin with children.")

        try:
            session.add(mutation_strength)
            session.commit()
        except (FlushError, IntegrityError) as e:
            print("Somebody beat us to saving a row with this generation. That's ok!")
            Session.rollback()
            # it's ok b/c this calculation should always yield the exact same result!
    sys.stdout.flush()
    return mutation_strength.strength

def evaluate_convergence(run_id, generation):
    '''Determines convergence by calculating variance of bin-counts.
    
    Args:
        run_id (str): identification string for run.
        generation (int): iteration in bin-mutate-simulate routine.

    Returns:
        bool: True if variance is less than or equal to cutt-off criteria (so
            method will continue running).
    '''
    simulations = config['material_properties']
    query_group = []
    if 'gas_adsorption' in simulations:
        query_group.append( getattr(Material, 'gas_adsorption_bin') )
    if 'surface_area' in simulations:
        query_group.append( getattr(Material, 'surface_area_bin') )
    if 'helium_void_fraction' in simulations:
        query_group.append( getattr(Material, 'void_fraction_bin') )

    bin_counts = session \
        .query(func.count(Material.id)) \
        .filter(
            Material.run_id == run_id, Material.generation < generation,
            Material.generation_index < config['children_per_generation']
        ) \
        .group_by(*query_group).all()
    bin_counts = [i[0] for i in bin_counts]    # convert SQLAlchemy result to list
    variance = sqrt( sum([(i - (sum(bin_counts) / len(bin_counts)))**2 for i in bin_counts]) / len(bin_counts))
    print('\nCONVERGENCE:\t%s\n' % variance)
    sys.stdout.flush()
    return variance <= config['convergence_cutoff_criteria']

def print_block(string):
    print('{0}\n{1}\n{0}'.format('=' * 80, string))

def load_pseudo_material(run_id, material):
    pseudo_material_path = os.path.join(
            os.path.dirname(os.path.dirname(htsohm.__file__)),
            run_id,
            'pseudo_materials',
            '{0}.yaml'.format(material.uuid)
        )
    with open(pseudo_material_path) as parent_file:
        parent_pseudo_material = yaml.load(parent_file)
    return parent_pseudo_material

def worker_run_loop(run_id):
    """
    Args:
        run_id (str): identification string for run.

    Writes seed generation and simulates properties, then manages overall
    bin-mutate-simualte routine until convergence cutt-off or maximum
    number of generations is reached.

    """
    print('CONFIG\n{0}'.format(config))

    gen = last_generation(run_id) or 0

    converged = False
    while not converged:
        print_block('GENERATION {}'.format(gen))
        size_of_generation = config['children_per_generation']

        while materials_in_generation(run_id, gen) < size_of_generation:
            if gen == 0:
                print_block('Generating pseudomaterial...')
                material, pseudo_material = generate_pseudo_material(
                        run_id, config['number_of_atom_types'])
                pseudo_material.dump()
            else:
                print_block('Selecting parent...')
                
                if config['selection_mode'] == 'manual':
                     parent_id = select_parent_interactive(run_id, max_generation=(gen - 1),
                                                      generation_limit=config['children_per_generation'])

#                    uuid = input('\n Enter UUID :\t')
#                    parent_id = session.query(Material.id).filter(
#                            Material.run_id == run_id, Material.uuid==uuid).one()[0]
                
                else:
                    parent_id = select_parent(run_id, max_generation=(gen - 1),
                                                      generation_limit=config['children_per_generation'])

                parent_material = session.query(Material).get(parent_id)
                parent_pseudo_material = load_pseudo_material(run_id, parent_material)

                # run retests until we've run enough
                print_block('Running retest...')
                while parent_material.retest_passed is None:
                    print("running retest...")
                    print("Date :\t%s" % datetime.now().date().isoformat())
                    print("Time :\t%s" % datetime.now().time().isoformat())
                    retest(
                            parent_material, config['retests']['number'],
                            config['retests']['tolerance'], parent_pseudo_material
                        )
                    session.refresh(parent_material)

                if not parent_material.retest_passed:
                    print("parent failed retest. restarting with parent selection.")
                    continue

                # obtain mutation strength
                if config['mutation_strength_method'] == 'flat':
                    mutation_strength = config['initial_mutation_strength']
                else:
                    mutation_strength_key = [run_id, gen] + parent_material.bin
                    mutation_strength = MutationStrength \
                            .get_prior(*mutation_strength_key).clone().strength
                
                # mutate material
                print_block('Mutating pseudomaterial..')
                material, pseudo_material = mutate_pseudo_material(
                        parent_material, parent_pseudo_material, mutation_strength, gen)
                pseudo_material.dump()
            run_all_simulations(material, pseudo_material)
            session.add(material)
            session.commit()

            material.generation_index = material.calculate_generation_index()
            if material.generation_index < config['children_per_generation']:
                print_block('ADDING MATERIAL {}'.format(material.uuid))
                session.add(material)

            #===================================================================
            # for visualising materials...
            #===================================================================
            print('Adding material to RASPA internal libraries...')
            raspa_dir = os.path.dirname(RASPA2.__file__)
            cif_dir = os.path.join(raspa_dir, 'share', 'raspa', 'structures', 'cif')
            write_cif_file(pseudo_material, cif_dir)
            ff_dir = os.path.join(raspa_dir, 'share', 'raspa', 'forcefield', pseudo_material.uuid)
            os.makedirs(ff_dir, exist_ok=True)
            write_mixing_rules(pseudo_material, ff_dir)

            if config['interactive_mode'] == 'on':
                print("\n\nGeneration :\t{}\nMat. no. :\t{} / {}".format(gen,
                    material.generation_index + 1, config['children_per_generation']))
                input("\nPress Enter to continue...\n")

            if config['mutation_strength_method'] != 'flat':
                if (
                    material.generation_index == config['children_per_generation'] - 1
                    and gen > 0
                    ):
                    parent_ids = get_all_parent_ids(run_id, gen)
    
                    print_block('Calculating mutation strengths...')
                    ms_bins = []
                    for parent_id in parent_ids:
                        parent_bin = session.query(Material).get(parent_id).bin
                        if parent_bin not in ms_bins:
                            if config['interactive_mode'] != 'on':
                                print(
                                        (
                                            'Calculating bin-mutation-strength for bin : {0}'
                                       ).format(parent_bin)
                                    )
                                calculate_mutation_strength(run_id, gen + 1, parent_bin)
                        ms_bins.append(parent_bin)

                    if config['interactive_mode'] == 'on':
                        print('The following bins contain parents for the preceding generation:')
                        for some_bin in ms_bins:
                            print('\t{}'.format(some_bin))
                        input('Press Enter to begin calculating new mutation strength(s) :')
                        counter = 1
                        for some_bin in ms_bins:
                            print('\nCalculating strength for bin :\t{}'.format(some_bin))
                            print('Bin {} / {}'.format(counter, len(ms_bins)))
                            calculate_mutation_strength(run_id, gen + 1, parent_bin)
                            input('Press Enter to continue :')


            else:
                # delete excess rows
                # session.delete(material)
                pass
            session.commit()
            sys.stdout.flush()
        gen += 1
        converged = evaluate_convergence(run_id, gen)
