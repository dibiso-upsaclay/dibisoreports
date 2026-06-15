from datetime import datetime
import json
import logging
import os
from os.path import dirname, join, isdir, abspath
import re
import shutil
import subprocess
import tempfile
import warnings
import zipfile


logging.captureWarnings(True)
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class DibisoReporting:
    """
    Class to generate HTML/PDF reports using Jinja2 templates.

    :cvar figures_dir_name: Directory where figures are stored.
    :cvar class_mapping: Dictionary that maps class names to actual classes.
    :cvar default_plot_main_color: Default color for the main plot.
    :cvar default_visualizations: Dictionary of default visualizations to include.
    """

    figures_dir_name = "figures"
    class_mapping = {}
    default_plot_main_color = "blue"
    default_visualizations = {}

    def __init__(
            self,
            entity_id: str = "",
            year: int | None = None,
            html_template_path: str | None = None,
            html_template_url: str | None = None,
            max_entities: int | None = 1000,
            max_plotted_entities: int = 25,
            plot_main_color: str | None = None,
            root_path: str | None = None,
            **kwargs,
    ):
        """
        Initialize the DibisoReporting class.

        :param entity_id: The ID of the entity (e.g. HAL collection identifier).
        :param year: Year of the report. Defaults to current year.
        :param html_template_path: Local path to the HTML template directory.
        :param html_template_url: GitHub release URL to download the HTML template.
        :param max_entities: Max entities to query from APIs (None = unlimited).
        :param max_plotted_entities: Max bars/rows in visualizations.
        :param plot_main_color: Main Plotly color for charts.
        :param root_path: Output directory for the report.
        """
        self.entity_id = entity_id
        self.year = datetime.now().year if year is None else year
        self.html_template_path = html_template_path
        self.html_template_url = html_template_url
        self.max_entities = max_entities
        self.max_plotted_entities = max_plotted_entities
        self.plot_main_color = plot_main_color if plot_main_color is not None else self.default_plot_main_color

        if root_path is None:
            raise AttributeError('root_path cannot be None')
        if isdir(dirname(abspath(root_path))):
            os.makedirs(root_path, exist_ok=True)
        else:
            raise ValueError(f"Unable to find path: {dirname(abspath(root_path))}")
        self.root_path = abspath(root_path)
        self.fig_dir_path = join(self.root_path, self.figures_dir_name)
        os.makedirs(self.fig_dir_path, exist_ok=True)

        self.macros_variables = {}
        self._html_figures = {}

        self.kwargs = kwargs

    # ── Template acquisition ────────────────────────────────────────────

    def get_html_template_from_path(self):
        """Copy the HTML template directory into root_path."""
        if self.html_template_path is None:
            raise ValueError("No HTML template path provided")
        if not os.path.exists(self.html_template_path):
            raise FileNotFoundError(f"HTML template path does not exist: {self.html_template_path}")
        if not os.path.isdir(self.html_template_path):
            raise ValueError(f"HTML template path is not a directory: {self.html_template_path}")

        _skip = {".git", ".hg", ".svn", "__pycache__"}
        for item in os.listdir(self.html_template_path):
            if item in _skip:
                continue
            src = os.path.join(self.html_template_path, item)
            dst = os.path.join(self.root_path, item)
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        log.info("HTML template copied from path.")

    def get_html_template_from_github(self):
        """Download the latest GitHub release ZIP and extract it into root_path."""
        if self.html_template_url is None:
            raise ValueError("No HTML template URL provided")

        if "github.com" in self.html_template_url and "/releases/latest" in self.html_template_url:
            url_parts = (self.html_template_url
                         .replace("https://github.com/", "")
                         .replace("/releases/latest", ""))
            api_url = f"https://api.github.com/repos/{url_parts}/releases/latest"
        else:
            api_url = self.html_template_url

        cmd = f'curl -s {api_url} | grep "browser_download_url.*zip" | cut -d \'"\' -f 4'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        download_url = result.stdout.strip()
        if not download_url:
            raise ValueError("No zip download URL found in the GitHub API response")

        with tempfile.TemporaryDirectory() as tmp:
            zip_path = os.path.join(tmp, "template.zip")
            subprocess.run(f"wget -q -O {zip_path} {download_url}", shell=True, check=True)
            extract_dir = os.path.join(tmp, "extracted")
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(extract_dir)
            contents = os.listdir(extract_dir)
            source_dir = (
                os.path.join(extract_dir, contents[0])
                if len(contents) == 1 and os.path.isdir(os.path.join(extract_dir, contents[0]))
                else extract_dir
            )
            for item in os.listdir(source_dir):
                src = os.path.join(source_dir, item)
                dst = os.path.join(self.root_path, item)
                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
        log.info("HTML template downloaded and extracted from GitHub.")

    # ── Figure saving ───────────────────────────────────────────────────

    def _save_figure_as_html(self, viz, fig, file_name: str) -> str:
        """
        Save a figure as SVG (for WeasyPrint PDF) and return an HTML fragment.

        - "plotly": saves .svg, returns interactive Plotly HTML fragment
        - "html_table" / "html_list": fig is already an HTML string
        """
        html_type = getattr(viz.__class__, "html_figure_type", "plotly")

        if html_type == "plotly":
            svg_str = viz.figure_to_svg(fig)
            svg_path = join(self.fig_dir_path, file_name + ".svg")
            with open(svg_path, "w", encoding="utf-8") as f:
                f.write(svg_str)
            return viz.figure_to_html_fragment(fig)

        # html_table or html_list: fig is already the HTML string
        return fig

    # ── Intermediate data persistence ───────────────────────────────────

    def _save_intermediate(self):
        """Persist figures and context to JSON for deferred rendering."""
        with open(join(self.root_path, "figures.json"), "w", encoding="utf-8") as f:
            json.dump(self._html_figures, f, ensure_ascii=False)
        with open(join(self.root_path, "context.json"), "w", encoding="utf-8") as f:
            json.dump(self.macros_variables, f, ensure_ascii=False, default=str)
        log.info("Saved figures.json and context.json.")

    # ── Deferred HTML rendering ─────────────────────────────────────────

    @classmethod
    def render_from_saved(cls, root_path: str, analyses: dict[str, str]) -> None:
        """
        Re-render the HTML report from saved figures.json + context.json,
        injecting user-written analyses (already converted to HTML).

        :param root_path: Directory containing figures.json, context.json and the dibiso-html/ template dir.
        :param analyses: Dict mapping section_id to HTML string (Markdown pre-rendered server-side).
        """
        from jinja2 import Environment, FileSystemLoader

        root_path = abspath(root_path)
        with open(join(root_path, "figures.json"), encoding="utf-8") as f:
            figures = json.load(f)
        with open(join(root_path, "context.json"), encoding="utf-8") as f:
            context = json.load(f)

        # Replace interactive Plotly HTML fragments with inline SVG when available.
        # SVGs render correctly in both WeasyPrint (no JS) and browsers (no layout quirks).
        figures_dir = join(root_path, "figures")
        for fig_name in list(figures.keys()):
            svg_path = join(figures_dir, f"{fig_name}.svg")
            if os.path.exists(svg_path):
                with open(svg_path, encoding="utf-8") as svgf:
                    svg_content = svgf.read()
                # Remove fixed width/height attributes from the SVG root so CSS can scale it.
                svg_content = re.sub(r'(<svg[^>]*)\s+width="[^"]*"', r'\1', svg_content, count=1)
                svg_content = re.sub(r'(<svg[^>]*)\s+height="[^"]*"', r'\1', svg_content, count=1)
                # Replace Unicode flag emoji (Regional Indicator pairs) with ASCII country codes.
                # WeasyPrint/Cairo cannot render these emoji glyphs.
                svg_content = re.sub(
                    r'([\U0001F1E0-\U0001F1FF])([\U0001F1E0-\U0001F1FF])',
                    lambda m: f"({chr(ord(m.group(1)) - 0x1F1E6 + ord('A'))}{chr(ord(m.group(2)) - 0x1F1E6 + ord('A'))})",
                    svg_content,
                )
                figures[fig_name] = f'<div class="dibiso-svg-figure">{svg_content}</div>'

        context["figures"] = figures
        context["analyses"] = analyses
        context["has_plotly_figures"] = False  # SVG path: no Plotly JS needed

        template_dir = join(root_path, context.get("template_subdir", "dibiso-html"))
        env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
        report_type = context.get("report_type", "biso")
        template_name = f"{report_type}.html.j2"
        html_output = env.get_template(template_name).render(**context)

        with open(join(root_path, "report.html"), "w", encoding="utf-8") as f:
            f.write(html_output)
        log.info(f"Rendered {template_name} → report.html")

        # Also render bibliography companion if works_bibtex is present
        biblio_template = f"{report_type}-biblio.html.j2"
        try:
            biblio_tmpl = env.get_template(biblio_template)
            biblio_html = biblio_tmpl.render(**context)
            with open(join(root_path, "biblio.html"), "w", encoding="utf-8") as f:
                f.write(biblio_html)
            log.info(f"Rendered {biblio_template} → biblio.html")
        except Exception:
            pass  # biblio template optional

    def _get_html_template_pairs(self) -> list[tuple[str, str]]:
        """Return [(template_name, output_filename)] pairs. Overridden by subclasses."""
        return [("biso.html.j2", "report.html")]

    # ── Main report generation ──────────────────────────────────────────

    def generate_report(
            self,
            visualizations_to_make: dict[str, list[dict]] | None = None,
            import_default_visualizations=True
    ):
        """
        Generate the report: fetch data, produce HTML figures, save intermediate JSON,
        acquire templates, then save for deferred rendering at export time.
        """
        if visualizations_to_make is None:
            visualizations_to_make = {}

        # Merge with defaults
        if import_default_visualizations:
            for viz_type, configs in self.default_visualizations.items():
                if viz_type not in visualizations_to_make:
                    visualizations_to_make[viz_type] = configs
                else:
                    for config in configs:
                        for provided in visualizations_to_make[viz_type]:
                            if 'name' in config:
                                if config['name'] == provided.get('name'):
                                    for k, v in config.items():
                                        if k not in provided:
                                            provided[k] = v
                                    break
                            elif (('name' not in config or config['name'] == '') and
                                  ('name' not in provided or provided['name'] == '')):
                                for k, v in config.items():
                                    if k not in provided:
                                        provided[k] = v
                                break
                        else:
                            visualizations_to_make[viz_type].append(config)

        # Generate visualizations
        for viz_type, configs in visualizations_to_make.items():
            if not configs:
                continue
            if viz_type not in self.class_mapping:
                warnings.warn(f"{viz_type} is not a valid visualization type for {self.__class__.__name__}")
                continue

            viz_class = self.class_mapping[viz_type]

            for config in configs:
                name = config.get("name", "")
                stats_to_save = config.get("stats_to_save", {})
                params = {k: v for k, v in config.items() if k not in ("name", "stats_to_save")}
                params.setdefault("entity_id", self.entity_id)
                params.setdefault("year", self.year)
                params.setdefault("max_entities", self.max_entities)
                params.setdefault("max_plotted_entities", self.max_plotted_entities)
                params.setdefault("main_color", self.plot_main_color)
                params.setdefault("language", getattr(self, "language", "fr"))

                viz = viz_class(**params, **self.kwargs)
                stats = viz.fetch_data()
                fig = viz.get_figure()

                snake = re.sub('(?<!^)(?=[A-Z])', '_', viz_class.__name__).lower()
                file_name = f"{snake}_{name}" if name else snake

                html_frag = self._save_figure_as_html(viz, fig, file_name)
                self._html_figures[file_name] = html_frag

                # Collect stats into macros_variables
                if "info" in stats:
                    info_key = (re.sub('(?<!^)(?=[A-Z])', '', viz_class.__name__).lower() +
                                (name or "") + "info")
                    stats_to_save["info"] = info_key
                for stat_key, var_name in stats_to_save.items():
                    val = stats.get(stat_key)
                    if var_name in self.macros_variables:
                        warnings.warn(f"Context variable {var_name} already exists. Overwriting.")
                    self.macros_variables[var_name] = val

        # Persist intermediate data
        self._save_intermediate()

        # Acquire template files
        if self.html_template_path or self.html_template_url:
            try:
                self.get_html_template_from_path()
            except Exception as e:
                if "No HTML template path provided" not in str(e) and \
                   "does not exist" not in str(e) and \
                   "not a directory" not in str(e):
                    log.error(str(e))
                try:
                    self.get_html_template_from_github()
                except Exception as url_e:
                    log.error(str(url_e))
                    warnings.warn("Failed to acquire HTML template. Report will not render until template is provided.")
        else:
            warnings.warn("No HTML template path or URL provided. Figures and context saved; render manually.")
