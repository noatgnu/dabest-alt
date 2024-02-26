# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/API/forest_plot.ipynb.

# %% auto 0
__all__ = ['load_plot_data', 'extract_plot_data', 'forest_plot']

# %% ../nbs/API/forest_plot.ipynb 5
import matplotlib.pyplot as plt
# %matplotlib inline
import seaborn as sns
from typing import List, Optional, Union


# %% ../nbs/API/forest_plot.ipynb 6
def load_plot_data(
    contrasts: List, effect_size: str = "mean_diff", contrast_type: str = "delta2"
) -> List:
    """
    Loads plot data based on specified effect size and contrast type.

    Parameters:
    contrasts (List): List of contrast objects.
    effect_size (str): Type of effect size ('mean_diff', 'median_diff', etc.).
    contrast_type (str): Type of contrast ('delta2', 'mini_meta').

    Returns:
    List: Contrast plot data based on specified parameters.
    """
    effect_attr_map = {
        "mean_diff": "mean_diff",
        "median_diff": "median_diff",
        "cliffs_delta": "cliffs_delta",
        "cohens_d": "cohens_d",
        "hedges_g": "hedges_g",
        "delta_g": "delta_g"
    }

    contrast_attr_map = {"delta2": "delta_delta", "mini_meta": "mini_meta_delta"}

    effect_attr = effect_attr_map.get(effect_size)
    contrast_attr = contrast_attr_map.get(contrast_type)

    if not effect_attr:
        raise ValueError(f"Invalid effect_size: {effect_size}")

    return [
        getattr(getattr(contrast, effect_attr), contrast_attr) for contrast in contrasts
    ]


def extract_plot_data(contrast_plot_data, contrast_type):
    """Extracts bootstrap, difference, and confidence intervals based on contrast labels."""
    if contrast_type == "mini_meta":
        attribute_suffix = "weighted_delta"
    else:
        attribute_suffix = "delta_delta"

    bootstraps = [
        getattr(result, f"bootstraps_{attribute_suffix}")
        for result in contrast_plot_data
    ]
    
    differences = [result.difference for result in contrast_plot_data]
    bcalows = [result.bca_low for result in contrast_plot_data]
    bcahighs = [result.bca_high for result in contrast_plot_data]
    
    return bootstraps, differences, bcalows, bcahighs


