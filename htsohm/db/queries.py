from statistics import variance

from sqlalchemy import *

from htsohm import config
from htsohm.utilities import *
from htsohm.db.__init__ import engine, materials, mutation_strengths
from htsohm.db.mutation_strength import *
from htsohm.htsohm import select_parent

def count_generations(run_id):
    """Queries database for last generation in run.

    Args:
        run_id (str): run identification string.

    Returns:
        generations (int): number of generations in run.

    """
    cols = [func.max(materials.c.generation)]
    rows = materials.c.run_id == run_id
    result = engine.execute(select(cols, rows))
    for row in result:
        max_gen = row[0]
    result.close()
    return max_gen

def query_points(x, z_bin, run_id, gen):
    print(x, z_bin, run_id, gen)
    config           = load_config_file(run_id)
    simulations      = config['material_properties']

    rows = and_(materials.c.run_id == run_id, materials.c.generation == gen)
    if z_bin != None:
        rows = and_(rows, get_z_attr(x, y) == z_bin)
    if 'TM' not in run_id:
        rows = and_(rows, or_(materials.c.retest_passed == None,
                                materials.c.retest_passed == True),
                        materials.c.generation_index <= generation_size)

    if x == 'vf' or x == 'sa' or 'gas_adsorption_1' not in simulations:
        if x == 'vf':
            cols = [materials.c.vf_helium_void_fraction]
        elif x == 'sa':
            cols = [materials.c.sa_volumetric_surface_area]
        elif x == 'ga':
            cols = [materials.c.ga0_absolute_volumetric_loading]
        result = engine.execute(select(cols, rows))
        x_ = []
        for row in result:
            x_.append(row[0])
        result.close()
    else:
        cols = [materials.c.ga0_absolute_volumetric_loading,
                materials.c.ga1_absolute_volumetric_loading]
        result = engine.execute(select(cols, rows))
        x_ = []
        for row in result:
            print(row)
            x_.append(abs(row[0] - row[1]))
        result.close()
    print(x_)
    return x_

def query_bin_counts(x, y, z_bin, run_id, gen):
    """Queries database for bin_counts.

    Args:
        x (str): `gl`, `sa`, `vf`.
        y (str): `gl`, `sa`, `vf`.
        z_bin (int): None, [0, number_of_bins].
        run_id (str): run identification string.
        gen (int): generation.

    Returns:
        values (list): [x_bin, y_bin, bin_count]

    If z_bin == None: all z_bins are queried, instead of one slice.

    """
    generation_size = load_config_file(run_id)['children_per_generation']

    cols = [get_attr(x), get_attr(y), func.count(materials.c.uuid)]
    rows = and_(materials.c.run_id == run_id, materials.c.generation <= gen)
    if 'TM' not in run_id:
        rows = and_(rows, or_(materials.c.retest_passed == None,
                                materials.c.retest_passed == True),
                        materials.c.generation_index <= generation_size)
    sort = [get_attr(x), get_attr(y)]
    ordr = [func.count(materials.c.uuid)]
    if z_bin != None:
        rows = and_(rows, get_z_attr(x, y) == z_bin)
    result = engine.execute(
            select(cols, rows).group_by(*sort).order_by(asc(*ordr)))
    x_ = []
    y_ = []
    c_ = []
    for row in result:
        x_.append(row[0])
        y_.append(row[1])
        c_.append(row[2])
    return x_, y_, c_

def query_all_counts(run_id, gen):
    """Queries database for bin_counts.

    Args:
        run_id (str): run identification string.
        gen (int): generation.

    Returns:
        values (list): [bin_counts]

    """
    generation_size = load_config_file(run_id)['children_per_generation']
    
    bins = [materials.c.gas_adsorption_bin,
            materials.c.surface_area_bin,
            materials.c.void_fraction_bin]
    cols = [*bins, func.count(materials.c.uuid)]
    rows = and_(materials.c.run_id == run_id, materials.c.generation <= gen)
    if 'TM' not in run_id:
        rows = and_(rows, or_(materials.c.retest_passed == None,
                                materials.c.retest_passed == True),
                        materials.c.generation_index <= generation_size)
    sort = bins
    ordr = [func.count(materials.c.uuid)]
    result = engine.execute(
            select(cols, rows).group_by(*sort).order_by(desc(*ordr)))
    c_ = []
    for row in result:
        c_.append(row[3])
    return c_

