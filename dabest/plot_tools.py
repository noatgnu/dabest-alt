# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/API/plot_tools.ipynb.

# %% ../nbs/API/plot_tools.ipynb 2
from __future__ import annotations

# %% auto 0
__all__ = ['halfviolin', 'get_swarm_spans', 'error_bar', 'check_data_matches_labels', 'normalize_dict', 'width_determine',
           'single_sankey', 'sankeydiag']

# %% ../nbs/API/plot_tools.ipynb 4
import pandas as pd
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import itertools
import matplotlib.lines as mlines

# %% ../nbs/API/plot_tools.ipynb 5
def halfviolin(v, half="right", fill_color="k", alpha=1, line_color="k", line_width=0):
    for b in v["bodies"]:
        V = b.get_paths()[0].vertices

        mean_vertical = np.mean(V[:, 0])
        mean_horizontal = np.mean(V[:, 1])

        if half == "right":
            V[:, 0] = np.clip(V[:, 0], mean_vertical, np.inf)
        elif half == "left":
            V[:, 0] = np.clip(V[:, 0], -np.inf, mean_vertical)
        elif half == "bottom":
            V[:, 1] = np.clip(V[:, 1], -np.inf, mean_horizontal)
        elif half == "top":
            V[:, 1] = np.clip(V[:, 1], mean_horizontal, np.inf)

        b.set_color(fill_color)
        b.set_alpha(alpha)
        b.set_edgecolor(line_color)
        b.set_linewidth(line_width)


def get_swarm_spans(coll):
    """
    Given a matplotlib Collection, will obtain the x and y spans
    for the collection. Will return None if this fails.
    """
    if coll is None:
        raise ValueError("The collection `coll` parameter cannot be None")

    x, y = np.array(coll.get_offsets()).T
    try:
        return x.min(), x.max(), y.min(), y.max()
    except ValueError:
        return None


