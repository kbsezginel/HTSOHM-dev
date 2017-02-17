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