def get_max_count(x, y, z_bin, run_id, gen):
    """Query database for highest bin-count.

    Args:
        run_id (str): run identification string.

    Returns:
        max_counts (int): highest bin-count.

    """
    generation_size = load_config_file(run_id)['children_per_generation']

    cols = [func.count(materials.c.uuid)]
    rows = and_(materials.c.run_id == run_id, materials.c.generation <= gen)
    if 'TM' not in run_id:
        rows = and_(rows, or_(materials.c.retest_passed == None,
                                materials.c.retest_passed == True),
                        materials.c.generation_index <= generation_size)
    sort = [get_attr(x), get_attr(y)]
    if z_bin != 0:
        rows = and_(rows, get_z_attr(x, y) == z_bin)
    result = engine.execute(select(cols, rows).group_by(*sort))
    counts = [row[0] for row in result]
    result.close()
    if counts != []:
        return min(counts), max(counts), sum(counts) / len(counts)
    else:
        return 0, 0, 0

def find_most_children(x, y, z_bin, run_id, gen):
    generation_size = load_config_file(run_id)['children_per_generation']

    cols = [materials.c.parent_id]
    rows = and_(material.c.run_id == run_id, materials.c.generation == gen)
    if 'TM' not in run_id:
        rows = and_(rows, or_(materials.c.retest_passed == None,
                                materials.c.retest_passed == True),
                        materials.c.generation_index <= generation_size)
    sort = func.count(materials.c.parent_id)
    s = select(cols, rows).group_by(*cols).order_by(desc(sort))
    result = engine.execute(s)
    parent_ids = []
    for row in result:
        parent_ids.append(row[material.c.parent_id])
    parents = parents[5:]
    values = []
    for parent in parent_ids:
        cols = [get_attr(x), get_attr(y)]
        s = select(cols, materials.c.id == parent)
        result = engine.execute(s)
        for row in result:
            parent = [row[0], row[1]]
        result.close()
        rows = and_(rows, materials.c.parent_id == parent)
        s = select(cols, rows)
        result = engine.execute(s)
        children = []
        for row in result:
            children.append(row[0], row[1])
        result.close()
        line = [parent, children]
        values.append(line)
    return values

def get_bin_coordinate(x_attr, y_attr, x, y, z):
    if x_attr == mutation_strengths.c.gas_loading_bin:
        if y_attr == mutation_strengths.c.surface_area_bin:
            coords = [x, y, z]
        elif y_attr == mutation_strengths.c.void_fraction_bin:
            coords = [x, z, y]
    elif x_attr == mutation_strengths.c.surface_area_bin:
        if y_attr == mutation_strengths.c.gas_loading_bin:
            coords = [y, x, z]
        elif y_attr == mutation_strengths.c.void_fraction_bin:
            coords = [z, x, y]
    elif x_attr == mutation_strengths.c.void_fraction_bin:
        if y_attr == mutation_strengths.c.gas_loading_bin:
            coords = [y, z, x]
        elif y_attr == mutation_strengths.c.surface_area_bin:
            coords = [z, y, x]
    return coords

def last_mutation_strength(run_id, gen, x, y, z):
    cols = [mutation_strengths.c.strength]
    rows = and_(
            mutation_strengths.c.run_id == run_id,
            mutation_strengths.c.generation <= gen,
            mutation_strengths.c.gas_loading_bin == x,
            mutation_strengths.c.surface_area_bin == y,
            mutation_strengths.c.void_fraction_bin == z,
    )
    sort = mutation_strengths.c.generation
    result = engine.execute(select(cols, rows).order_by(asc(sort)))
    for row in result:
        ms = row[0]
    result.close()
    if 'ms' in vars():
        return ms
    else:
        return load_config_file(run_id)['initial_mutation_strength']

