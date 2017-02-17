import os

import matplotlib.pyplot as plt

from htsohm.utilities import *
from htsohm.db.__init__ import materials, mutation_strengths
from htsohm.db.queries import *
from htsohm.plotting.plotting import *

def plot_HTSOHM(
        run_id,
        generations,
        z_bins,
        data_types,
        axes = [
            ['vf', 'sa'],
            ['vf', 'ga'],
            ['sa', 'ga']
        ],
        labels = 'off',
        parents = 'off',
        children = 'on',
        top_bins = None
    ):
    """Creates subplot figures for different axes and data-types.

    Args:
        run_id (str): run identification string.
        generations (str, int, <class 'list'>): `all`, [0, 1, 2, ...], etc.
        z_bins (str, int, <class 'list'>): `all`, None, [0, 1, 2, ...], etc.
        data_types (str, <class 'list'>): `all`, `DataPoints`, `BinCounts`,
            `MutationStrengths`, or list of these.
        axes (<class 'list'>): ex. [['vf', 'sa'], ['vf', 'ga'], ['sa', 'ga']]
        labels (str): `first_only`(default), `all`, None.
        parents (str): `on`(default), `off`.
        children (str): `on`(default), `off`.
        top_bins (str): `on`(default), `off`.

    Returns:
        None

    """
    config = load_config_file(run_id)

    if generations == 'all':
        generations = [ i for i in range( count_generations(run_id) ) ]
    if z_bins == 'all':
        z_bins = [ i for i in range( config['number_of_convergence_bins'] ) ]
    if data_types == 'all':
        data_types = ['DataPoints', 'BinCounts', 'MutationStrengths']
    if axes == 'all':
        axes = [
            ['vf', 'sa'],
            ['vf', 'ga'],
            ['sa', 'ga']
        ]

    generations = make_list(generations)
    z_bins = make_list(z_bins)
    data_types = make_list(data_types)
    axes = make_list(axes)

    for data_type in data_types:
        print('Plotting %s...' % data_type)

        for [x, y] in axes:
            print('\t%s v %s' % (x, y))

            fig = plt.figure(
                figsize = ( 2 * len(generations), 2 * len(z_bins) )
            )
#            fig_title = '%s\n' % run_id + \
#                'gen. %s thru %s\n' % (generations[0], generations[-1]) + \
#                'bin %s thru %s' % (z_bins[0], z_bins[-1])
#            fig.suptitle(fig_title)

            column = 0
            for generation in generations:
                print('\t\tgeneration:\t%s' % generation)

                column += 1
                for z_bin in z_bins:
                    print('\t\t\tz_bin:\t%s' % z_bin)

                    rows = len(z_bins)
                    row = z_bins.index(z_bin) + 1
                    if z_bins == None or len(z_bins) == 1:
                        row = rows = 1

                    columns = len(generations)
#                    column = generations.index(generation) + 1
                    if len(generations) == 1:
                        column = columns = 1

                    ax = plt.subplot(
                        rows,
                        columns,
                        (row - 1) * columns + column
                    )
                    
                    if data_type == 'DataPoints':
                        plot_points(
                            x, y, z_bin,
                            run_id, generation,
                            config, ax, z_bins, generations,
                            labels, children, parents, top_bins
                        )

                    elif data_type == 'BinCounts':
                        BC_x = x + '_bin'
                        BC_y = y + '_bin'
                        plot_bin_counts(
                            BC_x, BC_y, z_bin,
                            run_id, generation,
                            config, ax, z_bins, generations,
                            labels,
                            parents
                        )

                    elif data_type == 'MutationStrengths':
                        MS_x = x + '_mutation_strength'
                        MS_y = y + '_mutation_strength'
                        plot_mutation_strengths(
                            MS_x, MS_y, z_bin,
                            run_id, generation,
                            config, ax, z_bins, generations,
                            labels
#                            highlight_children,
#                            highlight_parents
                        )

            plt.savefig(
                '%s_%s_%s_%s_' % (run_id, x, y, data_type) +
                    'bins%sto%s_' % (z_bins[0], z_bins[-1]) +
                    'gens%sto%s.png' % (generations[0], generations[-1]),
                bbox_inches = 'tight',
                pad_inches = 0,
                dpi = 96 * 4,
                transparent = True
            )
            plt.cla()
            plt.close(fig)
    print('...done!')
