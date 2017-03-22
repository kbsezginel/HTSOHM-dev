import os

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.patches as patches
import matplotlib.gridspec as gridspec
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

over_bins = [
        '(0,0,2)', '(0,0,3)', '(0,0,9)', '(0,1,9)', '(1,0,4)', '(1,1,4)',
        '(1,1,5)', '(1,1,9)', '(1,2,5)', '(1,2,9)', '(1,3,9)', '(1,4,8)',
        '(1,4,9)', '(1,5,7)', '(1,5,8)', '(1,5,9)', '(1,6,8)', '(2,2,5)',
        '(2,2,6)', '(2,3,6)', '(2,4,6)', '(2,4,7)', '(2,5,7)', '(2,6,8)',
        '(3,4,7)'
        ]

average_bins = [
        '(0,0,1)', '(0,0,4)', '(1,0,3)', '(1,0,5)', '(1,2,4)', '(1,3,5)',
        '(1,4,6)', '(1,5,6)', '(1,6,7)', '(1,6,9)', '(2,1,5)', '(2,1,6)',
        '(2,3,5)', '(2,5,8)', '(2,6,7)', '(2,7,8)', '(3,3,6)', '(3,3,7)'
        ]

under_bins = [
        '(0,0,5)', '(0,2,9)', '(1,1,3)', '(1,1,6)', '(1,3,6)', '(1,4,7)',
        '(1,7,8)', '(2,1,4)', '(2,3,7)', '(2,5,6)', '(3,4,6)', '(3,5,7)',
        '(3,5,8)', '(3,6,7)', '(3,6,8)'
        ]

def plot_all_mutation_strengths(run_id):
    number_of_generations = count_generations(run_id)
    data = query_all_mutation_strengths(run_id)

    number_of_bins = load_config_file(run_id)['number_of_convergence_bins']

    for generation in range(number_of_generations):
        fig = plt.figure(figsize=(12, 41))
        G = gridspec.GridSpec(41,12)

        print('plot %s / %s ...' % (generation, number_of_generations))
        all_data        = data['generation_%s' % generation]
        # vf v. sa
        #######################################################################

        for i in range(number_of_bins):
            ax0 = plt.subplot2grid((41,12), (i * 4, 0), colspan=4, rowspan=4)
            plt.xlim(0, 10)
            plt.ylim(0, 10)

            for d in all_data:
                if d['ga'] == i:
                    current_bin = '({0},{1},{2})'.format(
                            d['ga'], d['sa'], d['vf'])
                    if current_bin in over_bins:
                        edge_color = 'r'
                    elif current_bin in under_bins:
                        edge_color = 'b'
                    elif current_bin in average_bins:
                        edge_color = 'g'
                    else:
                        edge_color = 'w'
                    ax0.add_patch(
                            patches.Rectangle(
                                (d['vf'], d['sa']),
                                1, 1,
                                facecolor=cm.Reds(d['strength']),
                                edgecolor=edge_color
                                )
                            )

        # colorbar
        ax1 = plt.subplot2grid((41,12), (40,0), colspan=12)
        cmap = mpl.cm.Reds
        norm = mpl.colors.Normalize(vmin=0, vmax=0)
        cb1 = mpl.colorbar.ColorbarBase(
                ax1, cmap=cmap,
                norm=norm,
                orientation='horizontal',
                )
        #cb1.set_label('bin-counts')

        # vf v. ga
        #######################################################################

        for i in range(number_of_bins):
            ax0 = plt.subplot2grid((41, 12), (i * 4, 4), rowspan=4, colspan=4)
            plt.xlim(0, 10)
            plt.ylim(0, 10)
            for d in all_data:
                if d['sa'] == i:
                    current_bin = '({0},{1},{2})'.format(
                            d['ga'], d['sa'], d['vf'])
                    if current_bin in over_bins:
                        edge_color = 'r'
                    elif current_bin in under_bins:
                        edge_color = 'b'
                    elif current_bin in average_bins:
                        edge_color = 'g'
                    else:
                        edge_color = 'w'
                    ax0.add_patch(
                            patches.Rectangle(
                                (d['vf'], d['ga']),
                                1, 1,
                                facecolor=cm.Reds(d['strength']),
                                edgecolor=edge_color
                                )
                            )


        # sa v. ga
        #######################################################################

        for i in range(number_of_bins):
            ax0 = plt.subplot2grid((41, 12), (i * 4, 8), rowspan=4, colspan=4)
            plt.xlim(0, 10)
            plt.ylim(0, 10)
            for d in all_data:
                if d['vf'] == i:
                    current_bin = '({0},{1},{2})'.format(
                            d['ga'], d['sa'], d['vf'])
                    if current_bin in over_bins:
                        edge_color = 'r'
                    elif current_bin in under_bins:
                        edge_color = 'b'
                    elif current_bin in average_bins:
                        edge_color = 'g'
                    else:
                        edge_color = 'w'
                    ax0.add_patch(
                            patches.Rectangle(
                                (d['sa'], d['ga']),
                                1, 1,
                                facecolor=cm.Reds(d['strength']),
                                edgecolor=edge_color
                                )
                            )


        
        plt.tight_layout()
        plt.savefig(
                '%s_%s_MutationStrengths.png' % (run_id, generation),
                transparent = True
        )
        plt.close(fig)