def query_mutation_strength(x, y, z_bin, run_id, gen):
    """Queries database for mutation strengths.
    
    Args:
        x (str): `gl`, `sa`, `vf`.
        y (str): `gl`, `sa`, `vf`.
        z_bin (int): None, [0, number_of_bins].
        run_id (str): run identification string.
        gen (int): generation.

    Returns:
        values (list): [x_bin, y_bin, mutation_strength]

    If z_bin == None: all z_bins are queried, instead of one slice.

    """
    number_of_bins = load_config_file(run_id)['number_of_convergence_bins']
    initial_strength = load_config_file(run_id)['initial_mutation_strength']
    x_ = get_attr(x)
    y_ = get_attr(y)
    z_ = [get_attr(i + '_mutation_strength') for i in ['ga', 'sa', 'vf']]
    z_.remove(x_)
    z_.remove(y_)
    vals = []
    for x in range(number_of_bins):
        for y in range(number_of_bins):
            cols = [mutation_strengths.c.strength]
            rows = and_(mutation_strengths.c.generation <= gen,
                    mutation_strengths.c.run_id == run_id,
                    x_ == x, y_ == y)
            if z_bin != None:
                rows = and_(rows, z_ == z_bin)
            s = select(cols, rows) \
                    .order_by(desc(mutation_strengths.c.generation)).limit(1)
            result = engine.execute(s)
            for row in result:
                ms = row[mutation_strengths.c.strength]
            result.close()
            if 'ms' not in vars():
                ms = initial_strength
            line = [x, y, ms]
            vals.append(line)
    print('vals :\t%s' % vals)
    return vals

def get_all_bins(x, y, z_bin, run_id, gen):
    cols = [get_attr(x), get_attr(y)]
    rows = and_(materials.c.generation <= gen,
            materials.c.run_id == run_id)
    if z_bin != None:
        rows = and_(rows, get_z_attr(x, y) == z_bin)
    return select(cols, rows)

def query_material(x, y, z_bin, id):
    """Query values `x` and `y` for one material.
   
    Args:
        x (str): `gl`, `sa`, `vf` or `gl_bin`, `sa_bin`, `vf_bin`
        y (str): `gl`, `sa`, `vf` or `gl_bin`, `sa_bin`, `vf_bin`
        id (int): Material.id
   
    Returns:
       value (list): [x(float, int), y(float, int)]
   
    """
    if z_bin != None:
        result = engine.execute(
            select([get_attr(x), get_attr(y)],
            and_(materials.c.id == id, get_z_attr(x, y) == z_bin))
        )
    else:
        result = engine.execute(
            select([get_attr(x), get_attr(y)], materials.c.id == id)
        )
    x_ = []
    y_ = []
    for row in result:
        x_.append(row[0])
        y_.append(row[1])
    result.close()
    return x_, y_

def query_parents(x, y, z_bin, run_id, gen):
    """Find parent-materials and return data.
       
    Args:
        x (str): `gl`, `sa`, `vf` or `gl_bin`, `sa_bin`, `vf_bin`.
        y (str): `gl`, `sa`, `vf` or `gl_bin`, `sa_bin`, `vf_bin`.
        z_bin (int): None, [0, number_of_generations].
        run_id (str): run identification string.
        gen (int): generation.
   
    Returns:
        values (list): [x(float, int), y(float, int)]
  
    """
    generation_size = load_config_file(run_id)['children_per_generation']

    cols = [materials.c.parent_id]
    rows = and_(materials.c.run_id == run_id, materials.c.generation == gen,
            or_(materials.c.retest_passed == None,
                                materials.c.retest_passed == True),
                        materials.c.generation_index <= generation_size)
    if z_bin != None:
        rows = and_(rows, get_z_attr(x, y) == z_bin)
    result = engine.execute(select(cols, rows))
    x_ = []
    y_ = []
    for row in result:
        x_list, y_list = query_material(x, y, z_bin, row[materials.c.parent_id])
        x_ += x_list
        y_ += y_list
    result.close()
    return x_, y_