def error_bar(
    data: pd.DataFrame,  # This DataFrame should be in 'long' format.
    x: str,  # x column to be plotted.
    y: str,  # y column to be plotted.
    type: str = "mean_sd",  # Choose from ['mean_sd', 'median_quartiles']. Plots the summary statistics for each group. If 'mean_sd', then the mean and standard deviation of each group is plotted as a gapped line. If 'median_quantiles', then the median and 25th and 75th percentiles of each group is plotted instead.
    offset: float = 0.2,  # Give a single float (that will be used as the x-offset of all gapped lines), or an iterable containing the list of x-offsets.
    ax=None,  # If a matplotlib Axes object is specified, the gapped lines will be plotted in order on this axes. If None, the current axes (plt.gca()) is used.
    line_color="black",  # The color of the gapped lines.
    gap_width_percent=1,  # The width of the gap in the gapped lines, as a percentage of the y-axis span.
    pos: list = [
        0,
        1,
    ],  # The positions of the error bars for the sankey_error_bar method.
    method: str = "gapped_lines",  # The method to use for drawing the error bars. Options are: 'gapped_lines', 'proportional_error_bar', and 'sankey_error_bar'.
    **kwargs: dict,
):
    """
    Function to plot the standard deviations as vertical errorbars.
    The mean is a gap defined by negative space.

    This function combines the functionality of gapped_lines(),
    proportional_error_bar(), and sankey_error_bar().

    """

    if gap_width_percent < 0 or gap_width_percent > 100:
        raise ValueError("`gap_width_percent` must be between 0 and 100.")
    if method not in ["gapped_lines", "proportional_error_bar", "sankey_error_bar"]:
        raise ValueError(
            "Invalid `method`. Must be one of 'gapped_lines', \
                         'proportional_error_bar', or 'sankey_error_bar'."
        )

    if ax is None:
        ax = plt.gca()
    ax_ylims = ax.get_ylim()
    ax_yspan = np.abs(ax_ylims[1] - ax_ylims[0])
    gap_width = ax_yspan * gap_width_percent / 100

    keys = kwargs.keys()
    if "clip_on" not in keys:
        kwargs["clip_on"] = False

    if "zorder" not in keys:
        kwargs["zorder"] = 5

    if "lw" not in keys:
        kwargs["lw"] = 2.0

    if isinstance(data[x].dtype, pd.CategoricalDtype):
        group_order = pd.unique(data[x]).categories
    else:
        group_order = pd.unique(data[x])

    means = data.groupby(x)[y].mean().reindex(index=group_order)

    if method in ["proportional_error_bar", "sankey_error_bar"]:
        g = lambda x: np.sqrt(
            (np.sum(x) * (len(x) - np.sum(x))) / (len(x) * len(x) * len(x))
        )
        sd = data.groupby(x)[y].apply(g)
    else:
        sd = data.groupby(x)[y].std().reindex(index=group_order)

    lower_sd = means - sd
    upper_sd = means + sd

    if (lower_sd < ax_ylims[0]).any() or (upper_sd > ax_ylims[1]).any():
        kwargs["clip_on"] = True

    medians = data.groupby(x)[y].median().reindex(index=group_order)
    quantiles = (
        data.groupby(x)[y].quantile([0.25, 0.75]).unstack().reindex(index=group_order)
    )
    lower_quartiles = quantiles[0.25]
    upper_quartiles = quantiles[0.75]

    if type == "mean_sd":
        central_measures = means
        lows = lower_sd
        highs = upper_sd
    elif type == "median_quartiles":
        central_measures = medians
        lows = lower_quartiles
        highs = upper_quartiles

    n_groups = len(central_measures)

    if isinstance(line_color, str):
        custom_palette = np.repeat(line_color, n_groups)
    else:
        if len(line_color) != n_groups:
            err1 = "{} groups are being plotted, but ".format(n_groups)
            err2 = "{} colors(s) were supplied in `line_color`.".format(len(line_color))
            raise ValueError(err1 + err2)
        custom_palette = line_color

    try:
        len_offset = len(offset)
    except TypeError:
        offset = np.repeat(offset, n_groups)
        len_offset = len(offset)

    if len_offset != n_groups:
        err1 = "{} groups are being plotted, but ".format(n_groups)
        err2 = "{} offset(s) were supplied in `offset`.".format(len_offset)
        raise ValueError(err1 + err2)

    kwargs["zorder"] = kwargs["zorder"]

    for xpos, central_measure in enumerate(central_measures):
        kwargs["color"] = custom_palette[xpos]

        if method == "sankey_error_bar":
            _xpos = pos[xpos] + offset[xpos]
        else:
            _xpos = xpos + offset[xpos]

        low = lows[xpos]
        high = highs[xpos]
        if low == high == central_measure:
            low_to_mean = mlines.Line2D(
                [_xpos, _xpos], [low, central_measure], **kwargs
            )
            ax.add_line(low_to_mean)

            mean_to_high = mlines.Line2D(
                [_xpos, _xpos], [central_measure, high], **kwargs
            )
            ax.add_line(mean_to_high)
        else:
            low_to_mean = mlines.Line2D(
                [_xpos, _xpos], [low, central_measure - gap_width], **kwargs
            )
            ax.add_line(low_to_mean)

            mean_to_high = mlines.Line2D(
                [_xpos, _xpos], [central_measure + gap_width, high], **kwargs
            )
            ax.add_line(mean_to_high)


def check_data_matches_labels(
    labels,  # list of input labels
    data,  # Pandas Series of input data
    side: str,  # 'left' or 'right' on the sankey diagram
):
    """
    Function to check that the labels and data match in the sankey diagram.
    And enforce labels and data to be lists.
    Raises an exception if the labels and data do not match.
    """
    if len(labels) > 0:
        if isinstance(data, list):
            data = set(data)
        if isinstance(data, pd.Series):
            data = set(data.unique())
        if isinstance(labels, list):
            labels = set(labels)
        if labels != data:
            msg = "\n"
            if len(labels) <= 20:
                msg = "Labels: " + ",".join(labels) + "\n"
            if len(data) < 20:
                msg += "Data: " + ",".join(data)
            raise Exception(f"{side} labels and data do not match.{msg}")


def normalize_dict(nested_dict, target):
    val = {}
    for key in nested_dict.keys():
        val[key] = np.sum(
            [
                nested_dict[sub_key][key]
                for sub_key in nested_dict.keys()
                if key in nested_dict[sub_key]
            ]
        )

    for key, value in nested_dict.items():
        if isinstance(value, dict):
            for subkey in value.keys():
                if subkey in val.keys():
                    if val[subkey] != 0:
                        # Address the problem when one of the label have zero value
                        value[subkey] = (
                            value[subkey] * target[subkey]["right"] / val[subkey]
                        )
                    else:
                        value[subkey] = 0
                else:
                    value[subkey] = target[subkey]["right"]
    return nested_dict


