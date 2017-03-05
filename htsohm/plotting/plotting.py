import os

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.patches as patches
import numpy as np
from sqlalchemy import *
from statistics import median

from htsohm.utilities import *
from htsohm.plotting.plotting_utilities import *
from htsohm.db.queries import *
from htsohm.db.__init__ import engine


def plot_points(
        x, y, z_bin,
        run_id, gen,
        config, ax, z_bins, generations,
        labels = None,
        children = 'off',
        parents = 'off',
        top_bins = None
    ):
    """Create scatterplot 'x' v. 'y' either by plotting a z-axis slice,
        or all slices at once.

    Args:
        x (str): `ML`, `SA`, `VF`
        y (str): `ML`, `SA`, `VF`
        z_bin (int): None(default), [0, number_of_bins]
        run_id (str): run identification string
        gen (int): [0, number_of_generations]
        config (yaml.load): use `data_vu.files.load_config_file`
        ax : plt.subplot(111)
        labels (str): None(default), `first_only`, `all`
        highlight_children (str): `on`(default), `off`
        highlight_parents (str): `on`, `off`(default)
        pick_parents (str): `on`, `off`(default)

    Returns:
        None

    """
    x_limits = get_limits(x, config)
    y_limits = get_limits(y, config)
    plt.xlim(x_limits)
    plt.ylim(y_limits)

    # add labels, as necessary
    labeling(labels, ax, config)

    # plot data points for all generations
    for i in range(gen):
        x_ = query_points(x, z_bin, run_id, i)
        y_ = query_points(y, z_bin, run_id, i)
        plt.scatter(
            x_, y_,
            marker='o', 
            facecolors='k',
            edgecolors='none',
            alpha=0.5, s=2
        )

    # highlight most recent generation
    highlight_children(x, y, z_bin, run_id, gen, children, 'DataPoints')
    # highlight parents
    if parents == 'on':
        hightlight_parents(x, y, z_bin, run_id, gen, 'DataPoints')
    # highlight most populated bins
    highlight_top_bins(x, y, z_bin, run_id, gen, top_bins)

def plot_bin_counts(
        x, y, z_bin,
        run_id, gen,
        config, ax,
        z_bins, generations,
        labels = None,
        parents='off'
    ):
    """Create bin-plot 'x' v. 'y' either by plotting a z-axis slice,
        or all slices at once. Bins are coloured by bin-count.

    Args:
        x (str): `ML`, `SA`, `VF`
        y (str): `ML`, `SA`, `VF`
        z_bin (int): None(default), [0, number_of_bins]
        run_id (str): run identification string
        gen (int): [0, number_of_generations]
        config (yaml.load): use `data_vu.files.load_config_file`
        ax : plt.subplot(111)
        labels (str): None(default), `first_only`, `all`
        highlight_children (str): `on`(default), `off`
        highlight_parents (str): `on`, `off`(default)

    Returns:
        None

    """
    x_limits = get_limits(x, config)
    y_limits = get_limits(y, config)
    plt.xlim(x_limits)
    plt.ylim(y_limits)

    # add labels, as necessary
    labeling(labels, ax, config)

    # bin materials
    x_, y_, c_ = query_bin_counts(x, y, z_bin, run_id, gen)

    # normalise bin-counts
    norm_c = [i / max(c_) for i in c_]
#    print('norm_c :\t%s' % norm_c)

    for i in range(len(x_)):
#        print(x_[i], y_[i])
        add_square(
                x, y,
                x_[i], y_[i],               # bin (x, y)
                cm.brg(norm_c[i]), None,     # square colour, edge colour
                ax, config
        )

    # highlight parents
    if parents == 'on':
        hightlight_parents(x, y, z_bin, run_id, gen, 'BinCounts')