def plot_all_bin_counts(run_id):
    number_of_generations = count_generations(run_id)
    data = query_all_bin_counts(run_id)

    number_of_bins = load_config_file(run_id)['number_of_convergence_bins']

    for generation in range(number_of_generations):
        fig = plt.figure(figsize=(12, 41))
        G = gridspec.GridSpec(41,12)

        print('plot %s / %s ...' % (generation, number_of_generations))
        d        = data['generation_%s' % generation]
        d_ga     = d['ga']
        d_sa     = d['sa']
        d_vf     = d['vf']
        d_count  = d['count']
       
        # vf v. sa
        #######################################################################

        for i in range(number_of_bins):
            ax0 = plt.subplot2grid((41,12), (i * 4, 0), colspan=4, rowspan=4)
            plt.xlim(0, 10)
            plt.ylim(0, 10)
            for j in range(len(d_ga)):
                if d_ga[j] == i:
                    current_bin = '(%s,%s,%s)' % (d_ga[j], d_sa[j], d_vf[j])
                    if current_bin in over_bins:
                        edge_color = 'r'
                    elif current_bin in under_bins:
                        edge_color = 'b'
                    elif current_bin in average_bins:
                        edge_color = 'g'
                    else:
                        edge_color = 'w'

                    ax0.add_patch(
                            patches.Rectangle(
                                (d_vf[j], d_sa[j]),
                                1, 1,
                                facecolor=cm.Reds(d_count[j]),
                                edgecolor=edge_color
                                )
                            )

        # colorbar
        ax1 = plt.subplot2grid((41,12), (40,0), colspan=12)
        cmap = mpl.cm.Reds
        norm = mpl.colors.Normalize(vmin=d['min_count'], vmax=d['max_count'])
        cb1 = mpl.colorbar.ColorbarBase(
                ax1, cmap=cmap,
                norm=norm,
                orientation='horizontal',
                ticks=[d['min_count'], d['max_count']]
                )
        #cb1.set_label('bin-counts')

        # vf v. ga
        #######################################################################

        for i in range(number_of_bins):
            ax0 = plt.subplot2grid((41, 12), (i * 4, 4), rowspan=4, colspan=4)
            plt.xlim(0, 10)
            plt.ylim(0, 10)
            for j in range(len(d_sa)):
                if d_sa[j] == i:
                    current_bin = '(%s,%s,%s)' % (d_ga[j], d_sa[j], d_vf[j])
                    if current_bin in over_bins:
                        edge_color = 'r'
                    elif current_bin in under_bins:
                        edge_color = 'b'
                    elif current_bin in average_bins:
                        edge_color = 'g'
                    else:
                        edge_color = 'w'

                    ax0.add_patch(
                            patches.Rectangle(
                                (d_vf[j], d_ga[j]),
                                1, 1,
                                facecolor=cm.Reds(d_count[j]),
                                edgecolor=edge_color
                                )
                            )

        # sa v. ga
        #######################################################################

        for i in range(number_of_bins):
            ax0 = plt.subplot2grid((41, 12), (i * 4, 8), rowspan=4, colspan=4)
            plt.xlim(0, 10)
            plt.ylim(0, 10)
            for j in range(len(d_vf)):
                if d_vf[j] == i:
                    current_bin = '(%s,%s,%s)' % (d_ga[j], d_sa[j], d_vf[j])
                    if current_bin in over_bins:
                        edge_color = 'r'
                    elif current_bin in under_bins:
                        edge_color = 'b'
                    elif current_bin in average_bins:
                        edge_color = 'g'
                    else:
                        edge_color = 'w'

                    ax0.add_patch(
                            patches.Rectangle(
                                (d_sa[j], d_ga[j]),
                                1, 1,
                                facecolor=cm.Reds(d_count[j]),
                                edgecolor=edge_color
                                )
                            )

        plt.tight_layout()
        plt.savefig(
                '%s_%s_AllBinCounts.png' % (run_id, generation),
                transparent = True
        )
        plt.close(fig)



