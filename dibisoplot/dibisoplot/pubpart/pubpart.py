from typing import Any
import traceback

from openalex_analysis.data import WorksData
from openalex_analysis.data import config as openalex_analysis_config
import pandas as pd
from pyalex import Institutions

from dibisoplot.utils import format_structure_name
from dibisoplot.dibisoplot import DataStatus, Dibisoplot

# bug fix: https://github.com/plotly/plotly.py/issues/3469
import plotly.io as pio
pio.kaleido.scope.mathjax = None

openalex_analysis_config.n_max_entities = 1e6


class PubPart(Dibisoplot):
    """
    Base class for generating plots and tables from data fetched from OpenAlex for the PubPart report (Publications and
    Partnerships report).
    The fetch methods are located in each child class.
    This class is not designed to be called directly but rather to provide general methods to the different plot types.

    :cvar default_margin: Default margins for plots.
    :cvar orientation: Orientation for plots ('h' for horizontal).
    """

    default_margin = dict(l=30, r=30, b=30, t=30, pad=4)
    orientation = 'h'

    def __init__(
            self,
            entity_id,
            year: int | None = None,
            barcornerradius: int = 10,
            dynamic_height: bool = True,
            dynamic_min_height: int | float = 150,
            dynamic_height_per_bar: int | float = 25,
            entity_openalex_filter_field: str = "authorships.institutions.id",
            height: int = 600,
            language: str = "fr",
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

        :param entity_id: The OpenAlex ID for the secondary entity.
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
        :param entity_openalex_filter_field: Field to filter on in the OpenAlex API.
            Default to 'authorships.institutions.id'.
            The list of possible values can be found in the OpenAlex documentation:
            https://docs.openalex.org/api-entities/works/filter-works
        :type entity_openalex_filter_field: str, optional
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
        super().__init__(
            entity_id = entity_id,
            year = year,
            barcornerradius = barcornerradius,
            dynamic_height = dynamic_height,
            dynamic_min_height = dynamic_min_height,
            dynamic_height_per_bar = dynamic_height_per_bar,
            height = height,
            language = language,
            legend_pos = legend_pos,
            main_color = main_color,
            margin = margin,
            max_entities = max_entities,
            max_plotted_entities = max_plotted_entities,
            template = template,
            text_position = text_position,
            title = title,
            width = width
        )
        self.entity_openalex_filter_field = entity_openalex_filter_field


class PubInstitutions(PubPart):
    """
    A class to fetch and plot data about institutions in publications.
    """

    def __init__(
            self,
            entity_id: str,
            year: int | None = None,
            collaboration_type: list[str] = None,
            countries_to_include: list[str] = None,
            countries_to_exclude: list[str] = None,
            ignore_institutions_from_lineage: bool = True,
            institutions_to_ignore: list[str] = None,
            **kwargs
    ):
        """
        Initialize the PubInstitutions class.

        :param entity_id: The OpenAlex ID for the secondary entity.
        :type entity_id: str
        :param year: The year for which to fetch data. If None, uses the current year.
        :type year: int | none, optional
        :param collaboration_type: Type of collaborations (from the ROR type controlled vocabulary). Default to None.
            If None, use all types of institutions.
        :type collaboration_type: list[str]
        :param countries_to_include: List of country codes to include in the plot. Default to None. If not None, only
            collaborations from countries in this list will be included in the plot.
        :type countries_to_include: list[str] | None, optional
        :param countries_to_exclude: List of country codes to exclude from the plot. Default to None. If not None,
            countries from the list will be excluded from the plot.
        :type countries_to_exclude: list[str] | None, optional
        :param ignore_institutions_from_lineage: Whether to ignore institutions from the lineage. Default to True.
        :type ignore_institutions_from_lineage: bool
        :param institutions_to_ignore: List of institutions to not plot.
        :type institutions_to_ignore: list[str]
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        """
        super().__init__(entity_id, year, **kwargs)
        self.collaboration_type = collaboration_type
        if countries_to_include is not None:
            countries_to_include = [c.upper() for c in countries_to_include]
        self.countries_to_include = countries_to_include
        if countries_to_exclude is not None:
            countries_to_exclude = [c.upper() for c in countries_to_exclude]
        self.countries_to_exclude = countries_to_exclude
        self.ignore_institutions_from_lineage = ignore_institutions_from_lineage
        if institutions_to_ignore is None:
            self.institutions_to_ignore = []
        else:
            self.institutions_to_ignore = [
                i.upper() if i.startswith("https://openalex.org/") else "https://openalex.org/" + i.upper()
                for i in institutions_to_ignore
            ]


    def fetch_data(self) -> dict[str, Any]:
        """
        Fetch data about collaborations from OpenAlex

        :return: The info about the fetched data.
        :rtype: dict[str, Any]
        """
        try:
            self.data = {}
            # entities to exclude
            if self.ignore_institutions_from_lineage:
                entities_to_exclude = [e["id"] for e in Institutions()[self.entity_id]["associated_institutions"]]
            else:
                entities_to_exclude = []
            entities_to_exclude.append("https://openalex.org/" + self.entity_id.upper())
            entities_to_exclude.extend(self.institutions_to_ignore)
            w = WorksData(
                extra_filters = {
                    self.entity_openalex_filter_field: self.entity_id,
                    "publication_year": self.year
                }
            )
            for index, row in w.entities_df.iterrows():
                for authorship in row["authorships"]:
                    for institution in authorship["institutions"]:
                        if (
                            institution["id"] not in entities_to_exclude and
                            ((self.collaboration_type is not None and institution["type"] in self.collaboration_type)
                                or self.collaboration_type is None)
                        ):
                            if (
                                (self.countries_to_include is not None
                                 and institution["country_code"] in self.countries_to_include)
                                or (self.countries_to_exclude is not None
                                    and institution["country_code"] not in self.countries_to_exclude)
                                or (self.countries_to_include is None and self.countries_to_exclude is None)
                            ):
                                name = format_structure_name(
                                    str(institution["display_name"]),
                                    str(institution["country_code"])
                                )
                                self.data[name] = self.data.get(name, 0) + 1
            self.n_entities_found = len(self.data)
            # sort values
            self.data = {k: v for k, v in sorted(self.data.items(), key=lambda item: item[1])}
            if not self.data:
                self.data_status = DataStatus.NO_DATA
            else:
                self.data_status = DataStatus.OK
            self.generate_plot_info()
            return {"info": self.info}
        except Exception as e:
            print(f"Error fetching or formatting data: {e}")
            traceback.print_exc()
            self.data = None
            self.data_status = DataStatus.ERROR
            return {"info": self._("Error")}


class PubTopics(PubPart):
    """
    A class to fetch and plot data about openalex topics in publications.
    """

    def fetch_data(self) -> dict[str, Any]:
        """
        Fetch data about topics from OpenAlex

        :return: The info about the fetched data.
        :rtype: dict[str, Any]
        """
        try:
            self.data = {}
            w = WorksData(
                extra_filters = {
                    self.entity_openalex_filter_field: self.entity_id,
                    "publication_year": self.year
                }
            )
            for index, row in w.entities_df.iterrows():
                for topic in row["topics"]:
                    name = topic["display_name"]
                    self.data[name] = self.data.get(name, 0) + 1
            self.n_entities_found = len(self.data)
            # sort values
            self.data = {k: v for k, v in sorted(self.data.items(), key=lambda item: item[1])}
            if not self.data:
                self.data_status = DataStatus.NO_DATA
            else:
                self.data_status = DataStatus.OK
            self.generate_plot_info()
            return {"info": self.info}
        except Exception as e:
            print(f"Error fetching or formatting data: {e}")
            traceback.print_exc()
            self.data = None
            self.data_status = DataStatus.ERROR
            return {"info": self._("Error")}


class Collaborations(PubPart):
    """
    A generic class for fetching and plotting data about collaborations.
    """

    def __init__(
            self,
            entity_id: str,
            year: int | None = None,
            secondary_entity_id: str | list[str] | None = None,
            secondary_entity_filter_field: str | list[str] | None = None,
            **kwargs
    ):
        """
        Initialize the TopicsPotentialCollaborations class.

        :param entity_id: The OpenAlex ID for the secondary entity.
        :type entity_id: str
        :param year: The year for which to fetch data. If None, uses the current year.
        :type year: int | none, optional
        :param secondary_entity_id: The OpenAlex ID for the secondary entity or entities to analyze the topics of
            collaborations. If a work is present in several entities, it is counted only once.
        :type secondary_entity_id: str | list[str] | None
        :param secondary_entity_filter_field: The OpenAlex filter field for the secondary entity or entities. If None,
            use the same as for the main entity. If a single string is provided, it is used for all secondary entities.
        :type secondary_entity_filter_field: str | list[str] | None, optional
        :param kwargs: Additional keyword arguments.
        """
        super().__init__(entity_id, year, **kwargs)
        if secondary_entity_id is None:
            raise ValueError("secondary_entity_id must be provided")
        if isinstance(secondary_entity_id, str):
            self.secondary_entity_id = [secondary_entity_id]
        else:
            self.secondary_entity_id = secondary_entity_id
        if secondary_entity_filter_field is None:
            self.secondary_entity_filter_field = [self.entity_openalex_filter_field] * len(self.secondary_entity_id)
        elif isinstance(secondary_entity_filter_field, str):
            self.secondary_entity_filter_field = [secondary_entity_filter_field] * len(self.secondary_entity_id)
        else:
            self.secondary_entity_filter_field = secondary_entity_filter_field


    def fetch_collab_data(self):
        """
        Fetch data for plots about collaborations.
        """
        self.data = {}
        # to reduce memory consumption when loading the DataFrames and optimize cache uses, load the data year by year:
        if isinstance(self.year, int):
            years = [self.year]
        elif isinstance(self.year, str) and self.year.isnumeric():
            years = [int(self.year)]
        else:
            years = [year for year in range(int(self.year.split("-")[0]), int(self.year.split("-")[1]) + 1)]
        w1 = pd.DataFrame()
        for year in years:
            w = WorksData(
                extra_filters={
                    self.entity_openalex_filter_field: self.entity_id,
                    "publication_year": year
                }
            ).entities_df
            w1 = pd.concat([w1, w], ignore_index=True)
        w2 = pd.DataFrame()
        for year in years:
            for entity, entity_filter in zip(self.secondary_entity_id, self.secondary_entity_filter_field):
                w = WorksData(
                    extra_filters={
                        entity_filter: entity,
                        "publication_year": year
                    }
                ).entities_df
                w2 = pd.concat([w2, w], ignore_index=True)
        # create topic count dicts:
        w1.set_index("id", inplace=True)
        w2.set_index("id", inplace=True)
        wc = w1.loc[w1.index.isin(w2.index)]  # work in common
        return w1, w2, wc


class InstitutionsLineageCollaborations(Collaborations):
    """
    A class to fetch and plot data about institutions in the lineage in co-publications.
    """

    def fetch_data(self) -> dict[str, Any]:
        """
        Fetch data about institutions in the lineage from OpenAlex

        :return: The info about the fetched data.
        :rtype: dict[str, Any]
        """
        try:
            self.data = {}
            inst_id_in_lineage = [e["id"] for e in Institutions()[self.entity_id]["associated_institutions"]]
            w1, w2, wc = self.fetch_collab_data()
            for index, row in wc.iterrows():
                # dict of collabs in the work (count each institution only once per work)
                collabs = {}
                for authorship in row["authorships"]:
                    for institution in authorship["institutions"]:
                        if institution["id"] in inst_id_in_lineage:
                            name = institution["display_name"]
                            collabs[name] = 1
                for collab in collabs.keys():
                    self.data[collab] = self.data.get(collab, 0) + 1
            self.n_entities_found = len(self.data)
            # sort values
            self.data = {k: v for k, v in sorted(self.data.items(), key=lambda item: item[1])}
            if not self.data:
                self.data_status = DataStatus.NO_DATA
            else:
                self.data_status = DataStatus.OK
            self.generate_plot_info()
            return {"info": self.info}
        except Exception as e:
            print(f"Error fetching or formatting data: {e}")
            traceback.print_exc()
            self.data = None
            self.data_status = DataStatus.ERROR
            return {"info": self._("Error")}


class TopicsCollaborations(Collaborations):
    """
    A class to fetch and plot data about openalex topics of collaborations.
    """

    def fetch_data(self) -> dict[str, Any]:
        """
        Fetch data about topics of collaborations from OpenAlex

        :return: The info about the fetched data.
        :rtype: dict[str, Any]
        """
        try:
            self.data_categories = {}
            w1, w2, wc = self.fetch_collab_data()
            for index, row in wc.iterrows():
                for topic in row["topics"]:
                    name = topic["display_name"]
                    self.data[name] = self.data.get(name, 0) + 1
                    self.data_categories[name] = topic["domain"]["display_name"]
            self.n_entities_found = len(self.data)
            # sort values
            self.data = {k: v for k, v in sorted(self.data.items(), key=lambda item: item[1])}
            if not self.data:
                self.data_status = DataStatus.NO_DATA
            else:
                self.data_status = DataStatus.OK
            self.generate_plot_info()
            return {"info": self.info}
        except Exception as e:
            print(f"Error fetching or formatting data: {e}")
            traceback.print_exc()
            self.data = None
            self.data_status = DataStatus.ERROR
            return {"info": self._("Error")}


class TopicsPotentialCollaborations(Collaborations):
    """
    A class to fetch and plot data about openalex topics of potential collaborations.
    """

    def fetch_data(self) -> dict[str, Any]:
        """
        Fetch data about topics of collaborations from OpenAlex

        :return: The info about the fetched data.
        :rtype: dict[str, Any]
        """
        try:
            self.data_categories = {}
            w1, w2, wc = self.fetch_collab_data()
            w_tmp = w1.loc[~w1.index.isin(w2.index)]
            w2 = w2.loc[~w2.index.isin(w1.index)] # works from the secondary entities that are not in the main entity
            w1 = w_tmp # works from the main entity that are not in secondary entities
            topics_info = {} # a dict to store the topics by their ids
            topics_main = {} # a dict to store the topics count from the main entity
            topics_secondary = {} # a dict to store the topics count from the secondary entities
            topics_collaborations = {} # a dict to store the topics count from the collaborations
            for index, row in w1.iterrows():
                for topic in row["topics"]:
                    topic_id = topic["id"]
                    topics_info[topic_id] = topic
                    topics_main[topic_id] = topics_main.get(topic_id, 0) + 1
            for index, row in w2.iterrows():
                for topic in row["topics"]:
                    topic_id = topic["id"]
                    topics_info[topic_id] = topic
                    topics_secondary[topic_id] = topics_secondary.get(topic_id, 0) + 1
            for index, row in wc.iterrows():
                for topic in row["topics"]:
                    topic_id = topic["id"]
                    topics_collaborations[topic_id] = topics_collaborations.get(topic_id, 0) + 1
            # calculate topic scores:
            topic_scores = {}
            for topic_id in topics_main.keys():
                collab_rate = topics_collaborations.get(topic_id, 0) / topics_main[topic_id]
                score = topics_main[topic_id] * topics_secondary.get(topic_id, 0) * (1 - collab_rate)
                topic_scores[topic_id] = score
            # generate data for plot:
            for topic_id in topic_scores:
                name = topics_info[topic_id]["display_name"]
                self.data[name] = topic_scores[topic_id]
                self.data_categories[name] = topics_info[topic_id]["domain"]["display_name"]
            self.n_entities_found = len(self.data)
            # sort values
            self.data = {k: v for k, v in sorted(self.data.items(), key=lambda item: item[1])}
            if not self.data:
                self.data_status = DataStatus.NO_DATA
            else:
                self.data_status = DataStatus.OK
            self.generate_plot_info()
            return {"info": self.info}
        except Exception as e:
            print(f"Error fetching or formatting data: {e}")
            traceback.print_exc()
            self.data = None
            self.data_status = DataStatus.ERROR
            return {"info": self._("Error")}


class WorksCollaborations(Collaborations):
    """
    A class to fetch and plot data about co-publications.
    By default, works are sorted by their citation_normalized_percentile value on OpenAlex, see documentation:
    https://docs.openalex.org/api-entities/works/work-object#citation_normalized_percentile
    Otherwise, it is possible to sort by the cited_by_count.

    :cvar default_margin: Default margins for plots.
    """

    default_margin = dict(l=30, r=45, b=30, t=30, pad=4)

    def __init__(
            self,
            entity_id: str,
            year: int | None = None,
            metric: str = "citation_normalized_percentile",
            **kwargs
    ):
        """
        Initialize the WorksCollaborations class.

        :param entity_id: The OpenAlex ID for the secondary entity.
        :type entity_id: str
        :param year: The year for which to fetch data. If None, uses the current year.
        :type year: int | none, optional
        :param metric: The metric to use for sorting the works. Default to "citation_normalized_percentile".
           Can be "cited_by_count" or "citation_normalized_percentile".
        :type metric: str, optional
        :param kwargs: Additional keyword arguments.
        """
        super().__init__(entity_id, year, **kwargs)
        self.metric = metric

    def fetch_data(self) -> dict[str, Any]:
        """
        Fetch data about co-publications from OpenAlex

        :return: The info about the fetched data.
        :rtype: dict[str, Any]
        """
        try:
            w1, w2, wc = self.fetch_collab_data()
            for index, row in wc.iterrows():
                if len(row["authorships"]) > 1:
                    author_name = row["authorships"][0]["author"]["display_name"] + " et al."
                elif len(row["authorships"]) == 1:
                    author_name = row["authorships"][0]["author"]["display_name"]
                else:
                    author_name = ""
                name = f"{author_name} ({row["publication_year"]}): {row["display_name"]}"
                if len(name) > 100:
                    name = name[:100] + "..."
                val = row[self.metric]
                if self.metric == "cited_by_count":
                    self.data[name] = val
                else:
                    self.data[name] = val["value"] if val is not None else 0
            self.n_entities_found = len(self.data)
            # sort values
            self.data = {k: v for k, v in sorted(self.data.items(), key=lambda item: item[1])}
            if not self.data:
                self.data_status = DataStatus.NO_DATA
            else:
                self.data_status = DataStatus.OK
            self.generate_plot_info()
            return {"info": self.info}
        except Exception as e:
            print(f"Error fetching or formatting data: {e}")
            traceback.print_exc()
            self.data = None
            self.data_status = DataStatus.ERROR
            return {"info": self._("Error")}
