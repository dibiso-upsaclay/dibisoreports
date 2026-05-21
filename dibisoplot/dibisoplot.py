from enum import Enum

import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

from dibisoplot.translation import get_translator
import html as html_lib

from dibisoplot.utils import get_empty_plot_with_message, get_bar_width


class DataStatus(Enum):
    """Status of the data."""
    NOT_FETCHED = 0
    OK = 1
    NO_DATA = 2
    ERROR = 3


class Dibisoplot:
    """
    Base class for generating plots and tables from data fetched from various APIs.
    The fetch methods are located in each child classes.
    This class is not designed to be called directly but rather to provide general methods to the different plot types.

    :cvar orientation: Orientation for plots ('v' for vertical, 'h' for horizontal).
    :cvar figure_file_extension: File extension of the figure (pdf, tex...).
    :cvar default_dynamic_bar_width: Default width for bars in plots when the height is set dynamically.
    :cvar default_height: Default height for plots.
    :cvar default_legend_pos: Default position for the legend.
    :cvar default_margin: Default margins for plots.
    """

    # TODO: change default orientation value to 'h'
    orientation = 'v'
    figure_file_extension = "pdf"
    html_figure_type = "plotly"  # "plotly" | "html_table" | "html_list"

    default_dynamic_bar_width = 0.7
    default_height = 600
    default_legend_pos = dict(x=1, y=0, xanchor='right', yanchor='bottom')
    default_margin = dict(l=15, r=15, b=15, t=15, pad=4)

    def __init__(
            self,
            entity_id,
            year: int | None = None,
            barcornerradius: int = 10,
            dynamic_height: bool = True,
            dynamic_min_height: int | float = 150,
            dynamic_height_per_bar: int | float = 25,
            height: int = 600,
            language: str = "en",
            legend_pos: dict = None,
            main_color: str = "blue",
            margin: dict = None,
            max_entities: int | None = 1000,
            max_plotted_entities: int = 25,
            template: str = "simple_white",
            text_position: str = "outside",
            title: str | None = None,
            width: int = 800,
    ):
        """
        Initialize the Biso class with the given parameters.

        :param entity_id: The HAL collection identifier. This usually refers to the entity id acronym.
        :type entity_id: str
        :param year: The year for which to fetch data. If None, uses the current year.
        :type year: int | none, optional
        :param barcornerradius: Corner radius for bars in plots.
        :type barcornerradius: int, optional
        :param dynamic_height: Whether to use dynamic height for the plot. Only implemented for horizontal bar plots.
        :type dynamic_height: bool, optional
        :param dynamic_min_height: Minimum height for the plot when the height is set dynamically.
        :type dynamic_min_height: int | float, optional
        :param dynamic_height_per_bar: Height per bar for plots when the height is set dynamically.
        :type dynamic_height_per_bar: int | float, optional
        :param height: Height of the plot.
        :type height: int, optional
        :param language: Language for the plot. Default to 'fr'.
        :type language: str, optional
        :param legend_pos: Position of the legend.
        :type legend_pos: dict, optional
        :param main_color: Main color for the plot.
        :type main_color: str, optional
        :param margin: Margins for the plot.
        :type margin: dict, optional
        :param max_entities: Default maximum number of entities used to create the plot. Default 1000.
            Set to None to disable the limit. This value limits the number of queried entities when doing analysis.
            For example, when creating the collaboration map, it limits the number of works to query from HAL to extract
            the collaborating institutions from.
        :type max_entities: int | None, optional
        :param max_plotted_entities: Maximum number of bars in the plot or rows in the table. Default to 25.
        :type max_plotted_entities: int, optional
        :param template: Template for the plot.
        :type template: str, optional
        :param text_position: Position of the text on bars.
        :type text_position: str, optional
        :param title: Title of the plot.
        :type title: str | None, optional
        :param width: Width of the plot.
        :type width: int, optional
        """
        self.entity_id = entity_id
        if year is None:
            # get current year
            self.year = datetime.now().year
        else:
            self.year = year
        self.barcornerradius = barcornerradius
        self.dynamic_height = dynamic_height
        self.dynamic_min_height = dynamic_min_height
        self.dynamic_height_per_bar = dynamic_height_per_bar
        self.height = height
        self.language = language
        if legend_pos is None:
            self.legend_pos = self.default_legend_pos
        else:
            self.legend_pos = legend_pos
        self.main_color = main_color
        if margin is None:
            self.margin = self.default_margin
        else:
            self.margin = margin
        self.max_entities = max_entities
        self.max_plotted_entities = max_plotted_entities
        self.template = template
        self.text_position = text_position
        self.title = title
        self.width = width

        self.data = None
        self.data_categories = None
        self.data_status = DataStatus.NOT_FETCHED
        self.n_entities_found = None
        # self.max_entities_reached is set to True if the number of processed entities was limited by max_entities
        self.max_entities_reached = False
        self.info = ""

        self._ = get_translator(language = self.language)


    def generate_plot_info(
            self,
            hide_max_entities_reached_warning: bool = False,
            hide_n_entities_warning: bool = False
    ):
        """
        Generate the plot info string (plain text / HTML).
        Used to display warnings in the HTML report.
        """
        parts = []
        if self.max_entities_reached and not hide_max_entities_reached_warning:
            parts.append(
                "⚠️ " +
                self._("The data processing was limited by the maximum number of downloadable entities (") +
                str(self.max_entities) +
                self._("). Data can be missing or values can be lower than the real values.")
            )
        if (self.n_entities_found is not None and self.n_entities_found > self.max_plotted_entities and
                not hide_n_entities_warning):
            cls = self.__class__.__name__
            if cls in ("AnrProjects", "EuropeanProjects"):
                prefix = self._("The number of displayed projects was limited to ")
                suffix = self._(f" projects were found.")
            elif cls == "Chapters":
                prefix = self._("The number of displayed chapters was limited to ")
                suffix = self._(" chapters were found.")
            elif cls in ("CollaborationNames", "PrivateSectorCollaborations"):
                prefix = self._("The number of displayed collaborations was limited to ")
                suffix = self._(" collaborations were found.")
            elif cls == "Conferences":
                prefix = self._("The number of displayed conferences was limited to ")
                suffix = self._(" conferences were found.")
            elif cls in ("Journals", "JournalsHal"):
                prefix = self._("The number of displayed journals was limited to ")
                suffix = self._(" journals were found.")
            elif cls == "WorksBibtex":
                prefix = self._("The number of displayed works was limited to ")
                suffix = self._(" works were found.")
            elif cls == "WorksType":
                prefix = self._("The number of displayed work types was limited to ")
                suffix = self._(" work types were found.")
            else:
                prefix = self._("The number of displayed entities was limited to ")
                suffix = self._(" entities were found.")
            parts.append(
                prefix + str(self.max_plotted_entities) +
                self._(". In the API, ") + str(self.n_entities_found) + suffix
            )
        self.info = " ".join(parts)


    def get_no_data_plot(self) -> go.Figure:
        """Create the no-data plot."""
        return get_empty_plot_with_message(self._("No data"))


    def get_error_plot(self) -> go.Figure:
        """Create the error plot."""
        return get_empty_plot_with_message(self._("Error while making the plot"))


    def get_no_data_html(self) -> str:
        """Create the no-data HTML fragment."""
        return f'<div class="dibiso-no-data">{html_lib.escape(self._("No data"))}</div>'


    def get_error_html(self) -> str:
        """Create the error HTML fragment."""
        return f'<div class="dibiso-error">{html_lib.escape(self._("Error while making the table"))}</div>'


    def figure_to_svg(self, fig: go.Figure) -> str:
        """Export a Plotly figure as an SVG string (for WeasyPrint PDF path)."""
        return fig.to_image(format="svg").decode("utf-8")


    def figure_to_html_fragment(self, fig: go.Figure) -> str:
        """Export a Plotly figure as an embeddable HTML div (no full page, no Plotly JS bundle)."""
        return fig.to_html(full_html=False, include_plotlyjs=False)


    def dataframe_to_html_table(
            self,
            table_df,
            caption: str | None = None,
            label: str | None = None,
            max_plotted_entities: int | None = None,
    ) -> str:
        """
        Convert a pandas DataFrame to an HTML table fragment wrapped in a <figure>.

        :param table_df: pandas DataFrame to convert.
        :param caption: Optional caption rendered as <figcaption>.
        :param label: Optional id attribute on the <figure> element.
        :param max_plotted_entities: If set, truncate to this many rows with a notice.
        :return: HTML string.
        """
        if table_df.empty:
            return f'<p class="dibiso-no-data">{html_lib.escape(self._("No data"))}</p>'

        rows = []
        truncated = False
        total_rows = len(table_df)

        for i, (_, row) in enumerate(table_df.iterrows()):
            if max_plotted_entities is not None and i >= max_plotted_entities:
                if not (self.n_entities_found is not None and total_rows < self.n_entities_found):
                    truncated = True
                    truncated_at = i
                    truncated_total = total_rows
                break
            cells = "".join(
                f"<td>{html_lib.escape(str(v)) if not pd.isna(v) else ''}</td>"
                for v in row
            )
            rows.append(f"<tr>{cells}</tr>")

        if self.n_entities_found is not None and total_rows < self.n_entities_found:
            truncated = True
            truncated_at = total_rows
            truncated_total = self.n_entities_found

        headers = "".join(
            f"<th>{html_lib.escape(str(c))}</th>" for c in table_df.columns
        )
        tbody_rows = "\n".join(rows)

        notice = ""
        if truncated:
            notice = (
                f'<p class="dibiso-truncation-notice">'
                f'{html_lib.escape(self._("Only"))} {truncated_at} '
                f'{html_lib.escape(self._("displayed lines out of"))} {truncated_total}.'
                f'</p>'
            )

        id_attr = f' id="{html_lib.escape(label)}"' if label else ""
        caption_html = f"<figcaption>{html_lib.escape(caption)}</figcaption>" if caption else ""

        return (
            f'<figure class="dibiso-table"{id_attr}>'
            f"{caption_html}"
            f'<table><thead><tr>{headers}</tr></thead>'
            f'<tbody>{tbody_rows}</tbody></table>'
            f"{notice}"
            f'</figure>'
        )


    def dataframe_to_longtable(
            self,
            table_df,
            alignments: list | None = None,
            caption: str | None = None,
            label: str | None = None,
            vertical_lines: bool = True,
            classic_horizontal_lines: bool = False,
            minimal_horizontal_lines: bool = True,
            max_plotted_entities: int | None = None,
    ) -> str:
        """
        Convert a pandas DataFrame to LaTeX longtable code without document headers.

        This function generates LaTeX code for a longtable from a pandas DataFrame. It handles various formatting options
        such as alignments, captions, labels, and lines between rows and columns.

        :param table_df: pandas DataFrame to convert.
        :type table_df: pd.DataFrame
        :param alignments: List of column alignments (e.g., ['l', 'c', 'r']).
        :type alignments: list | None, optional
        :param caption: Caption for the table.
        :type caption: str | None , optional
        :param label: Label for referencing the table.
        :type label: str | None, optional
        :param vertical_lines: Whether to include vertical lines between columns.
        :type vertical_lines: bool, optional
        :param classic_horizontal_lines: Whether to include horizontal lines between rows in a classic style.
        :type classic_horizontal_lines: bool, optional
        :param minimal_horizontal_lines: Whether to include minimal horizontal lines between rows.
        :type minimal_horizontal_lines: bool, optional
        :param max_plotted_entities: Maximum number of entities to show in the table. If None, show all entities in the
            table.
        :type max_plotted_entities: int | None, optional
        :return: LaTeX code for the longtable (without document headers).
        :rtype: str
        :raises AttributeError: If both classic_horizontal_lines and minimal_horizontal_lines are True.
        :raises ValueError: If the number of alignments does not match the number of columns.
        """
        def escape_latex(s: str) -> str:
            """
            Escape LaTeX special characters in a string.

            :param s: String to escape.
            :type s: str
            :return: Escaped string with LaTeX special characters.
            :rtype: str
            """
            if pd.isna(s):
                return ''
            s = str(s)
            replacements = {
                '&': '\\&',
                '%': '\\%',
                '$': '\\$',
                '#': '\\#',
                '_': '\\_',
            }
            for char, escaped in replacements.items():
                s = s.replace(char, escaped)
            return s

        if table_df.empty:
            latex_lines = [self._("No data")]
        else:
            if classic_horizontal_lines and minimal_horizontal_lines:
                raise AttributeError("classic_horizontal_lines and minimal_horizontal_lines cannot both be True")

            num_cols = len(table_df.columns)

            if alignments is None:
                alignments = ['l'] * num_cols
            else:
                if len(alignments) != num_cols:
                    raise ValueError("Number of alignments must match number of columns")

            if vertical_lines:
                col_spec = '|' + '|'.join(alignments) + '|'
            else:
                col_spec = ''.join(alignments)

            latex_lines = []

            # Begin longtable
            latex_lines.append(f'\\begin{{longtable}}{{{col_spec}}}')

            # Add caption and label after header (but before any \hline)
            if caption is not None:
                latex_lines.append(f'\\caption{{{escape_latex(caption)}}}')
            if label is not None:
                latex_lines.append(f'\\label{{{label}}}\\\\')

            if classic_horizontal_lines:
                latex_lines.append('\\hline')
            if minimal_horizontal_lines:
                latex_lines.append('\\toprule')

            # Add header row
            header = table_df.columns.tolist()
            header_line = ' & '.join([escape_latex(str(x)) for x in header]) + ' \\\\'
            latex_lines.append(header_line)

            if classic_horizontal_lines:
                latex_lines.append('\\hline')
            if minimal_horizontal_lines:
                latex_lines.append('\\midrule')

            # Add data rows with horizontal lines between them if specified
            i = 0
            for i, (_, row) in enumerate(table_df.iterrows()):
                # add the number of displayed rows when there are too many rows in dataframe (aka there was no limit in
                # API requests)
                if max_plotted_entities is not None and i >= max_plotted_entities:
                    # if we are not in the case that the number of entities found in the API is higher than the number
                    # of returned entities by the API
                    if not(self.n_entities_found is not None and len(table_df.index) < self.n_entities_found):
                        latex_lines.append(
                            '\\textbf{' + self._("Only") + ' ' + str(i) + ' ' + self._("displayed lines out of") + ' ' +
                            str(len(table_df.index)) + '.} \\\\'
                        )
                    break
                row_values = []
                for item in row:
                    row_values.append(escape_latex(item) if not pd.isna(item) else '')
                row_line = ' & '.join(row_values) + ' \\\\'
                latex_lines.append(row_line)

                # Add \hline after each data row except the last one
                if classic_horizontal_lines and i < len(table_df) - 1:
                    latex_lines.append('\\hline')
            # add the number of displayed rows when more entities where found in the API compared to the number of rows
            # in the dataframe
            if self.n_entities_found is not None and len(table_df.index) < self.n_entities_found:
                latex_lines.append(
                    '\\textbf{' + self._("Only") + ' ' + str(i + 1) + ' ' + self._("displayed lines out of") + ' ' +
                    str(self.n_entities_found) + '.} \\\\'
                )

            # Add a final \hline
            if classic_horizontal_lines:
                latex_lines.append('\\hline')
            if minimal_horizontal_lines:
                latex_lines.append('\\bottomrule')

            # End longtable
            latex_lines.append('\\end{longtable}')

        latex_lines.append('')

        latex_code = '\n'.join(latex_lines)

        return latex_code


    def get_figure(self) -> go.Figure:
        """
        Generate a bar plot based on the fetched data.

        :return: The plotly figure.
        :rtype: go.Figure
        """
        if self.data_status == DataStatus.NOT_FETCHED:
            self.fetch_data()
        if self.data_status == DataStatus.NO_DATA:
            return self.get_no_data_plot()
        if self.data_status == DataStatus.ERROR:
            return self.get_error_plot()
        # NOTE: subclasses with html_figure_type "html_table"/"html_list" override this method entirely

        # TODO: move sorting from fetch_data to here
        # keep only the first max_plotted_entities items in the dictionary
        self.data = dict(list(self.data.items())[-self.max_plotted_entities:])

        if self.dynamic_height and self.orientation == 'h':
            height = self.dynamic_height_per_bar*len(self.data.keys())
            if height < self.dynamic_min_height:
                height = self.dynamic_min_height
            bar_width = self.default_dynamic_bar_width
        else:
            height = self.height
            bar_width = get_bar_width(len(self.data.keys()))

        fig = go.Figure()

        if self.data_categories is not None:
            # Get all unique categories, sort to keep order consistent across re-runs for colors
            unique_categories = sorted(set(self.data_categories.values()))
            # Assign a color to each unique category
            colors = px.colors.qualitative.Bold[:len(unique_categories)]
            for category, color in zip(unique_categories, colors):
                values = [self.data[key] if self.data_categories[key] == category else 0 for key in self.data.keys()]
                if self.orientation == 'v':
                    x_values = list(self.data.keys())
                    y_values = values
                else:
                    x_values = values
                    y_values = list(self.data.keys())

                fig.add_trace(go.Bar(
                    x=x_values,
                    y=y_values,
                    name=category,
                    showlegend=True,
                    marker_color=color,
                    orientation=self.orientation,
                    text=list(self.data.values()),
                    textposition=self.text_position,
                    textangle=0,
                    cliponaxis=False,
                    width=bar_width,
                ))
        else:
            if self.orientation == 'v':
                x_values = list(self.data.keys())
                y_values = list(self.data.values())
            else:
                x_values = list(self.data.values())
                y_values = list(self.data.keys())
            fig.add_trace(go.Bar(
                x=x_values,
                y=y_values,
                showlegend=False,
                marker_color=self.main_color,
                orientation=self.orientation,
                text=list(self.data.values()),
                textposition=self.text_position,
                textangle=0,
                cliponaxis=False,
                width=bar_width,
            ))

        fig.update_layout(
            barmode='stack',
            barcornerradius=self.barcornerradius,
            width=self.width,
            height=height,
            template=self.template,
            legend=self.legend_pos,
            margin=self.margin,
            # xaxis = dict(dtick = 1), # TODO: fix for big values
        )
        if self.title is not None:
            fig.update_layout(title=self.title)

        return fig