def plot_child_and_parent_bins(run_id):
    number_of_generations = count_generations(run_id)
    parent_data = query_all_parent_bins(run_id)
    child_data = query_all_child_bins(run_id)

    number_of_bins = load_config_file(run_id)['number_of_convergence_bins']

    for generation in range(770, number_of_generations):
        fig = plt.figure(figsize=(30,40))
        G = gridspec.GridSpec(40,30)
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
            ax0 = plt.subplot2grid((40,30), (i * 4, 0), rowspan=4, colspan=4)
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
            ax1 = plt.subplot2grid((40,30), (i * 4, 5), rowspan=4, colspan=4)
            plt.xlim(0, 10)
            plt.ylim(0, 10)
            for j in range(len(c_ga)):
                if c_ga[j] == i:
                    ax1.add_patch(
                            patches.Rectangle(
                                (c_vf[j], c_sa[j]),
                                1, 1,
                                facecolor=cm.Reds(c_count[j])
                                )
                            )

        ax2 = plt.subplot2grid((40,30), (0,4), rowspan=8)
        cmap = mpl.cm.Reds
        norm = mpl.colors.Normalize(vmin=p['min_count'], vmax=p['max_count'])
        cb2 = mpl.colorbar.ColorbarBase(
                ax2, cmap=cmap,
                norm=norm,
                orientation='vertical',
                ticks=[p['min_count'], p['max_count']]
                )
        ax3 = plt.subplot2grid((40,30), (0,9), rowspan=8)
        norm = mpl.colors.Normalize(vmin=c['min_count'], vmax=c['max_count'])
        cb3 = mpl.colorbar.ColorbarBase(
                ax3, cmap=cmap,
                norm=norm,
                orientation='vertical',
                ticks=[c['min_count'], c['max_count']]
                )
         
        # vf v. ga
        #######################################################################

        # parent
        for i in range(number_of_bins):
            ax0 = plt.subplot2grid((40,30), (i * 4, 10), rowspan=4, colspan=4)
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
            ax1 = plt.subplot2grid((40,30), (i * 4, 15), rowspan=4, colspan=4)
            plt.xlim(0, 10)
            plt.ylim(0, 10)
            for j in range(len(c_ga)):
                if c_sa[j] == i:
                    ax1.add_patch(
                            patches.Rectangle(
                                (c_vf[j], c_ga[j]),
                                1, 1,
                                facecolor=cm.Reds(c_count[j])
                                )
                            )

        ax2 = plt.subplot2grid((40,30), (0,14), rowspan=8)
        cmap = mpl.cm.Reds
        norm = mpl.colors.Normalize(vmin=p['min_count'], vmax=p['max_count'])
        cb2 = mpl.colorbar.ColorbarBase(
                ax2, cmap=cmap,
                norm=norm,
                orientation='vertical',
                ticks=[p['min_count'], p['max_count']]
                )
        ax3 = plt.subplot2grid((40,30), (0,19), rowspan=8)
        norm = mpl.colors.Normalize(vmin=c['min_count'], vmax=c['max_count'])
        cb3 = mpl.colorbar.ColorbarBase(
                ax3, cmap=cmap,
                norm=norm,
                orientation='vertical',
                ticks=[c['min_count'], c['max_count']]
                )

        # sa v. ga
        #######################################################################

        # parent
        for i in range(number_of_bins):
            ax0 = plt.subplot2grid((40,30), (i * 4, 20), rowspan=4, colspan=4)
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
            ax1 = plt.subplot2grid((40,30), (i * 4, 25), rowspan=4, colspan=4)
            plt.xlim(0, 10)
            plt.ylim(0, 10)
            for j in range(len(c_ga)):
                if c_vf[j] == i:
                    ax1.add_patch(
                            patches.Rectangle(
                                (c_sa[j], c_ga[j]),
                                1, 1,
                                facecolor=cm.Reds(c_count[j])
                                )
                            )
        ax2 = plt.subplot2grid((40,30), (0,24), rowspan=8)
        cmap = mpl.cm.Reds
        norm = mpl.colors.Normalize(vmin=p['min_count'], vmax=p['max_count'])
        cb2 = mpl.colorbar.ColorbarBase(
                ax2, cmap=cmap,
                norm=norm,
                orientation='vertical',
                ticks=[p['min_count'], p['max_count']]
                )
        ax3 = plt.subplot2grid((40,30), (0,29), rowspan=8)
        norm = mpl.colors.Normalize(vmin=c['min_count'], vmax=c['max_count'])
        cb3 = mpl.colorbar.ColorbarBase(
                ax3, cmap=cmap,
                norm=norm,
                orientation='vertical',
                ticks=[c['min_count'], c['max_count']]
                )

        plt.tight_layout()
        plt.savefig(
#                '%s_%s_ParentBins_ChildBins.png' % (run_id, generation),
                '%s_%s_ParentBins_AllBins.png' % (run_id, generation),
                transparent = True
        )
        plt.close(fig)

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
    fig = plt.figure()
    print('querying counts from one bin...')
    counts = query_population_over_time(run_id, bin_of_interest, generations)
    print('plotting...')
    plt.plot(range(len(counts)), counts, '-r')

    print('querying average bin-counts...')
    average_counts = []
    for i in range(generations):