def query_child_bins(x, y, z_bin, run_id, gen):
    """Query bin-coordinates for across generation.
    
    Args:
        x (str): `gl`, `sa`, `vf` or `gl_bin`, `sa_bin`, `vf_bin`.
        y (str): `gl`, `sa`, `vf` or `gl_bin`, `sa_bin`, `vf_bin`.
        z_bin (int): None, [0, number_of_generations].
        run_id (str): run identification string.
        gen (int): generation.

    Returns:
        values (list): [x(float, int), y(float, int)]

    """
    generation_size = load_config_file(run_id)['children_per_generation']

    cols = [get_attr(x), get_attr(y)]
    rows = and_(materials.c.run_id == run_id, materials.c.generation == gen,
            or_(materials.c.retest_passed == None,
                                materials.c.retest_passed == True),
                        materials.c.generation_index <= generation_size)
    if z_bin != None:
        rows = and_(rows, get_z_attr(x, y) == z_bin)
    return select(cols, rows)

def evaluate_convergence(run_id, gen):
    """Use variance to evaluate convergence.

    Args:
        run_id (str): run identification string.
        gen (int): generation.

    Returns:
        variance (float): variance.

    """
    print('CALLED evaluate_convergence')
    generation_size = load_config_file(run_id)['children_per_generation']

    cols = [func.count(materials.c.uuid)]
    rows = and_(materials.c.run_id == run_id, materials.c.generation <= gen,
            or_(materials.c.retest_passed == None,
                                materials.c.retest_passed == True),
                        materials.c.generation_index <= generation_size)
    sort = [materials.c.gas_adsorption_bin,
            materials.c.surface_area_bin,
            materials.c.void_fraction_bin]
    print(cols)
    print(rows)
    result = engine.execute(select(cols, rows).group_by(*sort))
    c = [row[0] for row in result]
    print('c :\t%s' % c)
    result.close()
    norm_c = [(x - min(c)) / (max(c) - min(c)) for x in c]
    return variance(norm_c)

def select_parents(x, y, z_bin, run_id, gen, number=100):
    config = load_config_file(run_id)
    generation_limit = config['children_per_generation']
    parents = []
    for i in range(number):
        parents.append(
            select_parent(run_id, gen, 100)
        )
    return parents

def query_z_bin(x, y, id):
    s = select([get_z_attr(x, y)], material.c.id == id)
    z_bin = [ row[0] for row in engine.execute(s) ]
    return z_bin

def get_max(run_id, x):
    """Queries database for highest value for inputted parameter.

    Args:
        run_id (str): run identification string.

    Returns:
        generations (int): highest value.

    """
    s = select([get_attr(x)], materials.c.run_id == run_id)
    result = engine.execute(s)
    for row in result:
        print(row)
    result.close()

def query_dGdP(x, z_bin, run_id, gen):
    x_ = get_attr(x)
    cols = [
        x_,
        materials.c.ga0_absolute_volumetric_loading,
        materials.ga1_absolute_volumetric_loading
    ]
    rows = and_(materials.c.run_id == run_id, materials.c.generation <= gen,
            or_(materials.c.retest_passed == None,
                                materials.c.retest_passed == True),
                        materials.c.generation_index <= generation_size)
    x = []
    y0 = []
    y1 = []
    result = engine.execute(select(cols, rows))
    for row in result:
        x.append(row[0])
        y0.append(row[1])
        y1.append(row[2])
    result.close()

    return x, y0, y1

def query_most_populous_bin(run_id):
    sql = text(
            'select (gas_adsorption_bin, surface_area_bin, ' +
            'void_fraction_bin) from materials where ' +
            'run_id=\'%s\' and generation_index <=100' % run_id +
            ' group by (gas_adsorption_bin, surface_area_bin, ' +
            'void_fraction_bin) order by count(uuid) desc limit 1;'
            )
    result = engine.execute(sql)
    for row in result:
        most_populous_bin = row[0]
    result.close()

    return most_populous_bin