def plot_mutation_strengths(
        x, y, z_bin,
        run_id, gen,
        config, ax, z_bins, generations,
        labels = None,
        highlight_children='off',
        highlight_parents='off'
    ):
    """Create bin-plot 'x' v. 'y' either by plotting a z-axis slice,
        or all slices at once. Bins are coloured by mutation strength.

    Args:
        x (str): `ML`, `SA`, `VF`
        y (str): `ML`, `SA`, `VF`
        z_bin (int): None(default), [0, number_of_bins]
        run_id (str): run identification string
        gen (int): [0, number_of_generations]
        config (yaml.load): use `data_vu.files.load_config_file`
        ax : plt.subplot(111)
        labels (str): None(default), `first_only`, `all`
        highlight_children (str): `on`(default), `off`
        highlight_parents (str): `on`, `off`(default)

    Returns:
        None

    """
    x_limits = get_limits(x, config)
    y_limits = get_limits(y, config)
    plt.xlim(x_limits)
    plt.ylim(y_limits)

    # add labels, as necessary
    labeling(labels, ax, config)

    print('about to query...')
    values = query_mutation_strength(x, y, z_bin, run_id, gen)
    print('...values :\t%s' % values)
    for i in values:
        color = cm.Reds( i[2] )
        add_square(
            x, y,
            i[0], i[1],
            color,
            None,
            ax, config
        )

#    result = engine.execute(get_all_bins(x, y, z_bin, run_id, gen))
#    bins = []
#    for row in result:
#        line = [row[0], row[1]]
#        if line not in bins:
#            print(line)
#            bins.append(line)
#    result.close()
#    for b in bins:
#        add_square(
#            x, y,
#            b[0], b[1],
#            'k',
#            ax, config,
#            4
#        )

    if highlight_parents == 'on':
        if gen != 0:
            values = query_parents(
                x[:2] + '_bin',
                y[:2] + '_bin',
                z_bin,
                run_id, gen)
            for i in values:
                add_square(
                    x, y,
                    i[0][0], i[0][1],
                    'none',
                    'y',
                    ax, config,
                    2
                )

    if highlight_children == 'on':
        result = engine.execute( query_child_bins(
            x[:2] + '_bin', y[:2] + '_bin', z_bin, run_id, gen)) 
        for row in result:
            add_square(
                x, y,
                row[0], row[1],
                'none',
                'r',
                ax, config,
                1, ':'
            )

def plot_convergence(run0,  generations):
    fig = plt.figure(figsize = (6, 4))
    plt.tick_params(axis='both', which='both', labelbottom='off', labelleft='off')
    conv0 = [evaluate_convergence(run0, int(i)) for i in np.arange(0, generations, 100)]
    print('conv0 :\t%s' % conv0)
#    conv1 = [evaluate_convergence(run1, i) for i in range(generations)]
#    conv2 = [evaluate_convergence(run2, i) for i in range(generations)]
    plt.scatter(np.arange(0, generations, 100), conv0,
            marker='o', facecolors='k', edgecolors='none', alpha=1)
#    plt.scatter(range(generations), conv1,
#            marker='o', facecolors='g', edgecolors='none', alpha=0.5)
#    plt.scatter(range(generations), conv2,
#            marker='o', facecolors='b', edgecolors='none', alpha=0.5)
    plt.xlim(0, generations)
    y_lim = 0.1 # 1.1 * max([max(conv0), max(conv1), max(conv2)])
    plt.ylim(0, y_lim)
    print('ylim\t%s' % y_lim)
    plt.savefig(
        'CH4Convergence_%sgens.png' % generations,
#        '%s_convergence_%sgens.png' % (run_id, generations),
        bbox_inches = 'tight',
        pad_inches = 0,
        dpi = 96 * 8,
        transparent = True
    )
    plt.cla()
    plt.close(fig)
    print('...done!')

def plot_bin_bars(run_id, gen0, gen1):
    fig = plt.figure(figsize = (6, 4))
    plt.tick_params(axis='both', which='both', labelbottom='off', labelleft='off')
    c0 = query_all_counts(run_id, gen0)[2:]
    c0_ = [i / max(c0) for i in c0]
    c1 = query_all_counts(run_id, gen1)[2:]
    c1_ = [i / max(c1) for i in c1]
    width = 1
    plt.bar(range(len(c0)), c0_, width, color='black')
    plt.bar(range(len(c1)), c1_, width, color='red')
    plt.savefig(
            '%s_CompareGens_%s_%s_NOONE.png' % (run_id, gen0, gen1),
            transparent = True,
            bbox_inches = 'tight',
            pad_inches = 0
    )

