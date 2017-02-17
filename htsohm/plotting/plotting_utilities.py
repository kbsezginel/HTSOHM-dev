import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.patches as patches

from htsohm.utilities import *
from htsohm.db.queries import *
from htsohm.db.__init__ import engine

def labeling(labels, ax, config):
    if labels == None:
        plt.tick_params(
            axis='both', which='both', bottom='off', top='off', labelbottom='off',
            right='off', left='off', labelleft='off'
        )
    elif labels == 'first_only':
        if z_bins.index(z_bin) != 0 or generations.index(gen) != 0:
            ax.tick_params(labelbottom=False, labelleft=False)
        if z_bins.index(z_bin) == 0 and generations.index(gen) == 0:
            x_ticks = np.arange(
                x_limits[0], x_limits[1] + 0.01,
                (x_limits[1] - x_limits[0]) / 2.
            )
            ax.set_xticks(x_ticks)
            y_ticks = np.arange(
                y_limits[0], y_limits[1] + 0.01,
                (y_limits[1] - y_limits[0]) / 2.
            )
            ax.set_yticks(y_ticks)
        if z_bins.index(z_bin) == 0 and generations.index(gen) == 1:
            plt.xlabel(x)
            plt.ylabel(y)
    elif labels == 'all':
        plt.xlabel(x)
        plt.ylabel(y)
    elif labels == 'grid_only':
        ax.tick_params(labelbottom=False, labelleft=False)
        number_of_bins = config['number_of_convergence_bins']
        x_ticks = np.arange(
            x_limits[0], x_limits[1] + 0.01,
            (x_limits[1] - x_limits[0]) / float(number_of_bins)
        )
        ax.set_xticks(x_ticks)
        y_ticks = np.arange(
            y_limits[0], y_limits[1] + 0.01,
            (y_limits[1] - y_limits[0]) / float(number_of_bins)
        )
        ax.set_yticks(y_ticks)
        plt.grid(b = True, which = 'both', linestyle='-', alpha=0.5)

def highlight_children(x, y, z_bin, run_id, gen, children, data_type):
    if data_type == 'DataPoints':
        if children == 'off':
            child_colour = 'k'
        elif children == 'on':
            child_colour = 'r'
            x_ = query_points(x, z_bin, run_id, gen)
            y_ = query_points(y, z_bin, run_id, gen)
            plt.scatter(
                x_, y_,
                marker='o',
                facecolors=child_colour,
                edgecolors='none',
                alpha=0.7, s=2
            )
        
        elif children == 'top_five':
            top_five = find_most_children(x, y, z_bin, run_id, gen)
            colors = [
                ['red', 'darkred'],
                ['blue', 'darkblue'],
                ['green', 'darkgreen'],
                ['violet', 'darkviolet'],
                ['orange', 'darkorange']
            ]
            counter = 0
            for values in top_five:
                parent_color = colors[counter][0]
                child_color = colors[counter][1]
                plt.scatter(
                    *values[0][0],
                    marker='o',
                    facecolors=parent_color,
                    edgecolors='none',
                    s=4
                )
                for child_point in values[1]:
                    plt.scatter(
                        *child_point,
                        marker='o',
                        facecolors=child_color,
                        edgecolors='none',
                        alpha=0.5, s=2
                    )
                counter += 1
#    elif data_type == 'BinCounts':
#    elif data_type == 'MutationStrength':

def hightlight_parents(x, y, z_bin, run_id, gen, data_type):
    if data_type == 'DataPoints':
        x_, y_ = query_parents(x, y, z_bin, run_id, gen)
        if len(x_) > 0 and len(y_) > 0:
            plt.scatter(
                x_, y_,
                marker='o',
                facecolors='none',
                edgecolors='k',
                linewidth='0.4',
                alpha=0.5, s=5
            )

    elif data_type == 'BinCounts':
        if gen != 0:
            s = query_parents(x, y, z_bin, run_id, gen)
            result = engine.execute(s)
            for row in result:
                add_square(
                    x, y,
                    row[0][0], i[0][1],
                    'none',
                    'y',
                    ax, config,
                    2
                )
            result.close()

def highlight_top_bins(x, y, z_bin, run_id, gen, pick_bins):
    if pick_bins != None:
        BC_x = x + '_bin'
        BC_y = y + '_bin'
        x_, y_, c_ = query_bin_counts(BC_x, BC_y, z_bin, run_id, gen - 1)
        x_ = x_[:pick_bins]
        y_ = y_[:pick_bins]
        for i in range(len(x_)):
            add_square(
                x, y,
                x_[i], y_[i],
                'none',
                'k',
                ax, config
            )

def add_square(
        x, y, 
        x_value, y_value,
        facecolor,
        edgecolor,
        ax, config,
        linewidth=None,
        linestyle='solid'):
    x_width = get_width(x, config)
    y_width = get_width(y, config)
    x_pos = x_value * x_width
    y_pos = y_value * y_width
    ax.add_patch(
        patches.Rectangle(
            (x_pos, y_pos),
            x_width,
            y_width,
            facecolor = facecolor,
            edgecolor = edgecolor,
            linewidth = linewidth,
            linestyle = linestyle,
            alpha = 1
        )
    )