def query_parents_of_bin(run_id, child_bin):
    sql = text(
            'select parent_id from materials where ' +
            'run_id=\'%s\' and generation_index <= 100 and ' % run_id +
            '(gas_adsorption_bin, surface_area_bin, void_fraction_bin)' +
            '=%s;' % child_bin
            )
    result=engine.execute(sql)
    parent_ids = []
    for row in result:
        parent_ids.append(row[0])
    result.close()

    return parent_ids

def parent_search(run_id):
    child_bin = query_most_populous_bin(run_id)
    parent_ids = query_parents_of_bin(run_id, child_bin)

    new_parent_ids = []
    parent_bins = []
    for parent_id in parent_ids:
        if parent_id != None:
            sql = text(
                    'select (gas_adsorption_bin, surface_area_bin, ' +
                    'void_fraction_bin) from materials where ' +
                    'run_id=\'%s\' and id=%s;' % (run_id, parent_id)
                    )
            result = engine.execute(sql)
            for row in result:
                parent_bins.append(row[0])
            result.close()
            new_parent_ids.append(parent_id)
    
    filtered_parent_bins = []
    for i in parent_bins:
        if i not in filtered_parent_bins:
            print('%s\t%s' % (i, parent_bins.count(i)))
            filtered_parent_bins.append(i)

    return parent_bins

def query_population_over_time(run_id, bin_of_interest, generations):
    counts = []
    for generation in range(generations):
        sql = text(
                'select count(uuid) from materials where ' +
                'run_id=\'%s\' and generation_index <= 100 and' % run_id +
                '(gas_adsorption_bin, surface_area_bin, void_fraction_bin)=' +
                '%s and generation <= %s;' % (bin_of_interest, generation)
                )
        result = engine.execute(sql)
        for row in result:
            if row[0] == None:
                counts.append(0)
            else:
                counts.append(int(row[0]))
        result.close()
    return counts

def query_average_bin_count(run_id, generation):
    sql = text(
            'select avg(x.count) from (select count(uuid) from materials ' +
            'where run_id=\'%s\' and generation <= %s ' % (run_id, generation) +
            'group by (gas_adsorption_bin, surface_area_bin, ' +
            'void_fraction_bin))x;'
            )
    result = engine.execute(sql)
    for row in result:
        average_bin_count = int(row[0])
    result.close()
    return average_bin_count

def query_all_parent_bins(run_id):
    config = load_config_file(run_id)
    
    sql = text(
            'select max(generation) from materials where ' +
            'run_id=\'%s\';' % run_id
            )
    result = engine.execute(sql)
    for row in result:
        max_generation = row[0]

    print('max generation :\t%s' % max_generation)

    # query parent_ids
    all_parent_ids = []
    for generation in range(1, max_generation):
        sql = text(
                'select parent_id from materials where ' +
                'run_id=\'%s\' and generation=%s;' % (run_id, generation)
                )
        result = engine.execute(sql)
        generation_parent_ids   = []
        for row in result:
            generation_parent_ids.append(row[0])
        result.close()
        all_parent_ids.append(generation_parent_ids)

    # query parent bins
    all_parent_bins = []
    for gen_parent_ids in all_parent_ids:
        gen_parent_bins = []
        for parent_id in gen_parent_ids:
            sql = text(
                    'select (gas_adsorption_bin, surface_area_bin, ' +
                    'void_fraction_bin) from materials where id=%s;' % parent_id
                    )
            result = engine.execute(sql)
            for row in result:
                gen_parent_bins.append(row[0])
            result.close()
        all_parent_bins.append(gen_parent_bins)
        
    # count and filter
    all_filtered_bins = []
    all_counts = []
    for gen_parent_bins in all_parent_bins:
        gen_filtered_bins = []
        gen_counts = []
        for parent_bin in gen_parent_bins:
            if parent_bin not in gen_filtered_bins:
                gen_filtered_bins.append(parent_bin)
                gen_counts.append(gen_parent_bins.count(parent_bin))
        all_filtered_bins.append(gen_filtered_bins)
        all_counts.append(gen_counts)

    # normalise count, combine in one object
    data = {}
    for generation in range(len(all_filtered_bins)):
        gen_bins = all_filtered_bins[generation]
        gen_counts = all_counts[generation]
        data['generation_%s' % generation] = {}
        data['generation_%s' % generation]['ga'] = [int(i[1]) for i in gen_bins]
        data['generation_%s' % generation]['sa'] = [int(i[3]) for i in gen_bins]
        data['generation_%s' % generation]['vf'] = [int(i[5]) for i in gen_bins]
        normalised_counts = [i / max(gen_counts) for i in gen_counts]
        data['generation_%s' % generation]['count'] = normalised_counts
        data['generation_%s' % generation]['min_count'] = min(gen_counts)
        data['generation_%s' % generation]['max_count'] = max(gen_counts)

    return data