def plot_bin_search(x_type, y_type, x, y, ax, config):
    new_bins = ['%s,%s' % (x[i], y[i]) for i in range(len(x))]
    filtered_bins = []
    counts = []
    for i in new_bins:
        if i not in filtered_bins:
            filtered_bins.append(i)
            counts.append(new_bins.count(i))
    counts = [i / float(max(counts)) for i in counts]

    for i in range(len(filtered_bins)):
        ax.add_patch(
                patches.Rectangle(
                    (
                        int(filtered_bins[i][0]),
                        int(filtered_bins[i][2])
                        ),
                    1, 1,
                    facecolor=cm.Reds(counts[i]), edgecolor=None
                    )
                )

def plot_child_and_parent_bins(run_id):
    number_of_generations = count_generations(run_id)
    parent_data = query_all_parent_bins(run_id)
    child_data = query_all_child_bins(run_id)

    number_of_bins = load_config_file(run_id)['number_of_convergence_bins']

##    column = 0
##    columns = number_of_generations
##    rows = number_of_bins
    for generation in range(1, number_of_generations):
##        column += 1
        fig = plt.figure(figsize=(12, 20))
        print('plot %s / %s ...' % (generation, number_of_generations))
        p        = parent_data['generation_%s' % generation]
        p_ga     = p['ga']
        p_sa     = p['sa']
        p_vf     = p['vf']
        p_count  = p['count']
        c        = child_data['generation_%s' % generation]
        c_ga     = c['ga']
        c_sa     = c['sa']
        c_vf     = c['vf']
        c_count  = c['count']

        # vf v. sa
        #######################################################################

        # parent
        for i in range(number_of_bins):
            ax0 = plt.subplot(number_of_bins, 6, 1 + i * 6)
            plt.xlim(0, 10)
            plt.ylim(0, 10)
            for j in range(len(p_ga)):
                if p_ga[j] == i:
                    ax0.add_patch(
                            patches.Rectangle(
                                (p_vf[j], p_sa[j]),
                                1, 1,
                                facecolor=cm.Reds(p_count[j])
                                )
                            )
        # child
            ax1 = plt.subplot(number_of_bins, 6, 1 + i * 6 + 1)
            plt.xlim(0, 10)
            plt.ylim(0, 10)
            c = 0
            for j in range(len(c_ga)):
                if c_ga[j] == i:
                    c += 1
                    ax1.add_patch(
                            patches.Rectangle(
                                (c_vf[j], c_sa[j]),
                                1, 1,
                                facecolor=cm.Reds(c_count[j])
                                )
                            )

        # vf v. ga
        #######################################################################

        # parent
        for i in range(number_of_bins):
            ax0 = plt.subplot(number_of_bins, 6, 1 + i * 6 + 2)
            plt.xlim(0, 10)
            plt.ylim(0, 10)
            for j in range(len(p_ga)):
                if p_sa[j] == i:
                    ax0.add_patch(
                            patches.Rectangle(
                                (p_vf[j], p_ga[j]),
                                1, 1,
                                facecolor=cm.Reds(p_count[j])
                                )
                            )
        # child
            ax1 = plt.subplot(number_of_bins, 6, 1 + i * 6 + 3)
            plt.xlim(0, 10)
            plt.ylim(0, 10)
            c = 0
            for j in range(len(c_ga)):
                if c_sa[j] == i:
                    c += 1
                    ax1.add_patch(
                            patches.Rectangle(
                                (c_vf[j], c_ga[j]),
                                1, 1,
                                facecolor=cm.Reds(c_count[j])
                                )
                            )
 
        # sa v. ga
        #######################################################################

        # parent
        for i in range(number_of_bins):
            ax0 = plt.subplot(number_of_bins, 6, 1 + i * 6 + 4)
            plt.xlim(0, 10)
            plt.ylim(0, 10)
            for j in range(len(p_ga)):
                if p_vf[j] == i:
                    ax0.add_patch(
                            patches.Rectangle(
                                (p_sa[j], p_ga[j]),
                                1, 1,
                                facecolor=cm.Reds(p_count[j])
                                )
                            )
        # child
            ax1 = plt.subplot(number_of_bins, 6, 1 + i * 6 + 5)
            plt.xlim(0, 10)
            plt.ylim(0, 10)
            c = 0
            for j in range(len(c_ga)):
                if c_vf[j] == i:
                    c += 1
                    ax1.add_patch(
                            patches.Rectangle(
                                (c_sa[j], c_ga[j]),
                                1, 1,
                                facecolor=cm.Reds(c_count[j])
                                )
                            )
 

        plt.savefig(
                '%s_%s_DatL0ud.png' % (run_id, generation),
                transparent = True
        )
        plt.close(fig)

                   
                    
                    
                    
                    
                    ##        for z_bin in range(number_of_bins):