#        print('%s / %s' % (i, generations))
        average_counts.append(query_average_bin_count(run_id, i))
    print('plotting...')

    plt.plot(range(len(average_counts)), average_counts, '-k')

    plt.savefig(
            '%s_%s_BCvG.png' % (bin_of_interest, generations), 
            transparent=True)
    plt.close(fig)

def plot_all_bin_populations_over_time(run_id):
    generations = count_generations(run_id)
    number_of_bins = load_config_file(run_id)['number_of_convergence_bins']

    all_accessed_bins = query_all_bins_ever_accessed(run_id)

    for ga in range(number_of_bins):
        for sa in range(number_of_bins):
            for vf in range(number_of_bins):
                bin_of_interest = '(%s,%s,%s)' % (ga, sa, vf)
                if bin_of_interest in all_accessed_bins:
                    print(bin_of_interest)
                    plot_population_over_time(run_id, bin_of_interest, generations)

def plot_all_points_within_bin(run_id, bin_of_interest):
    config = load_config_file(run_id)
    number_of_bins = config['number_of_convergence_bins']
    ga_limits = config['gas_adsorption_0']['limits']
    sa_limits = config['surface_area']['limits']
    vf_limits = config['helium_void_fraction']['limits']

    fig = plt.figure(figsize=(12, 4))

    data = query_points_within_bin(run_id, bin_of_interest)
    ga = data['ga']
    sa = data['sa']
    vf = data['vf']

    ga_bin = int(bin_of_interest[1])
    sa_bin = int(bin_of_interest[3])
    vf_bin = int(bin_of_interest[5])
    ga_width = ga_limits[1] / float(number_of_bins)
    sa_width = sa_limits[1] / float(number_of_bins)
    vf_width = vf_limits[1] / float(number_of_bins)
    ga_min = ga_bin * ga_width
    sa_min = sa_bin * sa_width
    vf_min = vf_bin * vf_width
    ga_max = ga_min + ga_width
    sa_max = sa_min + sa_width
    vf_max = vf_min + vf_width

    # vf v. sa
    ax0 = plt.subplot(131)
    plt.xlim(vf_min, vf_max)
    plt.ylim(sa_min, sa_max)
    plt.scatter(vf, sa, facecolor='r', edgecolor='none')

    # vf v. ga
    ax1 = plt.subplot(132)
    plt.xlim(vf_min, vf_max)
    plt.ylim(ga_min, ga_max)
    plt.scatter(vf, ga, facecolor='r', edgecolor='none')

    # sa v. ga
    ax0 = plt.subplot(133)
    plt.xlim(sa_min, sa_max)
    plt.ylim(ga_min, ga_max)
    plt.scatter(sa, ga, facecolor='r', edgecolor='none')

    plt.savefig(
            'AllPointsWithinBin_%s.png' % bin_of_interest,
            transparent=True)
    plt.close(fig)