def query_all_child_bins(run_id):
    config = load_config_file(run_id)
    
    sql = text(
            'select max(generation) from materials where ' +
            'run_id=\'%s\';' % run_id
            )
    result = engine.execute(sql)
    for row in result:
        max_generation = row[0]

    print('max generation :\t%s' % max_generation)

    # query bins and counts
    data = {}
    for generation in range(1, max_generation):
        sql = text(
                'select (gas_adsorption_bin, surface_area_bin, ' +
                'void_fraction_bin), count(uuid) from materials where ' +
                'run_id=\'%s\' and generation=%s' % (run_id, generation) +
#                'run_id=\'%s\' and generation=%s' % (run_id, generation - 1) +
                'group by (gas_adsorption_bin, surface_area_bin, ' +
                'void_fraction_bin);'
                )
        result = engine.execute(sql)
        data['generation_%s' % generation] = {}
        data['generation_%s' % generation]['ga'] = []
        data['generation_%s' % generation]['sa'] = []
        data['generation_%s' % generation]['vf'] = []
        count = []
        for row in result:
            data['generation_%s' % generation]['ga'].append(int(row[0][1]))
            data['generation_%s' % generation]['sa'].append(int(row[0][3]))
            data['generation_%s' % generation]['vf'].append(int(row[0][5]))
#            data['generation_%s' % generation]['count'].append(int(row[1]))
            count.append(int(row[1]))
        data['generation_%s' % generation]['count'] = [i / max(count) for i in count]
        data['generation_%s' % generation]['min_count'] = min(count)
        data['generation_%s' % generation]['max_count'] = max(count)

        result.close()

    return data

def query_all_bins_ever_accessed(run_id):
    max_generation = count_generations(run_id)
    sql = text(
            'select distinct (gas_adsorption_bin, surface_area_bin, ' +
            'void_fraction_bin) from materials where ' +
            'run_id=\'%s\';' % (run_id)
            )
    result = engine.execute(sql)
    bin_coordinates = []
    for row in result:
        bin_coordinates.append(row[0])

    return bin_coordinates

def query_all_mutation_strength_bins(run_id):
    max_generation = count_generations(run_id)
    sql = text(
            'select distinct (gas_adsorption_bin, surface_area_bin, ' +
            'void_fraction_bin) from mutation_strengths where ' +
            'run_id=\'%s\';' % (run_id)
            )
    result = engine.execute(sql)
    bin_coordinates = []
    for row in result:
        bin_coordinates.append(row[0])

    return bin_coordinates