##            row = z_bin + 1
##
##        # parents, vf v sa
##        ax = plt.subplot(rows, columns, (row - 1) * columns + column)

#        for i in range(len(p_ga)):
#            ax.add_path(
#                    patches.Rectangle(
#                        (p_vf[i], p_sa[i]),
#                        1, 1,
#                        facecolor=cm.Reds(p_counts[i])
#                        )
#                    )
#        p_ax = plt.subplot(2, 3, 2)
#        for i in range(len(p_ga)):
#            ax.add_path(
#                    patches.Rectangle(
#                        (p_vf[i], p_ga[i]),
#                        1, 1,
#                        facecolor=cm.Reds(p_counts[i])
#                        )
#                    )
#        p_ax = plt.subplot(2, 3, 1)
#        for i in range(len(p_ga)):
#            ax.add_path(
#                    patches.Rectangle(
#                        (p_vf[i], p_sa[i]),
#                        1, 1,
#                        facecolor=cm.Reds(p_counts[i])
#                        )
#                    )
#

#
#
#        children = parent_data[generation]
#
#        fig.close()

def plot_parent_search(run_id):
    fig = plt.figure(figsize = (12, 4))
    number_of_bins = load_config_file(run_id)['number_of_convergence_bins']
    config = load_config_file(run_id)

    # child bin
    most_populous_bin = query_most_populous_bin(run_id)
    ga_child = int(most_populous_bin[1])
    sa_child = int(most_populous_bin[3])
    vf_child = int(most_populous_bin[5])

    # parent bins
    parent_bins = parent_search(run_id)
    ga = []
    sa = []
    vf = []
    for parent_bin in parent_bins:
        ga.append(int(parent_bin[1]))
        sa.append(int(parent_bin[3]))
        vf.append(int(parent_bin[5]))

    # vf v sa
    print(vf_child, sa_child)
    ax0 = plt.subplot(1, 3, 1)
    plt.xlabel('void fraction')
    plt.ylabel('surface area')
    plt.xlim(0,10)
    plt.ylim(0,10)
    plot_bin_search('vf', 'sa', vf, sa, ax0, config)
    ax0.add_patch(
        patches.Rectangle(
            (vf_child, sa_child),
            1, 1,
            facecolor='none', edgecolor='b', linewidth=2
            )
        )

    # vf v ga
    ax1 = plt.subplot(1, 3, 2)
    plt.xlabel('void fraction')
    plt.ylabel('gas adsorption')
    plt.xlim(0,10)
    plt.ylim(0,10)
    plot_bin_search('vf', 'ga', vf, ga, ax1, config)
    ax1.add_patch(
        patches.Rectangle(
            (vf_child, ga_child),
            1, 1,
            facecolor='none', edgecolor='b', linewidth=2
            )
        )
 
    # sa v ga
    ax2 = plt.subplot(1, 3, 3)
    plt.xlabel('surface area')
    plt.ylabel('gas adsorption')
    plt.xlim(0,10)
    plt.ylim(0,10)
    plot_bin_search('sa', 'ga', sa, ga, ax2, config)
    ax2.add_patch(
        patches.Rectangle(
            (sa_child, ga_child),
            1, 1,
            facecolor='none', edgecolor='b', linewidth=2
            )
        )

    plt.savefig(
            '%s_ParentSearch.png' % run_id,
            transparent = True
    )


def plot_population_over_time(run_id, bin_of_interest, generations):

    print('querying counts from one bin...')
    counts = query_population_over_time(run_id, bin_of_interest, generations)
    print('plotting...')
    plt.plot(range(len(counts)), counts, '-r')

    print('querying average bin-counts...')
    average_counts = []
    for i in range(generations):
        print('%s / %s' % (i, generations))
        average_counts.append(query_average_bin_count(run_id, i))
    print('plotting...')

    plt.plot(range(len(average_counts)), average_counts, '-k')

    plt.savefig(
            '%s_%s_%s_BCvG.png' % (run_id, bin_of_interest, generations), 
            transparent=True)