def forest_plot(
    contrasts: List,
    selected_indices: Optional[List] = None,
    contrast_type: str = "delta2",
    xticklabels: Optional[List] = None,
    effect_size: str = "mean_diff",
    contrast_labels: List[str] = None,
    ylabel: str = "value",
    plot_elements_to_extract: Optional[List] = None,
    title: str = "ΔΔ Forest",
    custom_palette: Optional[Union[dict, list, str]] = None,
    fontsize: int = 20,
    violin_kwargs: Optional[dict] = None,
    marker_size: int = 20,
    ci_line_width: float = 2.5,
    zero_line_width: int = 1,
    remove_spines: bool = True,
    ax: Optional[plt.Axes] = None,
    additional_plotting_kwargs: Optional[dict] = None,
    rotation_for_xlabels: int = 45,
    alpha_violin_plot: float = 0.4,
    horizontal: bool = False  # New argument for horizontal orientation
)-> plt.Figure:
    
    """
    Generates a customized forest plot using contrast objects. This function supports both horizontal and vertical orientations of the plot, as determined by the 'horizontal' parameter.

    Parameters:
    __________
    contrasts (List): List of contrast objects to be plotted.
    selected_indices (Optional[List]): Specific indices of contrasts to be plotted, if not plotting all. Default is None, which means all contrasts are plotted.
    contrast_type (str): Specifies the type of analysis (e.g., 'delta2', 'minimeta') for the contrasts. This determines the statistical approach used for the contrasts.
    xticklabels (Optional[List]): Custom labels for the x-axis ticks. If not provided, the default is to use indices.
    effect_size (str): Specifies the type of effect size to be plotted (e.g., 'mean_diff', 'median_diff'). This is crucial for interpreting the results correctly.
    contrast_labels (List[str]): Labels for each contrast. These are used for labeling the plot elements and must correspond to the contrasts provided.
    ylabel (str): Label for the y-axis. This should describe the data or effect size being plotted and is essential for plot interpretation.
    plot_elements_to_extract (Optional[List]): Specifies which plot elements to extract for custom plotting. This allows for more detailed customization of the plot. Default is None.
    title (str): The title of the plot. This should provide a concise summary of what the plot represents.
    custom_palette (Optional[Union[dict, list, str]]): A custom color palette for the plot. Can be specified as a dictionary mapping contrasts to colors, a list of colors, or a string name of a seaborn or matplotlib colormap. Default is None.
    fontsize (int): Font size for all text elements in the plot, including labels, title, and tick labels. This is important for ensuring the plot is readable.
    violin_kwargs (Optional[dict]): Additional keyword arguments passed to the violinplot function. This allows for further customization of the violin plots. Default is None.
    marker_size (int): Size of the markers used for plotting mean differences or effect sizes. This affects the visual representation of the data points.
    ci_line_width (float): Line width for the confidence interval lines. This helps to visually distinguish the confidence intervals.
    zero_line_width (int): Width of the line representing the zero effect size or reference line. This is important for identifying the point of no effect.
    remove_spines (bool): If True, removes the top and right spines from the plot, which can make the plot look cleaner. Default is False.
    ax (Optional[plt.Axes]): An existing matplotlib Axes object to plot on. If None, a new figure and axes are created. This allows for integration into larger figures.  
    additional_plotting_kwargs (Optional[dict]): Additional keyword arguments for customizing the plot. This provides flexibility for advanced plot customization. Default is None.
    rotation_for_xlabels (int): Rotation angle (in degrees) for the x-axis labels. This can help with label readability, especially for long labels. Default is 0.
    alpha_violin_plot (float): Transparency level for the violin plots. This can be adjusted to make the plot more visually appealing. Default is 1.0 (fully opaque).
    horizontal (bool): If True, plots the forest plot horizontally (with effect sizes along the y-axis). Otherwise, plots vertically with effect sizes along the x-axis. This affects the orientation of the plot.

    Returns:
    _______
    plt.Figure: The matplotlib figure object containing the generated plot. This object can be further modified or saved as an image file.
    """
    from .plot_tools import halfviolin

    # Validate inputs
    if not contrasts:
        raise ValueError("The `contrasts` list cannot be empty.")
    
    if contrast_labels is not None and len(contrast_labels) != len(contrasts):
        raise ValueError("`contrast_labels` must match the number of `contrasts` if provided.")
    
    # Load plot data
    contrast_plot_data = load_plot_data(contrasts, effect_size, contrast_type)

    # Extract data for plotting
    bootstraps, differences, bcalows, bcahighs = extract_plot_data(
        contrast_plot_data, contrast_type
    )
    # Adjust figure size based on orientation
    all_groups_count = len(contrasts)
    if horizontal:
        fig_size = (4, 2.5 * all_groups_count)
    else:
        fig_size = (2.5 * all_groups_count, 4)

    if ax is None:
        fig, ax = plt.subplots(figsize=fig_size)
    else:
        fig = ax.figure

    # Adjust violin plot orientation based on the 'horizontal' argument
    violin_kwargs = violin_kwargs or {
        "widths": 0.5,
        "showextrema": False,
        "showmedians": False,
    }
    violin_kwargs["vert"] = not horizontal
    v = ax.violinplot(bootstraps, **violin_kwargs)

    # Adjust the halfviolin function call based on 'horizontal'
    if horizontal:
        half = "top"
    else:
        half = "right"  # Assuming "right" is the default or another appropriate value

    # Assuming halfviolin has been updated to accept a 'half' parameter
    halfviolin(v, alpha=alpha_violin_plot, half=half)
    
    # Handle the custom color palette
    if custom_palette:
        if isinstance(custom_palette, dict):
            violin_colors = [
                custom_palette.get(c, sns.color_palette()[0]) for c in contrasts
            ]
        elif isinstance(custom_palette, list):
            violin_colors = custom_palette[: len(contrasts)]
        elif isinstance(custom_palette, str):
            if custom_palette in plt.colormaps():
                violin_colors = sns.color_palette(custom_palette, len(contrasts))
            else:
                raise ValueError(
                    f"The specified `custom_palette` {custom_palette} is not a recognized Matplotlib palette."
                )
    else:
        violin_colors = sns.color_palette()[: len(contrasts)]

    for patch, color in zip(v["bodies"], violin_colors):
        patch.set_facecolor(color)
        patch.set_alpha(alpha_violin_plot)

    # Flipping the axes for plotting based on 'horizontal'
    for k in range(1, len(contrasts) + 1):
        if horizontal:
            ax.plot(differences[k - 1], k, "k.", markersize=marker_size)  # Flipped axes
            ax.plot([bcalows[k - 1], bcahighs[k - 1]], [k, k], "k", linewidth=ci_line_width)  # Flipped axes
        else:
            ax.plot(k, differences[k - 1], "k.", markersize=marker_size)
            ax.plot([k, k], [bcalows[k - 1], bcahighs[k - 1]], "k", linewidth=ci_line_width)

    # Adjusting labels, ticks, and limits based on 'horizontal'
    if horizontal:
        ax.set_yticks(range(1, len(contrasts) + 1))
        ax.set_yticklabels(contrast_labels,  rotation=rotation_for_xlabels, fontsize=fontsize)
        ax.set_xlabel(ylabel, fontsize=fontsize)
    else:
        ax.set_xticks(range(1, len(contrasts) + 1))
        ax.set_xticklabels(contrast_labels, rotation=rotation_for_xlabels, fontsize=fontsize)
        ax.set_ylabel(ylabel, fontsize=fontsize)

    # Setting the title and adjusting spines as before
    ax.set_title(title, fontsize=fontsize)
    if remove_spines:
        for spine in ax.spines.values():
            spine.set_visible(False)

    # Apply additional customizations if provided
    if additional_plotting_kwargs:
        ax.set(**additional_plotting_kwargs)

    return fig