def query_all_bin_counts(run_id):
    max_generation = count_generations(run_id)
    
    data = {}
    for generation in range(0, max_generation):
        sql = text(
                'select (gas_adsorption_bin, surface_area_bin, ' +
                'void_fraction_bin), count(uuid) from materials where ' +
                'run_id=\'%s\' and generation<=%s' % (run_id, generation) +
                'group by (gas_adsorption_bin, surface_area_bin, ' +
                'void_fraction_bin);'
                )
        result = engine.execute(sql)
        data['generation_%s' % generation] = {}
        data['generation_%s' % generation]['ga'] = []
        data['generation_%s' % generation]['sa'] = []
        data['generation_%s' % generation]['vf'] = []
        count = []
        for row in result:
            data['generation_%s' % generation]['ga'].append(int(row[0][1]))
            data['generation_%s' % generation]['sa'].append(int(row[0][3]))
            data['generation_%s' % generation]['vf'].append(int(row[0][5]))
            count.append(int(row[1]))
        data['generation_%s' % generation]['count'] = [i / max(count) for i in count]
        data['generation_%s' % generation]['min_count'] = min(count)
        data['generation_%s' % generation]['max_count'] = max(count)

        result.close()

    return data

def query_points_within_bin(run_id, bin_of_interest):
    max_generation = count_generations(run_id)

    sql = text(
            'select (ga0_absolute_volumetric_loading - ' +
            'ga1_absolute_volumetric_loading), sa_volumetric_surface_area, ' +
            'vf_helium_void_fraction from materials where ' +
            'run_id=\'%s\' and (gas_adsorption_bin, ' % run_id +
            'surface_area_bin, void_fraction_bin) = %s;' % bin_of_interest
            )
    data = {}
    data['ga'] = []
    data['sa'] = []
    data['vf'] = []
    result = engine.execute(sql)
    for row in result:
        data['ga'].append(row[0])
        data['sa'].append(row[1])
        data['vf'].append(row[2])
    result.close()

    return data

over_bins = [
            '(0,0,1)', '(0,0,2)', '(0,0,3)', '(0,0,4)', '(0,0,5)', 
            '(0,1,9)', '(1,0,3)', '(1,0,4)', '(1,1,4)', '(1,1,5)',
            '(1,2,4)', '(1,2,5)', '(1,2,9)', '(1,3,5)', '(1,3,9)',
            '(1,4,6)', '(1,4,8)', '(1,4,9)', '(1,5,7)', '(1,5,8)',
            '(1,5,9)', '(1,6,8)', '(1,6,9)', '(2,1,5)', '(2,2,5)',
            '(2,2,6)', '(2,2,7)', '(2,3,6)', '(2,4,6)', '(2,4,7)',
            '(2,5,7)', '(2,5,8)', '(2,6,8)', '(2,7,8)', '(2,7,9)',
            '(2,8,8)', '(3,3,6)', '(3,3,7)', '(3,4,7)', '(3,5,7)',
            '(3,6,8)', '(3,7,8)'
            ]

under_bins = [
            '(0,0,9)', '(0,2,9)', '(1,0,5)', '(1,1,3)', '(1,1,6)',
            '(1,1,9)', '(1,3,6)', '(1,4,5)', '(1,4,7)', '(1,5,6)',
            '(1,6,7)', '(1,7,8)', '(1,7,9)', '(2,1,4)', '(2,1,6)',
            '(2,3,5)', '(2,3,7)', '(2,5,6)', '(2,5,9)', '(2,6,7)',
            '(2,6,9)', '(2,8,9)', '(3,4,6)', '(3,4,8)', '(3,5,8)',
            '(3,6,7)', '(3,8,8)', '(4,4,7)', '(4,5,7)', '(4,5,8)',
            '(4,6,7)', '(4,6,8)', '(4,7,8)', '(4,6,7)', '(4,6,8)',
            '(4,7,8)'
            ]

def query_variance_no_flat_liners(run_id):
    max_generation = count_generations(run_id)

    data = {}
    for generation in range(max_generation):
        sql = text(
                'select (gas_adsorption_bin, surface_area_bin, ' +
                'void_fraction_bin), count(uuid) from materials where ' +
                'run_id=\'%s\' and generation_index <= 100 and ' % run_id +
                'retest_passed=True or retest_passed=NULL and ' +
                'generation<=%s group by (gas_adsorption_bin, ' % generation +
                'void_fraction_bin, surface_area_bin);'
                )
        data['generation_%s' % generation] = []
        result = engine.execute(sql)
        for row in result:
