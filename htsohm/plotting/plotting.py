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