def width_determine(labels, data, pos="left"):
    if labels is None:
        raise ValueError("The `labels` parameter cannot be None")

    if data is None:
        raise ValueError("The `data` parameter cannot be None")
    
    widths_norm = defaultdict()
    for i, label in enumerate(labels):
        myD = {}
        myD[pos] = data[data[pos] == label][pos + "Weight"].sum()
        if len(labels) != 1:
            if i == 0:
                myD["bottom"] = 0
                myD[pos] -= 0.01
                myD["top"] = myD[pos]
            elif i == len(labels) - 1:
                myD[pos] -= 0.01
                myD["bottom"] = 1 - myD[pos]
                myD["top"] = 1
            else:
                myD[pos] -= 0.02
                myD["bottom"] = widths_norm[labels[i - 1]]["top"] + 0.02
                myD["top"] = myD["bottom"] + myD[pos]
        else:
            myD["bottom"] = 0
            myD["top"] = 1
        widths_norm[label] = myD
    return widths_norm


def single_sankey(
    left: np.array,  # data on the left of the diagram
    right: np.array,  # data on the right of the diagram, len(left) == len(right)
    xpos: float = 0,  # the starting point on the x-axis
    leftWeight: np.array = None,  # weights for the left labels, if None, all weights are 1
    rightWeight: np.array = None,  # weights for the right labels, if None, all weights are corresponding leftWeight
    colorDict: dict = None,  # input format: {'label': 'color'}
    leftLabels: list = None,  # labels for the left side of the diagram. The diagram will be sorted by these labels.
    rightLabels: list = None,  # labels for the right side of the diagram. The diagram will be sorted by these labels.
    ax=None,  # matplotlib axes to be drawn on
    flow: bool = True,  # if True, draw the sankey in a flow, else draw 1 vs 1 Sankey diagram for each group comparison
    sankey: bool = True,  # if True, draw the sankey diagram, else draw barplot
    width=0.5,
    alpha=0.65,
    bar_width=0.2,
    error_bar_on: bool = True,  # if True, draw error bar for each group comparison
    strip_on: bool = True,  # if True, draw strip for each group comparison
    one_sankey: bool = False,  # if True, only draw one sankey diagram
    rightColor: bool = False,  # if True, each strip of the diagram will be colored according to the corresponding left labels
    align: bool = "center",  # if 'center', the diagram will be centered on each xtick,  if 'edge', the diagram will be aligned with the left edge of each xtick
):
    """
    Make a single Sankey diagram showing proportion flow from left to right
    Original code from: https://github.com/anazalea/pySankey
    Changes are added to normalize each diagram's height to be 1

    """

    # Initiating values
    if ax is None:
        ax = plt.gca()

    if leftWeight is None:
        leftWeight = []
    if rightWeight is None:
        rightWeight = []
    if leftLabels is None:
        leftLabels = []
    if rightLabels is None:
        rightLabels = []
    # Check weights
    if len(leftWeight) == 0:
        leftWeight = np.ones(len(left))
    if len(rightWeight) == 0:
        rightWeight = np.ones(len(right))

    # Create Dataframe
    if isinstance(left, pd.Series):
        left.reset_index(drop=True, inplace=True)
    if isinstance(right, pd.Series):
        right.reset_index(drop=True, inplace=True)
    dataFrame = pd.DataFrame(
        {
            "left": left,
            "right": right,
            "leftWeight": leftWeight,
            "rightWeight": rightWeight,
        },
        index=range(len(left)),
    )

    if dataFrame[["left", "right"]].isnull().any(axis=None):
        raise Exception("Sankey graph does not support null values.")

    # Identify all labels that appear 'left' or 'right'
    allLabels = pd.Series(
        np.sort(np.r_[dataFrame.left.unique(), dataFrame.right.unique()])[::-1]
    ).unique()

    # Identify left labels
    if len(leftLabels) == 0:
        leftLabels = pd.Series(np.sort(dataFrame.left.unique())[::-1]).unique()
    else:
        check_data_matches_labels(leftLabels, dataFrame["left"], "left")

    # Identify right labels
    if len(rightLabels) == 0:
        rightLabels = pd.Series(np.sort(dataFrame.right.unique())[::-1]).unique()
    else:
        check_data_matches_labels(leftLabels, dataFrame["right"], "right")

    # If no colorDict given, make one
    if colorDict is None:
        colorDict = {}
        palette = "hls"
        colorPalette = sns.color_palette(palette, len(allLabels))
        for i, label in enumerate(allLabels):
            colorDict[label] = colorPalette[i]
        fail_color = {0: "grey"}
        colorDict.update(fail_color)
    else:
        missing = [label for label in allLabels if label not in colorDict.keys()]
        if missing:
            msg = "The palette parameter is missing values for the following labels : "
            msg += "{}".format(", ".join(missing))
            raise ValueError(msg)

    if align not in ("center", "edge"):
        err = "{} assigned for `align` is not valid.".format(align)
        raise ValueError(err)
    if align == "center":
        try:
            leftpos = xpos - width / 2
        except TypeError as e:
            raise TypeError(
                f"the dtypes of parameters x ({xpos.dtype}) "
                f"and width ({width.dtype}) "
                f"are incompatible"
            ) from e
    else:
        leftpos = xpos

    # Combine left and right arrays to have a pandas.DataFrame in the 'long' format
    left_series = pd.Series(left, name="values").to_frame().assign(groups="left")
    right_series = pd.Series(right, name="values").to_frame().assign(groups="right")
    concatenated_df = pd.concat([left_series, right_series], ignore_index=True)

    # Determine positions of left label patches and total widths
    # We also want the height of the graph to be 1
    leftWidths_norm = defaultdict()
    for i, leftLabel in enumerate(leftLabels):
        myD = {}
        myD["left"] = (
            dataFrame[dataFrame.left == leftLabel].leftWeight.sum()
            / dataFrame.leftWeight.sum()
        )
        if len(leftLabels) != 1:
            if i == 0:
                myD["bottom"] = 0
                myD["left"] -= 0.01
                myD["top"] = myD["left"]
            elif i == len(leftLabels) - 1:
                myD["left"] -= 0.01
                myD["bottom"] = 1 - myD["left"]
                myD["top"] = 1
            else:
                myD["left"] -= 0.02
                myD["bottom"] = leftWidths_norm[leftLabels[i - 1]]["top"] + 0.02
                myD["top"] = myD["bottom"] + myD["left"]
                topEdge = myD["top"]
        else:
            myD["bottom"] = 0
            myD["top"] = 1
            myD["left"] = 1
        leftWidths_norm[leftLabel] = myD

    # Determine positions of right label patches and total widths
    rightWidths_norm = defaultdict()
    for i, rightLabel in enumerate(rightLabels):
        myD = {}
        myD["right"] = (
            dataFrame[dataFrame.right == rightLabel].rightWeight.sum()
            / dataFrame.rightWeight.sum()
        )
        if len(rightLabels) != 1:
            if i == 0:
                myD["bottom"] = 0
                myD["right"] -= 0.01
                myD["top"] = myD["right"]
            elif i == len(rightLabels) - 1:
                myD["right"] -= 0.01
                myD["bottom"] = 1 - myD["right"]
                myD["top"] = 1
            else:
                myD["right"] -= 0.02
                myD["bottom"] = rightWidths_norm[rightLabels[i - 1]]["top"] + 0.02
                myD["top"] = myD["bottom"] + myD["right"]
                topEdge = myD["top"]
        else:
            myD["bottom"] = 0
            myD["top"] = 1
            myD["right"] = 1
        rightWidths_norm[rightLabel] = myD

    # Total width of the graph
    xMax = width

    # Plot vertical bars for each label
    for leftLabel in leftLabels:
        ax.fill_between(
            [leftpos + (-(bar_width) * xMax * 0.5), leftpos + (bar_width * xMax * 0.5)],
            2 * [leftWidths_norm[leftLabel]["bottom"]],
            2 * [leftWidths_norm[leftLabel]["top"]],
            color=colorDict[leftLabel],
            alpha=0.99,
        )
    if (flow == False and sankey == True) or one_sankey:
        for rightLabel in rightLabels:
            ax.fill_between(
                [
                    xMax + leftpos + (-bar_width * xMax * 0.5),
                    leftpos + xMax + (bar_width * xMax * 0.5),
                ],
                2 * [rightWidths_norm[rightLabel]["bottom"]],
                2 * [rightWidths_norm[rightLabel]["top"]],
                color=colorDict[rightLabel],
                alpha=0.99,
            )

    # Plot error bars
    if error_bar_on and strip_on:
        error_bar(
            concatenated_df,
            x="groups",
            y="values",
            ax=ax,
            offset=0,
            gap_width_percent=2,
            method="sankey_error_bar",
            pos=[leftpos, leftpos + xMax],
        )

    # Determine widths of individual strips, all widths are normalized to 1
    ns_l = defaultdict()
    ns_r = defaultdict()
    ns_l_norm = defaultdict()
    ns_r_norm = defaultdict()
    for leftLabel in leftLabels:
        leftDict = {}
        rightDict = {}
        for rightLabel in rightLabels:
            leftDict[rightLabel] = dataFrame[
                (dataFrame.left == leftLabel) & (dataFrame.right == rightLabel)
            ].leftWeight.sum()

            rightDict[rightLabel] = dataFrame[
                (dataFrame.left == leftLabel) & (dataFrame.right == rightLabel)
            ].rightWeight.sum()
        factorleft = leftWidths_norm[leftLabel]["left"] / sum(leftDict.values())
        leftDict_norm = {k: v * factorleft for k, v in leftDict.items()}
        ns_l_norm[leftLabel] = leftDict_norm
        ns_r[leftLabel] = rightDict

    # ns_r should be using a different way of normalization to fit the right side
    # It is normalized using the value with the same key in each sub-dictionary
    ns_r_norm = normalize_dict(ns_r, rightWidths_norm)

    # Plot strips
    if sankey and strip_on:
        for leftLabel, rightLabel in itertools.product(leftLabels, rightLabels):
            labelColor = leftLabel
            
            if rightColor:
                labelColor = rightLabel
            
            if len(dataFrame[(dataFrame.left == leftLabel) & 
                        (dataFrame.right == rightLabel)]) > 0:
                # Create array of y values for each strip, half at left value,
                # half at right, convolve
                ys_d = np.array(
                    50 * [leftWidths_norm[leftLabel]["bottom"]]
                    + 50 * [rightWidths_norm[rightLabel]["bottom"]]
                )
                ys_d = np.convolve(ys_d, 0.05 * np.ones(20), mode="valid")
                ys_d = np.convolve(ys_d, 0.05 * np.ones(20), mode="valid")
                # to remove the array wrapping behaviour of black
                # fmt: off
                ys_u = np.array(50 * [leftWidths_norm[leftLabel]['bottom'] + ns_l_norm[leftLabel][rightLabel]] + \
                    50 * [rightWidths_norm[rightLabel]['bottom'] + ns_r_norm[leftLabel][rightLabel]])
                # fmt: on
                ys_u = np.convolve(ys_u, 0.05 * np.ones(20), mode="valid")
                ys_u = np.convolve(ys_u, 0.05 * np.ones(20), mode="valid")

                # Update bottom edges at each label so next strip starts at the right place
                leftWidths_norm[leftLabel]["bottom"] += ns_l_norm[leftLabel][rightLabel]
                rightWidths_norm[rightLabel]["bottom"] += ns_r_norm[leftLabel][
                    rightLabel
                ]
                ax.fill_between(
                    np.linspace(
                        leftpos + (bar_width * xMax * 0.5),
                        leftpos + xMax - (bar_width * xMax * 0.5),
                        len(ys_d),
                    ),
                    ys_d,
                    ys_u,
                    alpha=alpha,
                    color=colorDict[labelColor],
                    edgecolor="none",
                )


