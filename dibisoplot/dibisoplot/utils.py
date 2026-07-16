from io import BytesIO
import pkgutil
import tomllib
import warnings

import flag
import plotly.graph_objects as go

hal_doc_types_names_mapping = tomllib.load(BytesIO(pkgutil.get_data(__name__, "HAL_doc_types_names.toml")))


def get_hal_doc_type_name(name):
    if name in hal_doc_types_names_mapping.keys():
        return hal_doc_types_names_mapping[name]
    else:
        warnings.warn(f"Unknown HAL doc type name: {name}. Using raw name.")
        parts = name.split('_')
        return ' '.join([parts[0].capitalize()] + [part.lower() for part in parts[1:]])


def get_empty_plot_with_message(message: str) -> go.Figure:
    """Create an empty plot with a message."""
    fig = go.Figure()
    fig.add_annotation(text=message, showarrow=False)
    fig.update_layout(showlegend=False, template="simple_white")
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def get_empty_latex_with_message(message: str) -> str:
    """Create an empty plot with a message."""
    latex_str = """
\\setlength{\\fboxsep}{10pt}
\\fbox{
    \\parbox{\\textwidth}{
        \\centering """+message+"""
    }
}
"""
    return latex_str


# Calculate plot bar width depending on the number of bars on the plot, based on a linear interpolation of two examples
max_width = 0.7
n_bars_max_width = 10
example_width = 0.25
example_n_bars = 2
a = (max_width - example_width)/(n_bars_max_width - example_n_bars)
b = example_width - example_n_bars*(max_width - example_width)/(n_bars_max_width - example_n_bars)


def get_bar_width(n_bars: int) -> int | float:
    """
    Calculate the width of bars in a plot based on the number of bars.

    This function uses linear interpolation to determine the bar width based on the number of bars.
    The interpolation is based on two examples: one with 10 bars and a width of 0.7, and another with 2 bars and a width
    of 0.25.

    :param n_bars: Number of bars in the plot.
    :type n_bars: int
    :return: Width of the bars.
    :rtype: int | float
    """
    if n_bars >= n_bars_max_width:
        return max_width
    return a * n_bars + b


def format_structure_name(struct_name: str, country_code: str) -> str:
    """
    Format the structure name by cropping if too long and adding a country flag.

    :param struct_name: The structure name.
    :type struct_name: str
    :param country_code: The country code.
    :type country_code: str
    :return: The formatted structure name with country flag.
    :rtype: str
    """
    # crop name if too long
    if len(struct_name) > 65:
        struct_name = struct_name[:65]+"... "
    # add country flag
    if country_code is None:
        return struct_name + " (Unspecified country)"
    # country_flag=get_flag_img(country_code)
    # return f"{country_flag}{struct_name}"
    return f"{struct_name} __{country_code.upper()}__"

# def get_flag_img(country_code: str) -> str:
#     if not country_code:
#         return ""
#     code = country_code.lower().strip()
#     # Import flag in svg format by Flagcdn
#     return f'<img src="https://flagcdn.com/{code}.svg"/>'