def plot_variance(run_id):
    fig = plt.figure()
    variances = query_variance(run_id)
    plt.plot(range(len(variances)), variances)
    plt.savefig(
            'Var.png'
            )

def plot_mutation_strengths_in_bin(run_id, bin_of_interest):
    generation, strength = query_mutation_strengths_in_bin(run_id, bin_of_interest)
    if bin_of_interest in over_bins:
        color = 'r.'
    elif bin_of_interest in average_bins:
        color = 'g.'
    elif bin_of_interest in under_bins:
        color = 'b.'
    else:
        color = 'k.'
    plt.plot(generation, strength, color)
    plt.savefig(
            '{0}_{1}_MutationStrengths.png'.format(run_id, bin_of_interest)
            )
    plt.close()

def plot_all_mutation_strengths_over_time(run_id):
    number_of_bins = load_config_file(run_id)['number_of_convergence_bins']

    all_accessed_bins = query_all_mutation_strength_bins(run_id)

    for ga in range(number_of_bins):
        for sa in range(number_of_bins):
            for vf in range(number_of_bins):
                bin_of_interest = '(%s,%s,%s)' % (ga, sa, vf)
                if bin_of_interest in all_accessed_bins:
                    print(bin_of_interest)
                    plot_mutation_strengths_in_bin(run_id, bin_of_interest)

def plot_all_data_points_2D(run_id, generations):
    config                 = load_config_file(run_id)
    gas_adsorption_limits  = config['gas_adsorption_0']['limits']
    surface_area_limits    = config['surface_area']['limits']
    void_fraction_limits   = config['helium_void_fraction']['limits']
    
    data = query_all_data_points(run_id)
#    number_of_generations = len(data)
    fig = plt.figure(figsize=(4 * len(generations), 12))
    G = gridspec.GridSpec(12, 4 * len(generations))

    col_counter = 0
    for generation in generations:
        print('plotting generation {0}...'.format(generation))
        d = data['generation_%s' % generation]
        d_ga = d['ga']
        d_sa = d['sa']
        d_vf = d['vf']
        d_ga_old = d['ga_old']
        d_sa_old = d['sa_old']
        d_vf_old = d['vf_old']

        property_combinations = [
                {
                    'old_x' : d_vf_old,
                    'old_y' : d_sa_old,
                    'x' : d_vf,
                    'y' : d_sa,
                    'x_label' : 'void fraction',
                    'y_label' : 'surface_area',
                    'x_limits' : void_fraction_limits,
                    'y_limits' : surface_area_limits
                },
                {
                    'old_x' : d_vf_old,
                    'old_y' : d_ga_old,
                    'x' : d_vf,
                    'y' : d_ga,
                    'x_label' : 'void fraction',
                    'y_label' : 'gas adsorption',
                    'x_limits' : void_fraction_limits,
                    'y_limits' : gas_adsorption_limits
                },
                {
                    'old_x' : d_sa_old,
                    'old_y' : d_ga_old,
                    'x' : d_sa,
                    'y' : d_ga,
                    'x_label' : 'surface area',
                    'y_label' : 'gas adsorption',
                    'x_limits' : surface_area_limits,
                    'y_limits' : gas_adsorption_limits
                }
            ]
    
        row_counter = 0
        for p in property_combinations:
            print(row_counter, col_counter)
            ax = plt.subplot2grid(
                    (12, 4 * len(generations)),
                    (row_counter, col_counter),
                    rowspan=4, colspan=4
                )
            print(len(p['old_x']), len(p['old_y']))
            plt.scatter(
                    p['old_x'], p['old_y'],
                    edgecolor='none', facecolor='k',
                    alpha=0.7, s=10
                )
            plt.scatter(
                    p['x'], p['y'],
                    edgecolor='none', facecolor='r',
                    alpha=0.7, s=10
                )
            plt.xlim(*p['x_limits'])
            plt.ylim(*p['y_limits'])
            if generation == 0:
                plt.xlabel(p['x_label'])
                plt.ylabel(p['y_label'])
            elif generation != 0: 
                plt.tick_params(
                        axis='both', which='both', bottom='off', top='off',
                        labelbottom='off', right='off', left='off', labelleft='off'
                    )
            row_counter += 4
        col_counter += 4


    plt.tight_layout()
    plt.savefig(
            '{0}_AllDataPoints.png'.format(run_id),
            transparent = True
        )