def sankeydiag(
    data: pd.DataFrame,
    xvar: str,  # x column to be plotted.
    yvar: str,  # y column to be plotted.
    left_idx: str,  # the value in column xvar that is on the left side of each sankey diagram
    right_idx: str,  # the value in column xvar that is on the right side of each sankey diagram, if len(left_idx) == 1, it will be broadcasted to the same length as right_idx, otherwise it should have the same length as right_idx
    leftLabels: list = None,  # labels for the left side of the diagram. The diagram will be sorted by these labels.
    rightLabels: list = None,  # labels for the right side of the diagram. The diagram will be sorted by these labels.
    palette: str | dict = None,
    ax=None,  # matplotlib axes to be drawn on
    flow: bool = True,  # if True, draw the sankey in a flow, else draw 1 vs 1 Sankey diagram for each group comparison
    sankey: bool = True,  # if True, draw the sankey diagram, else draw barplot
    one_sankey: bool = False,  # determined by the driver function on plotter.py, if True, draw the sankey diagram across the whole raw data axes
    width: float = 0.4,  # the width of each sankey diagram
    rightColor: bool = False,  # if True, each strip of the diagram will be colored according to the corresponding left labels
    align: str = "center",  # the alignment of each sankey diagram, can be 'center' or 'left'
    alpha: float = 0.65,  # the transparency of each strip
    **kwargs,
):
    """
    Read in melted pd.DataFrame, and draw multiple sankey diagram on a single axes
    using the value in column yvar according to the value in column xvar
    left_idx in the column xvar is on the left side of each sankey diagram
    right_idx in the column xvar is on the right side of each sankey diagram

    """

    if "width" in kwargs:
        width = kwargs["width"]

    if "align" in kwargs:
        align = kwargs["align"]

    if "alpha" in kwargs:
        alpha = kwargs["alpha"]

    if "rightColor" in kwargs:
        rightColor = kwargs["rightColor"]

    if "bar_width" in kwargs:
        bar_width = kwargs["bar_width"]

    if "sankey" in kwargs:
        sankey = kwargs["sankey"]

    if "flow" in kwargs:
        flow = kwargs["flow"]

    if ax is None:
        ax = plt.gca()

    allLabels = pd.Series(np.sort(data[yvar].unique())[::-1]).unique()

    # Check if all the elements in left_idx and right_idx are in xvar column
    unique_xvar = data[xvar].unique()
    if not all(elem in unique_xvar for elem in left_idx):
        raise ValueError(f"{left_idx} not found in {xvar} column")
    if not all(elem in unique_xvar for elem in right_idx):
        raise ValueError(f"{right_idx} not found in {xvar} column")

    xpos = 0

    # For baseline comparison, broadcast left_idx to the same length as right_idx
    # so that the left of sankey diagram will be the same
    # For sequential comparison, left_idx and right_idx can have anything different
    # but should have the same length
    if len(left_idx) == 1:
        broadcasted_left = np.broadcast_to(left_idx, len(right_idx))
    elif len(left_idx) != len(right_idx):
        raise ValueError(f"left_idx and right_idx should have the same length")
    else:
        broadcasted_left = left_idx

    if isinstance(palette, dict):
        if not all(key in allLabels for key in palette.keys()):
            raise ValueError(f"keys in palette should be in {yvar} column")
        plot_palette = palette
    elif isinstance(palette, str):
        plot_palette = {}
        colorPalette = sns.color_palette(palette, len(allLabels))
        for i, label in enumerate(allLabels):
            plot_palette[label] = colorPalette[i]
    else:
        plot_palette = None

    # Create a strip_on list to determine whether to draw the strip during repeated measures
    strip_on = [
        int(right not in broadcasted_left[:i]) for i, right in enumerate(right_idx)
    ]

    draw_idx = list(zip(broadcasted_left, right_idx))
    for i, (left, right) in enumerate(draw_idx):
        if one_sankey == False:
            if flow == True:
                width = 1
                align = "edge"
                sankey = (
                    False if i == len(draw_idx) - 1 else sankey
                )  # Remove last strip in flow
            error_bar_on = (
                False if i == len(draw_idx) - 1 and flow else True
            )  # Remove last error_bar in flow
            bar_width = 0.4 if sankey == False and flow == False else bar_width
            single_sankey(
                data[data[xvar] == left][yvar],
                data[data[xvar] == right][yvar],
                xpos=xpos,
                ax=ax,
                colorDict=plot_palette,
                width=width,
                leftLabels=leftLabels,
                rightLabels=rightLabels,
                strip_on=strip_on[i],
                rightColor=rightColor,
                bar_width=bar_width,
                sankey=sankey,
                error_bar_on=error_bar_on,
                flow=flow,
                align=align,
                alpha=alpha,
            )
            xpos += 1
        else:
            xpos = 0
            width = 1
            if sankey == False:
                bar_width = 0.5
            single_sankey(
                data[data[xvar] == left][yvar],
                data[data[xvar] == right][yvar],
                xpos=xpos,
                ax=ax,
                colorDict=plot_palette,
                width=width,
                leftLabels=leftLabels,
                rightLabels=rightLabels,
                rightColor=rightColor,
                bar_width=bar_width,
                sankey=sankey,
                one_sankey=one_sankey,
                flow=False,
                align="edge",
                alpha=alpha,
            )

    # Now only draw vs xticks for two-column sankey diagram
    if ~one_sankey or (sankey and not flow):
        sankey_ticks = (
            [f"{left}" for left in broadcasted_left]
            if flow
            else [
                f"{left}\n v.s.\n{right}"
                for left, right in zip(broadcasted_left, right_idx)
            ]
        )
        ax.get_xaxis().set_ticks(np.arange(len(right_idx)))
        ax.get_xaxis().set_ticklabels(sankey_ticks)
    else:
        sankey_ticks = [broadcasted_left[0], right_idx[0]]
        ax.set_xticks([0, 1])
        ax.set_xticklabels(sankey_ticks)