#            if row[0] in over_bins or row[0] in under_bins:
            data['generation_%s' % generation].append(row[1])
        result.close()

    max_count = max(data['generation_%s' % str(max_generation - 1)])

    variances = []
    for generation in range(max_generation):
        counts = data['generation_%s' % generation]
        normalised_counts = [i for i in counts]
        var = variance(normalised_counts)
        variances.append(var)

    return variances

#def query_variance_adding_zeroes(run_id):
#    max_generation = count_generations(run_id)
#
#    all_bins = []
#    sql = text(
#            'select (gas_adsorption_bin, surface_area_bin, void_fraction_bin)' +
#            ' from materials where run_id=\'%s\' and ' % run_id +
#            'generation=%s
#
#    data = {}
#    for generation in range(max_generation):
#        sql = text(
#                'select (gas_adsorption_bin, surface_area_bin, ' +
#                'void_fraction_bin), count(uuid) from materials where ' +
#                'run_id=\'%s\' and generation_index <= 100 and ' % run_id +
#                'generation=%s group by (gas_adsorption_bin, ' % generation +
#                'void_fraction_bin, surface_area_bin);'
#                )
#        data['generation_%s' % generation] = []
#        result = engine.execute(sql)
#        for row in result:
#            if row[0] in over_bins or row[0] in under_bins:
#                data['generation_%s' % generation].append(row[1])
#        result.close()
#
#    variances = []
#    for generation in range(max_generation):
#        counts = data['generation_%s' % generation]
#        normalised_counts = [i / max(counts) for i in counts]
#        var = variance(normalised_counts)
#        variances.append(var)
#
#    return variances

def query_mutation_strengths_in_bin(run_id, bin_of_interest):
    sql = text(
            'select generation, strength from mutation_strengths where ' +
            'run_id=\'%s\' and (gas_adsorption_bin, surface_area_bin, ' % run_id +
            'void_fraction_bin)=%s;' % bin_of_interest
            )
    generations = []
    strengths = []
    result = engine.execute(sql)
    for row in result:
        generations.append(int(row[0]))
        strengths.append(float(row[1]))
    return generations, strengths

def query_all_mutation_strengths(run_id):
    config = load_config_file(run_id)
    initial_mutation_strength = config['initial_mutation_strength']
    max_generation = count_generations(run_id)
    
    data = {}
    for generation in range(max_generation):
        print('{0} / {1}'.format(generation, max_generation))
        # find all bins accessed at generation
        bins = []
        sql = text(
                (
                    'select (gas_adsorption_bin, surface_area_bin, '
                    'void_fraction_bin) from materials where run_id=\'{0!s}\' '
                    'and generation<={1!s};'
                    ).format(run_id, generation)
                )
        result = engine.execute(sql)
        for row in result:
            bins.append(row[0])
        result.close()
        # find all mutation strengths for all accessed bins
        mutation_strengths = []
        for material_bin in bins:
            sql = text(
                    (
                        'select strength from mutation_strengths where '
                        'run_id=\'{0!s}\' and (gas_adsorption_bin, surface_area_bin, '
                        'void_fraction_bin)={1!s} and generation<={2!s} order by '
                        'generation desc limit 1;'
                        ).format(run_id, material_bin, generation)
                    )
            result = engine.execute(sql)
            rows_amount = 0
            for row in result:
                rows_amount += 1
                mutation_strengths.append(row[0])
            if rows_amount == 0:
                mutation_strengths.append(initial_mutation_strength)
            result.close()
        data['generation_{0!s}'.format(generation)] = []
        for i in range(len(bins)):
            bin_data = {
                    'ga' : int(bins[i][1]),
                    'sa' : int(bins[i][3]),
                    'vf' : int(bins[i][5]),
                    'strength' : mutation_strengths[i]
                    }
            data['generation_{0!s}'.format(generation)].append(bin_data)

    print(data)
    return data
