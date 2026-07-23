from typing import Any
import math
import logging
import warnings
from collections import defaultdict
import traceback
import re

from collections import Counter
from datetime import datetime
from openalex_analysis.data import InstitutionsData, WorksData
import numpy as np
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import requests
from elasticsearch import Elasticsearch

from dibisoplot.utils import get_hal_doc_type_name, format_structure_name
from dibisoplot.dibisoplot import DataStatus, Dibisoplot

# bug fix: https://github.com/plotly/plotly.py/issues/3469
import plotly.io as pio
pio.kaleido.scope.mathjax = None

# catch useless warning logs, e.g.:
# WARNING:pylatexenc.latexencode._unicode_to_latex_encoder:No known latex representation for character
logging.getLogger('pylatexenc').setLevel(logging.ERROR)


class Biso(Dibisoplot):
    """
    Base class for generating plots and tables from data fetched from various APIs.
    The fetch methods are located in each child classes.
    This class is not designed to be called directly but rather to provide general methods to the different plot types.

    :cvar default_hal_cursor_rows_per_request: Default number of rows per request when using the cursor API.
    """

    default_hal_cursor_rows_per_request = 10000

    def __init__(
            self,
            entity_id,
            year: int | None = None,
            barcornerradius: int = 10,
            dynamic_height: bool = True,
            dynamic_min_height: int | float = 150,
            dynamic_height_per_bar: int | float = 25,
            height: int = 600,
            language: str = "fr",
            legend_pos: dict = None,
            main_color: str = "blue",
            margin: dict = None,
            max_entities: int | None = 1000,
            max_plotted_entities: int = 25,
            scanr_api_password: str | None = None,
            scanr_api_port: int = 443,
            scanr_api_scheme: str | None = "https",
            scanr_api_url: str | None = None,
            scanr_api_username: str | None = None,
            scanr_bso_index: str | None = None,
            scanr_bso_version: str | None = None,   # Now calculated dynamically
            scanr_chunk_size: int = 50,
            scanr_publications_index: str | None = None,
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
        :param scanr_api_password: scanR API password.
        :type scanr_api_password: str | None, optional
        :param scanr_api_port: scanR API port. Default to 443.
        :type scanr_api_port: int | None, optional
        :param scanr_api_scheme: scanR API scheme. Default to 'https'.
        :param scanr_api_url: scanR API URL. If None, data won't be queried.
        :type scanr_api_url: str | None, optional
        :param scanr_api_username: scanR API username.
        :type scanr_api_username: str | None, optional
        :param scanr_bso_index: scanR BSO index.
        :type scanr_bso_index: str | None, optional
        :param scanr_bso_version: Version of the BSO data. Default to "2024Q4".
        :type scanr_bso_version: str, optional
        :param scanr_chunk_size: Number of publications to fetch at a time when using the scanR API. Default to 50.
        :type scanr_chunk_size: int, optional
        :param scanr_publications_index: scanR publications index.
        :type scanr_publications_index: str | None, optional
        :param template: Template for the plot.
        :type template: str, optional
        :param text_position: Position of the text on bars.
        :type text_position: str, optional
        :param title: Title of the plot.
        :type title: str | None, optional
        :param width: Width of the plot.
        :type width: int, optional
        """

        # Dynamic calculation of BSO version (last quarter of the previous year)
        if scanr_bso_version is None:
            current_year = datetime.now().year
            scanr_bso_version = f"{current_year - 1}Q4"

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
            max_entities = max_entities,
            max_plotted_entities = max_plotted_entities,
            template = template,
            text_position = text_position,
            title = title,
            width = width
        )
        self.scanr_api_password = scanr_api_password
        self.scanr_api_port = scanr_api_port
        self.scanr_api_scheme = scanr_api_scheme
        self.scanr_api_url = scanr_api_url
        self.scanr_api_username = scanr_api_username
        self.scanr_bso_index = scanr_bso_index
        self.scanr_bso_version = scanr_bso_version
        self.scanr_chunk_size = scanr_chunk_size
        self.scanr_publications_index = scanr_publications_index

        # Security check for BSO version
        if self.scanr_api_url and self.scanr_bso_index:
            self._validate_bso_version()

    def _validate_bso_version(self):
        """
        Check if the dynamically calculated BSO version exists in the Elasticsearch index.
        If the version is not found, automatically switch to the previous year's version.
        """
        try:
            es = self.connect_to_elasticsearch()
            query = {
                "query": {"match_all": {}},
                "_source": [f"oa_details.{self.scanr_bso_version}"],
                "size": 1
            }
            response = es.search(index=self.scanr_bso_index, body=query)
            
            # Check if the returned structure contains our BSO key
            hits = response.get('hits', {}).get('hits', [])
            if hits:
                source = hits[0].get('_source', {}).get('oa_details', {})
                if self.scanr_bso_version not in source:
                    # The dynamically calculated BSO version is not found in the data, fallback to the previous year's version:
                    old_version = self.scanr_bso_version
                    fallback_year = datetime.now().year - 2
                    self.scanr_bso_version = f"{fallback_year}Q4"
                    logging.warning(
                        f"The dynamically calculated BSO version {old_version} is not found in ScanR. "
                        f"Switching to the fallback version : {self.scanr_bso_version}"
                    )
        except Exception as e:
            logging.error(f"Impossible to validate BSO version with Elasticsearch : {e}")

    def get_all_ids_with_cursor(self, id_type = 'doi', doc_types: list[str] | None = None):
        """Get all DOI articles using cursor pagination"""
        id_type_fields = {
            "doi": "doiId_s",
            "hal": "halId_s"
        }
        id_field = id_type_fields[id_type]
        all_ids = []
        cursor_mark = "*"  # Initial cursor

        if doc_types is None:
            doc_types = ["ART", "COMM"]
        doc_type_query = doc_types[0] if len(doc_types) == 1 else f"({' OR '.join(doc_types)})"

        if self.max_entities is None:
            rows_per_request = self.default_hal_cursor_rows_per_request
        else:
            rows_per_request = min(self.default_hal_cursor_rows_per_request, self.max_entities)

        while True:
            # Calculate how many more results we need
            if self.max_entities is not None:
                remaining = self.max_entities - len(all_ids)
                if remaining <= 0:
                    self.max_entities_reached = True
                    logging.warning(f"Max entities reached (plot {self.__class__.__name__}).")
                    break
                current_rows = min(rows_per_request, remaining)
            else:
                current_rows = rows_per_request

            # Build the cursor-based query URL
            cursor_url = (
                f"https://api.archives-ouvertes.fr/search/{self.entity_id}/?q=publicationDateY_i:{self.year} AND "
                f"docType_s:{doc_type_query} AND {id_field}:[* TO *]&wt=json&rows={current_rows}&"
                f"sort=docid asc&cursorMark={cursor_mark}&fl={id_field}"
            )

            try:
                response = requests.get(cursor_url)
                response.raise_for_status()
                data = response.json()

                # Extract IDs from the response
                docs = data.get('response', {}).get('docs', [])
                for doc in docs:
                    if id_field in doc and doc[id_field]:
                        all_ids.append(doc[id_field])

                # Get the next cursor mark
                next_cursor_mark = data.get('nextCursorMark', '')

                # Check if we've reached the end (cursor mark unchanged)
                if next_cursor_mark == cursor_mark:
                    break

                cursor_mark = next_cursor_mark

            except requests.RequestException as e:
                # TODO: manage errors
                print(f"Error fetching data: {e}")
                break

        # Return results (with limit if max_entities is set)
        if self.max_entities is not None:
            print(f"Returning {len(all_ids)} {id_type} (limit at {self.max_entities})")
            if len(all_ids) > self.max_entities:
                self.max_entities_reached = True
                logging.warning(f"Max entities reached (plot {self.__class__.__name__}).")
            return all_ids[:self.max_entities]
        else:
            print(f"Returning all {len(all_ids)} {id_type} ids")
            return all_ids


    def connect_to_elasticsearch(self) -> Elasticsearch:
        """Connect to Elasticsearch using the provided credentials."""
        es = Elasticsearch(
            hosts=[{
                "host": self.scanr_api_url,
                "port": self.scanr_api_port,
                "scheme": self.scanr_api_scheme
            }],
            basic_auth=(self.scanr_api_username, self.scanr_api_password)  # Updated to use basic auth
        )
        return es
    
    
    def get_works_from_es_index_from_id(
            self,
            index: str,
            ids: list[str] | tuple[str],
            fields_to_retrieve: list[str] | tuple[str] | None = None,
            es: Elasticsearch = None,
    ) -> list[dict]:
        """
        Get works by their id from an elasticsearch index.

        :param index: Index to search in.
        :type index: str
        :param ids: List of ids to fetch.
        :type ids: list[str] | tuple[str]
        :param fields_to_retrieve: List of fields to retrieve. If None, all fields are retrieved.
        :type fields_to_retrieve: list[str] | tuple[str] | None
        :param es: Elasticsearch client. If None, a new client is created.
        :type es: Elasticsearch | None
        :return: List of works.
        :rtype: list[dict]
        """
        if es is None:
            es = self.connect_to_elasticsearch()

        # print(f"Retrieving {len(ids)} works from Elasticsearch index {index}...")
        query = {
            "query": {
                "terms": {
                    "id.keyword": ids  # Using .keyword for exact match on non-analyzed field
                }
            },
            "size": len(ids)
        }
        if fields_to_retrieve is not None:
            query["_source"] = fields_to_retrieve

        response = es.search(index=index, body=query)

        # print(f"Retrieved {response['hits']['total']['value']} documents from Elasticsearch.")

        return response['hits']['hits']


    def get_works_from_es_index_from_id_and_private_sector(
            self,
            index: str,
            ids: list[str] | tuple[str],
            fields_to_retrieve: list[str] | tuple[str] | None = None,
            es: Elasticsearch = None,
    ) -> list[dict]:
        """
        Get works which are from the private sector by their id from an elasticsearch index.

        :param index: Index to search in.
        :type index: str
        :param ids: List of ids to fetch.
        :type ids: list[str] | tuple[str]
        :param fields_to_retrieve: List of fields to retrieve. If None, all fields are retrieved.
        :type fields_to_retrieve: list[str] | tuple[str] | None
        :param es: Elasticsearch client. If None, a new client is created.
        :type es: Elasticsearch | None
        :return: List of works.
        :rtype: list[dict]
        """
        if es is None:
            es = self.connect_to_elasticsearch()

        # print(f"Retrieving {len(ids)} works from Elasticsearch index {index}...")
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"terms": {"id.keyword": ids}},
                        {
                            "term": {
                                "affiliations.kind.keyword": "Secteur privé"
                            }
                        }
                    ]
                }
            },
            "size": len(ids)  # Limit the results to the number of IDs provided
        }

        if fields_to_retrieve is not None:
            query["_source"] = fields_to_retrieve

        response = es.search(index=index, body=query)

        # print(f"Retrieved {response['hits']['total']['value']} documents from Elasticsearch.")

        return response['hits']['hits']


    def get_works_from_es_index_from_id_by_chunk(
            self,
            index: str,
            ids: list[str] | tuple[str],
            fields_to_retrieve: list[str] | tuple[str] | None = None,
            query_type: str | None = None,
    ) -> list[dict]:
        """
        Get works by their id from an elasticsearch index by chuncks.

        :param index: Index to search in.
        :type index: str
        :param ids: List of ids to fetch.
        :type ids: list[str] | tuple[str]
        :param fields_to_retrieve: List of fields to retrieve. If None, all fields are retrieved.
        :type fields_to_retrieve: list[str] | tuple[str] | None
        :param query_type: Type of query to use, if None, the query will simply get all the documents by their IDs.
        :type query_type: str | None
        :return: List of works.
        :rtype: list[dict]
        """
        es = self.connect_to_elasticsearch()

        res = []
        for i in range(0, len(ids), self.scanr_chunk_size):
            chunk_id = ids[i:i + self.scanr_chunk_size]
            if query_type == "private_sector":
                res += self.get_works_from_es_index_from_id_and_private_sector(index, chunk_id, fields_to_retrieve, es)
            else:
                res += self.get_works_from_es_index_from_id(index, chunk_id, fields_to_retrieve, es)

        return res

    def _handle_fetch_error(self, exception: Exception, context_msg: str ,return_bso_stats: bool = False, return_map_stats: bool=False, return_oaworks_stats: bool=False) -> dict[str, Any]:
        """
        Factorisation of error handling for data fetching methods.
        Returns a standard error dictionary to be used in the application.
        """
        print(f"{context_msg}: {exception}")
        traceback.print_exc()
        self.data = None
        self.data_status = DataStatus.ERROR
        if return_bso_stats:
            return {
                'nb_works': self._("Error"),
                'nb_works_found_in_bso': self._("Error"),
                'nb_journals': self._("Error"),
                'bso_version': self.scanr_bso_version,
                'info': self._("Error")
            }
        if return_map_stats:
            return {
                'collaborations_nb': self._("Error"),
                'institutions_nb': self._("Error"),
                'countries_nb': self._("Error"),
                'info': self._("Error")
            }
        if return_oaworks_stats:
            return {
                'oa_works_period': f"{self.year_range[0]} - {self.year_range[1]}",
                'info': self._("Error")
            }
        return {'info': self._("Error")}


class AnrProjects(Biso):
    """
    A class to fetch and plot data about ANR projects.

    :cvar orientation: Orientation for plots ('h' for horizontal).
    """

    orientation = 'h'

    def __init__(self, entity_id: str, year: int | None = None, **kwargs):
        """
        Initialize the AnrProjects class.

        :param entity_id: The HAL collection identifier. This usually refers to the entity id acronym.
        :type entity_id: str
        :param year: The year for which to fetch data. If None, uses the current year.
        :type year: int | none, optional
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        """
        super().__init__(entity_id, year, **kwargs)


    def fetch_data(self) -> dict[str, Any]:
        """
        Fetch data about ANR projects from the HAL API.

        This method queries the API to get the list of ANR projects and their counts.
        The data is stored in the `data` attribute as a dictionary where keys are ANR project acronyms
        and values are their respective counts.

        :return: The info about the fetched data.
        :rtype: dict[str, Any]
        """
        try:
            facet_url = (
                f"https://api.archives-ouvertes.fr/search/{self.entity_id}/?q=publicationDateY_i:{self.year}&wt=json&rows=0&"
                f"facet=true&facet.field=anrProjectAcronym_s&facet.limit={self.max_plotted_entities}&facet.mincount=1&"
                "stats=true&stats.field={!count=true+cardinality=true}anrProjectAcronym_s"
            )
            res = requests.get(facet_url).json()
            self.n_entities_found = (res.get('stats', {}).get('stats_fields', {}).get('anrProjectAcronym_s', {}).
                                     get('cardinality', 0))
            anr_projects_list = res.get('facet_counts', {}).get('facet_fields', {}).get('anrProjectAcronym_s', [])
            raw_data = {anr_projects_list[i]: anr_projects_list[i + 1] for i in range(0, len(anr_projects_list), 2)}
            # sort values
            self.data = {}
            for k, v in raw_data.items():
                if re.search(r"^Universit", k, re.IGNORECASE):
                    new_key = "Autres projets"
                    self.data[new_key] = self.data.get(new_key, 0) + v
                else:
                    self.data[k] = v
            self.data = {k: v for k, v in sorted(self.data.items(), key=lambda item: item[1])}
            if not self.data:
                self.data_status = DataStatus.NO_DATA
            else:
                self.data_status = DataStatus.OK
            self.generate_plot_info()
            return {"info": self.info}
        except Exception as e:
            return self._handle_fetch_error(e, "Error fetching or formatting ANR projects data")

class Books(Biso):
    """
    A class to fetch and generate a table of books (ouvrages).
    """

    figure_file_extension = "tex"
    html_figure_type = "html_table"

    def __init__(self, entity_id: str, year: int | None = None, **kwargs):
        """
        Initialize the Books class.
        """
        super().__init__(entity_id, year, **kwargs)

    def fetch_data(self) -> dict[str, Any]:
        """
        Fetch data about books from the HAL API.
        """
        try:
            # Request with docType_s:OUV for full books and authFullName_s for author names
            url = (
                f"https://api.archives-ouvertes.fr/search/{self.entity_id}/?q=*:*&fq=docType_s:OUV&"
                f"fq=producedDateY_i:{self.year}&rows={self.max_plotted_entities}&wt=json&indent=true&"
                f"fl=title_s,publisher_s,authFullName_s"
            )
            books = requests.get(url).json()
            self.n_entities_found = books.get('response', {}).get('numFound', 0)
            books = books.get('response', {}).get('docs', [])

            if not books:
                self.data_status = DataStatus.NO_DATA
            else:
                for i in range(len(books)):
                    if 'title_s' not in books[i].keys():
                        books[i]['title_s'] = ""
                    else:
                        books[i]['title_s'] = ' ; '.join(books[i]['title_s'])

                    if 'publisher_s' not in books[i].keys():
                        books[i]['publisher_s'] = ""
                    else:
                        books[i]['publisher_s'] = ' ; '.join(books[i]['publisher_s'])

                    if 'authFullName_s' not in books[i].keys():
                        books[i]['authFullName_s'] = ""
                    else:
                        books[i]['authFullName_s'] = ', '.join(books[i]['authFullName_s'])

                self.data = pd.DataFrame.from_records(books)

                self.data = self.data.rename(columns={
                    "title_s": self._("Book title"),
                    "authFullName_s": self._("Authors"),
                    "publisher_s": self._("Publisher"),
                })
                self.data_status = DataStatus.OK
            # hide_n_entities_warning as this information is already displayed on the table    
            self.generate_plot_info(hide_n_entities_warning=True)
            return {"info": self.info}
        except Exception as e:
            return self._handle_fetch_error(e, "Error fetching or formatting books data")

    def get_figure(self) -> str:
        """
        Generate an HTML table of books.
        """
        if self.data_status == DataStatus.NOT_FETCHED:
            self.fetch_data()
        if self.data_status == DataStatus.NO_DATA:
            return self.get_no_data_html()
        if self.data_status == DataStatus.ERROR:
            return self.get_error_html()

        return self.dataframe_to_html_table(
            self.data,
            caption=self._("List of books entered in HAL"),
            label="books",
            max_plotted_entities=self.max_plotted_entities,
        )

class Chapters(Biso):
    """
    A class to fetch and generate a table of book chapters.
    """

    figure_file_extension = "tex"
    html_figure_type = "html_table"


    def __init__(self, entity_id: str, year: int | None = None, **kwargs):
        """
        Initialize the Chapters class.

        :param entity_id: The HAL collection identifier. This usually refers to the entity id acronym.
        :type entity_id: str
        :param year: The year for which to fetch data. If None, uses the current year.
        :type year: int | none, optional
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        """
        super().__init__(entity_id, year, **kwargs)


    def fetch_data(self) -> dict[str, Any]:
        """
        Fetch data about book chapters from the HAL API.

        This method queries the API to get the list of book chapters and their metadata.
        The data is stored in the `data` attribute as a pandas DataFrame with columns for title (`title_s`),
        book title (`bookTitle_s`), and publisher (`publisher_s`).

        :return: The info about the fetched data.
        :rtype: dict[str, Any]
        """
        try:
            url = (
                f"https://api.archives-ouvertes.fr/search/{self.entity_id}/?q=*:*&fq=docType_s:COUV&"
                f"fq=producedDateY_i:{self.year}&rows={self.max_plotted_entities}&wt=json&indent=true&"
                f"fl=title_s,bookTitle_s,publisher_s"
            )
            chapters = requests.get(url).json()
            self.n_entities_found = chapters.get('response', {}).get('numFound', 0)
            chapters = chapters.get('response', {}).get('docs', [])

            if not chapters:
                self.data_status = DataStatus.NO_DATA
            else:
                for i in range(len(chapters)):
                    if 'title_s' not in chapters[i].keys():
                        chapters[i]['title_s'] = ""
                    else:
                        chapters[i]['title_s'] = ' ; '.join(chapters[i]['title_s'])

                    if 'publisher_s' not in chapters[i].keys():
                        chapters[i]['publisher_s'] = ""
                    else:
                        chapters[i]['publisher_s'] = ' ; '.join(chapters[i]['publisher_s'])

                self.data = pd.DataFrame.from_records(chapters)

                self.data = self.data.rename(columns={
                    "title_s": self._("Chapter title"),
                    "bookTitle_s": self._("Book title"),
                    "publisher_s": self._("Publisher"),
                })
                self.data_status = DataStatus.OK
            # hide_n_entities_warning as this information is already displayed on the table
            self.generate_plot_info(hide_n_entities_warning=True)
            return {"info": self.info}
        except Exception as e:
            return self._handle_fetch_error(e, "Error fetching or formatting chapters data")


    def get_figure(self) -> str:
        """
        Generate an HTML table of book chapters.

        :return: HTML fragment representing the book chapters data.
        :rtype: str
        """
        if self.data_status == DataStatus.NOT_FETCHED:
            self.fetch_data()
        if self.data_status == DataStatus.NO_DATA:
            return self.get_no_data_html()
        if self.data_status == DataStatus.ERROR:
            return self.get_error_html()

        return self.dataframe_to_html_table(
            self.data,
            caption=self._("List of chapters entered in HAL"),
            label="chapters",
            max_plotted_entities=self.max_plotted_entities,
        )

class CollaborationMap(Biso):
    """
    A class to fetch and plot data about collaborations on a map.

    :cvar default_countries_land_color: Default color for the land in the map.
    :cvar default_countries_lines_color: Default color for the lines in the map.
    :cvar default_frame_color: Default color for the frame of the map.
    :cvar default_height: Default height for the map.
    :cvar default_width: Default width for the map.
    :cvar default_zoom_lat_range: Default latitude range for zoomed map.
    :cvar default_zoom_lon_range: Default longitude range for zoomed map.
    """

    default_countries_land_color = "#eaeaea"
    default_countries_lines_color = "#999999"
    default_frame_color = default_countries_lines_color
    # override Biso class default height and width
    default_height = 700
    default_width = 1400
    default_height_zoom = 800
    default_width_zoom = 1200
    default_zoom_lat_range = [33.5,71]
    default_zoom_lon_range = [-18.5, 39.5]

    def __init__(
            self,
            entity_id: str,
            year: int | None = None,
            countries_land_color: str | None = None,
            countries_lines_color: str | None = None,
            countries_to_ignore: list[str] | None = None,
            frame_color: str | None = None,
            height: int | None = None,
            institutions_to_exclude: list[str] | None = None,
            map_zoom: bool = False,
            markers_scale_factor: float | int | None = None,
            resolution: int = 110,
            width: int | None = None,
            zoom_lat_range: list[float | int] | None = None,
            zoom_lon_range: list[float | int] | None = None,
            **kwargs
    ):
        """
        Initialize the CollaborationMap class.

        :param entity_id: The HAL collection identifier. This usually refers to the entity id acronym.
        :type entity_id: str
        :param year: The year for which to fetch data. If None, uses the current year.
        :type year: int | None, optional
        :param countries_land_color: Color of the land in the map.
        :type countries_land_color: str | None, optional
        :param countries_lines_color: Color of the country lines in the map.
        :type countries_lines_color: str | None, optional
        :param countries_to_ignore: List of countries to ignore in the data.
        :type countries_to_ignore: list[str] | None, optional
        :param frame_color: Color of the frame of the plot.
        :type frame_color: str | None, optional
        :param height: Height of the plot.
        :type height: int | None, optional
        :param institutions_to_exclude: List of institutions to exclude from the data.
        :type institutions_to_exclude: list[str] | None, optional
        :param map_zoom: If set to true, zoom the map according to the ranges of coordinates defined by
            zoom_lat_range and zoom_lat_range
        :type map_zoom: bool, optional
        :param markers_scale_factor: Scale factor for the markers. Default is 1. Increase to decrease marker size.
            If not set and map_zoom is True, default to 0.5.
        :type markers_scale_factor: float | int | None, optional
        :param resolution: Resolution of the plot: can either be 110 (low resolution) or 50 (high resolution).
        :type resolution: int, optional
        :param width: Width of the plot.
        :type width: int | None, optional
        :param zoom_lat_range: Latitude range of coordinates for the zoom map. If set to None, the zoom will be on
            Europe.
        :type zoom_lat_range: list[float | int] | None, optional
        :param zoom_lon_range: Longitude range of coordinates for the zoom map. If set to None, the zoom will be on
            Europe.
        :type zoom_lon_range: list[float | int] | None, optional
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        """
        if height is None and width is None:
            self.has_default_width_and_height = True
        else:
            self.has_default_width_and_height = False
        if countries_land_color is None:
            self.countries_land_color = self.default_countries_land_color
        else:
            self.countries_land_color = countries_land_color
        if countries_lines_color is None:
            self.countries_lines_color = self.default_countries_lines_color
        else:
            self.countries_lines_color = countries_lines_color
        if countries_to_ignore is None:
            self.countries_to_ignore = []
        else:
            self.countries_to_ignore = countries_to_ignore
        if frame_color is None:
            self.frame_color = self.default_frame_color
        else:
            self.frame_color = frame_color
        if height is None:
            height = self.default_height
        if institutions_to_exclude is None:
            institutions_to_exclude = []
        self.institutions_to_exclude = institutions_to_exclude
        self.map_zoom = map_zoom
        if markers_scale_factor is None:
            if map_zoom:
                self.markers_scale_factor = 0.1
            else:
                self.markers_scale_factor = 1
        else:
            self.markers_scale_factor = markers_scale_factor
        self.resolution = resolution
        if width is None:
            width = self.default_width
        super().__init__(entity_id, year, height=height, width=width, **kwargs)
        if zoom_lat_range is None:
            self.zoom_lat_range = self.default_zoom_lat_range
        else:
            self.zoom_lat_range = zoom_lat_range
        if zoom_lon_range is None:
            self.zoom_lon_range = self.default_zoom_lon_range
        else:
            self.zoom_lon_range = zoom_lon_range


    def fetch_data(self) -> dict[str, Any]:
        """
        Fetch data about collaborations from the HAL API and OpenAlex API.

        This method queries the API to get the list of collaborations and their metadata.
        It processes the data to create a DataFrame with latitude, longitude, and other relevant information.

        :return: The info about the fetched data.
        :rtype: dict[str, Any]
        """
        try:
            # get the list of DOI from HAL:
            article_dois = self.get_all_ids_with_cursor(id_type="doi")
            article_dois.sort()  # sort the list to improve cache usage by openalex-analysis

            # Download articles metadata from OpenAlex:
            print(f"Downloading the metadata for {len(article_dois)} DOIs from OpenAlex...")
            # works = WorksData().get_multiple_works_from_doi(article_dois, return_dataframe=False)
            works = WorksData(entities_from_id_list = article_dois).entities_df.to_dict(orient = 'records')
            works = [work for work in works if work is not None]
            print(f"{len(works)} works retrieved successfully from OpenAlex out of {len(article_dois)}")

            # Download institution metadata from OpenAlex:
            # get the list of institutions who collaborated per work:
            works_institutions = [
                list(set([
                    institution['id']
                    for author in work['authorships'] for institution in author.get('institutions', [])
                    if institution.get('id') is not None
                ]))
                for work in works
            ]
            # list of the institutions we collaborated with
            institutions_id = set(list([
                institution for institutions in works_institutions for institution in institutions
                if institution not in self.institutions_to_exclude
            ]))
            print(f"{len(institutions_id)} unique institutions with which we collaborated on works")
            # remove the https://openalex.org/ at the beginning
            institutions_id = [institution_id[21:] for institution_id in institutions_id]
            # Filter out any invalid ID: ID that is not strictly 'I' followed by numbers.
            institutions_id = [i_id for i_id in institutions_id if i_id.startswith('I') and i_id[1:].isdigit()]
            institutions_id.sort()  # sort the list to improve cache usage by openalex-analysis
            # create dictionaries with the institution id as key and lon, lat and name as item
            institutions_name = {}
            institutions_lat = {}
            institutions_lon = {}
            institutions_country = {}
            institutions_count = {}
            # count the number of collaboration per institutions:
            # works_institutions contains the institutions we collaborated per work, so we
            # can count on how many works we collaborated with each institution
            all_institutions_count = Counter(list(
                [institution for institutions in works_institutions for institution in institutions]
            ))
            if not institutions_id:
                institutions = []
            else:
                institutions = InstitutionsData(
                    entities_from_id_list = institutions_id
                ).entities_df.to_dict(orient = 'records')
            for institution in institutions:
                if institution['geo']['country'] not in self.countries_to_ignore:
                    institutions_name[institution['id']] = institution['display_name']
                    institutions_lat[institution['id']] = institution['geo']['latitude']
                    institutions_lon[institution['id']] = institution['geo']['longitude']
                    institutions_country[institution['id']] = institution['geo']['country']
                    institutions_count[institution['id']] = all_institutions_count[institution['id']]


            # Create DataFrame to plot:
            institutions_name_s = pd.Series(dict(institutions_name), name='name')
            institutions_lat_s = pd.Series(dict(institutions_lat), name='lat')
            institutions_lon_s = pd.Series(dict(institutions_lon), name='lon')
            institutions_country_s = pd.Series(dict(institutions_country), name='country')
            institutions_count_s = pd.Series(dict(institutions_count), name='count')
            self.data = pd.concat([institutions_name_s, institutions_lat_s, institutions_lon_s,
                                   institutions_country_s, institutions_count_s], axis=1)

            # calculate stats:
            collaborations_nb = int(self.data['count'].sum())
            institutions_nb = len(self.data)
            countries_nb = len(self.data['country'].unique())

            print(f"{len(self.data)} unique institutions to plot")

            self.generate_plot_info()
            stats = {
                'collaborations_nb': collaborations_nb,
                'institutions_nb': institutions_nb,
                'countries_nb': countries_nb,
                'info': self.info
            }

            if collaborations_nb == 0:
                self.data_status = DataStatus.NO_DATA
            else:
                self.data_status = DataStatus.OK

            return stats
        except Exception as e:
            return self._handle_fetch_error(e, "Error fetching or formatting collaboration maps data", return_map_stats=True)



    def get_figure(self) -> go.Figure:
        """
        Plot a map with the number of collaborations per institution.

        :return: The plotly figure.
        :rtype: go.Figure
        """
        if self.data_status == DataStatus.NOT_FETCHED:
            self.fetch_data()
        # If no data, we plot the map as usual
        if self.data_status == DataStatus.ERROR:
            return self.get_error_plot()

        if self.map_zoom:
            lataxis_range = self.zoom_lat_range if self.zoom_lat_range is None else self.zoom_lat_range
            lonaxis_range = self.zoom_lon_range if self.zoom_lon_range is None else self.zoom_lon_range
        else:
            lataxis_range = None
            lonaxis_range = None

        # calculate count max and count sum within lataxis_range and lonaxis_range
        if lataxis_range is not None and lonaxis_range is not None:
            # Filter data within the specified ranges
            filtered_data = self.data[
                (self.data['lat'] >= lataxis_range[0]) &
                (self.data['lat'] <= lataxis_range[1]) &
                (self.data['lon'] >= lonaxis_range[0]) &
                (self.data['lon'] <= lonaxis_range[1])
            ]
            count_max = filtered_data['count'].max() if not filtered_data.empty else 0
            count_sum = filtered_data['count'].sum() if not filtered_data.empty else np.array([0])
        else:
            # Use all data if no range is specified
            count_max = self.data['count'].max() if not self.data.empty else 0
            count_sum = self.data['count'].sum() if not self.data.empty else np.array([0])

        # example values: 0.05 for 10 entities, 0.5 for 1000 entities
        # calculate markers_size_ref to auto-adjust based on count_max and count_sum
        # markers_size_ref = 3.54e-3*math.sqrt(count_max*20 + count_sum.sum())
        markers_size_ref = self.markers_scale_factor*1e-2*math.sqrt(count_max*20 + count_sum.sum())
        # markers_size_ref = 0.5
        # set a ln scale
        self.data['size'] = np.log(self.data['count'] + 1)

        if self.data.empty:
            fig = px.scatter_geo(
                height=self.default_height_zoom if self.map_zoom and self.has_default_width_and_height else self.height,
                width=self.default_width_zoom if self.map_zoom and self.has_default_width_and_height else self.width,
                #color_discrete_sequence=["#eb7125"]
            )
        else:
            fig = px.scatter_geo(
                self.data,
                lat='lat',
                lon='lon',
                size='size',
                custom_data=['name', 'country', 'count'],
                height=self.default_height_zoom if self.map_zoom and self.has_default_width_and_height else self.height,
                width=self.default_width_zoom if self.map_zoom and self.has_default_width_and_height else self.width,
                #color_discrete_sequence=["#eb7125"]
            )
        # add the hover
        hover_template = [
                "%{customdata[0]}",
                "%{customdata[1]}",
                "%{customdata[2]} co-authored paper(s)",
        ]
        fig.update_traces(
            hovertemplate="<br>".join(hover_template),
            marker=dict(
                color=self.main_color,
                opacity=1,
                # sizemode='area',
                sizeref=markers_size_ref,
                #size=1,
                line=dict(
                    color="white",
                    width=0 # 0.1
                )
            ),
        )

        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), autosize=True)

        if self.title is not None:
            fig.update_layout(title=self.title)

        fig.update_geos(
            visible=False,
            resolution=self.resolution,
            projection_type="natural earth",
            showcountries=True,
            showland=True,
            countrycolor=self.countries_lines_color,
            landcolor=self.countries_land_color,
            showframe=True,
            countrywidth=0.5,
            framecolor=self.frame_color,
        )

        if self.map_zoom:
            fig.update_geos(
                lataxis_range=lataxis_range,
                lonaxis_range=lonaxis_range,
            )

        return fig


class CollaborationNames(Biso):
    """
    A class to fetch and plot data about institutions collaboration names.

    :cvar orientation: Orientation for plots ('h' for horizontal).
    """

    orientation = 'h'

    def __init__(self, entity_id: str, year: int | None = None, countries_to_exclude: list[str] | None = None, **kwargs):
        """
        Initialize the CollaborationNames class.

        :param entity_id: The HAL collection identifier. This usually refers to the entity id acronym.
        :type entity_id: str
        :param year: The year for which to fetch data. If None, uses the current year.
        :type year: int | none, optional
        :param countries_to_exclude: List of countries to exclude from the data.
            Use country code (e.g. 'fr' for France).
        :type countries_to_exclude: list[str] | None, optional
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        """
        if countries_to_exclude is None:
            countries_to_exclude = []
        self.countries_to_exclude = countries_to_exclude
        super().__init__(entity_id, year, **kwargs)


    def fetch_data(self) -> dict[str, Any]:
        """
        Fetch data about collaboration names from the HAL API only.

        This method queries the API to get the list of collaboration names and their counts.
        It processes the data to create a dictionary where keys are formatted structure names (including country flags)
        and values are their respective counts.

        :return: The info about the fetched data.
        :rtype: dict[str, Any]
        """

        try:
            # Get count of each structure id in publications
            structs_facet_url = (
                f"https://api.archives-ouvertes.fr/search/{self.entity_id}/?q=publicationDateY_i:{self.year} AND "
                f"docType_s:(ART OR COMM)&wt=json&rows=0&facet=true&facet.field=structId_i&"
                f"facet.limit=10000&facet.mincount=1"
            )
            res = requests.get(structs_facet_url).json()
            # We don't set the self.n_entities_found value as calculating it would request too many API requests.
            # It would require the full iterations for the 10k structures in the for loop below, and it would not give
            # the right value for collections with more than 10k collaborations.
            structs_id_facets = res.get('facet_counts', {}).get('facet_fields', {}).get('structId_i', [])
            if not structs_id_facets:
                self.data_status = DataStatus.NO_DATA
                self.generate_plot_info()
                return {"info": self.info}
            structs_id_count = {
                struct_id: count for struct_id, count in zip(structs_id_facets[::2], structs_id_facets[1::2])
            }

            struct_list = []
            # get metadata of each structure (name + country code)
            for i in range (0, len(structs_id_count), 500):
                if not self.countries_to_exclude:
                    facet_url = (
                    f"https://api.archives-ouvertes.fr/ref/structure/?q="
                    f"docid:({" OR ".join(list(structs_id_count.keys())[i:i+500])})&"
                    f"fl=docid,label_s,country_s&rows=10000"
                )
                else:
                    facet_url = (
                    f"https://api.archives-ouvertes.fr/ref/structure/?q="
                    f"docid:({" OR ".join(list(structs_id_count.keys())[i:i+500])}) AND "
                    f"-country_s:{" OR ".join(self.countries_to_exclude)}&"
                    f"fl=docid,label_s,country_s&rows=10000"
                )
                facets = requests.get(facet_url).json()
                facets_res = facets['response']['docs']
                # As HAL returns structures that were not requested, we remove non-requested structures + remove
                # structures not in countries to exclude
                struct_list[i:i+500] = [
                    struct for struct in facets_res if struct['docid'] in list(structs_id_count.keys())[i:i+500]
                                                       and struct.get('country_s') not in self.countries_to_exclude
                ]
                # if we found more structures than the number to plot, stop here to save useless API requests
                if len(struct_list) >= self.max_plotted_entities:
                    break
            if not struct_list:
                self.data_status = DataStatus.NO_DATA
                self.generate_plot_info()
                return {"info": self.info}

            self.data = {
                format_structure_name(struct['label_s'], struct.get('country_s', None)):
                    structs_id_count[struct['docid']] for struct in struct_list
            }

            # sort values
            self.data = {k: v for k, v in sorted(self.data.items(), key=lambda item: item[1])}
            self.data_status = DataStatus.OK
            self.generate_plot_info()
            return {"info": self.info}
        except Exception as e:
            return self._handle_fetch_error(e, "Error fetching or formatting collaborations data")


class Conferences(Biso):
    """
    A class to fetch and plot data about conferences.

    :cvar orientation: Orientation for plots ('h' for horizontal).
    """

    orientation = 'h'

    def __init__(self, entity_id: str, year: int | None = None, **kwargs):
        """
        Initialize the Conferences class.

        :param entity_id: The HAL collection identifier. This usually refers to the entity id acronym.
        :type entity_id: str
        :param year: The year for which to fetch data. If None, uses the current year.
        :type year: int | none, optional
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        """
        super().__init__(entity_id, year, **kwargs)

    def fetch_data(self) -> dict[str, Any]:
        """
        Fetch data about conferences from the HAL API.

        This method queries the API to get the list of conferences and their counts.
        It processes the data to create a dictionary where keys are formatted conference names (including country flags)
        and values are their respective counts.

        :return: The info about the fetched data.
        :rtype: dict[str, Any]
        """
        def format_conference_name(conf_name: str, country_code: str | None) -> str:
            """
            Format the conference name by cropping if too long and adding a country flag.

            :param conf_name: The conference name.
            :type conf_name: str
            :param country_code: The country code.
            :type country_code: str | None
            :return: The formatted conference name with country flag.
            :rtype: str
            """
            # crop name if too long
            if len(conf_name) > 65:
                conf_name = conf_name[:70]+"... "
            # add country flag
            if country_code is None:
                return conf_name + " (" + self._("Unspecified country") + ")"
            # country_flag=get_flag_img(country_code)
            # return f"{country_flag}{conf_name}"
            return f"{conf_name} __{country_code.upper()}__"
        
        try:
            stats_url = (
                f"https://api.archives-ouvertes.fr/search/{self.entity_id}/?q=publicationDateY_i:{self.year} AND "
                "docType_s:(COMM)&wt=json&rows=0&stats=true&stats.field={!count=true+cardinality=true}conferenceTitle_s"
            )
            res = requests.get(stats_url).json()
            self.n_entities_found = (res.get('stats', {}).get('stats_fields', {}).get('conferenceTitle_s', {}).
                                     get('cardinality', 0))
            facet_url = (
                f"https://api.archives-ouvertes.fr/search/{self.entity_id}/?q=publicationDateY_i:{self.year} AND "
                f"docType_s:(COMM)&wt=json&rows=0&facet=true&facet.pivot=conferenceTitle_s,country_s&"
                f"facet.limit={self.max_plotted_entities}&facet.mincount=1"
            )
            res = requests.get(facet_url).json()
            conferences_list = res.get('facet_counts', {}).get('facet_pivot', {}).get(
                'conferenceTitle_s,country_s', [])
            if not conferences_list:
                self.data_status = DataStatus.NO_DATA
            else:
                conferences_list = sorted(conferences_list, key=lambda conf: conf['count'])
                self.data = {
                    format_conference_name(
                        conf_name = conf.get('value', self._("Unspecified conference")),
                        country_code = conf.get('pivot', [{}])[0].get('value', None)
                    ): conf.get('count', 0)
                    for conf in conferences_list
                }
                self.data_status = DataStatus.OK
            self.generate_plot_info()
            return {"info": self.info}
        except Exception as e:
            return self._handle_fetch_error(e, "Error fetching or formatting conferences data")

class EuropeanProjects(Biso):
    """
    A class to fetch and plot data about European projects.

    :cvar orientation: Orientation for plots ('h' for horizontal).
    """

    orientation = 'h'

    def __init__(self, entity_id: str, year: int | None = None, **kwargs):
        """
        Initialize the EuropeanProjects class.

        :param entity_id: The HAL collection identifier. This usually refers to the entity id acronym.
        :type entity_id: str
        :param year: The year for which to fetch data. If None, uses the current year.
        :type year: int | none, optional
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        """
        super().__init__(entity_id, year, **kwargs)


    def fetch_data(self) -> dict[str, Any]:
        """
        Fetch data about European projects from the HAL API.

        This method queries the API to get the list of European projects and their counts.
        The data is stored in the `data` attribute as a dictionary where keys are European project acronyms
        and values are their respective counts.

        :return: The info about the fetched data.
        :rtype: dict[str, Any]
        """
        try:
            facet_url=(
                f"https://api.archives-ouvertes.fr/search/{self.entity_id}/?q=publicationDateY_i:{self.year}&wt=json&rows=0"
                f"&facet=true&facet.field=europeanProjectAcronym_s&facet.limit={self.max_plotted_entities}"
                "&facet.mincount=1&stats=true&stats.field={!count=true+cardinality=true}europeanProjectAcronym_s"
            )
            res = requests.get(facet_url).json()
            self.n_entities_found = (res.get('stats', {}).get('stats_fields', {}).get('europeanProjectAcronym_s', {}).
                                     get('cardinality', 0))
            eu_projects_list=res.get('facet_counts', {}).get('facet_fields', {}).get('europeanProjectAcronym_s', [])
            raw_data = {eu_projects_list[i]: eu_projects_list[i + 1] for i in range(0, len(eu_projects_list), 2)
                         if eu_projects_list[i + 1] != 0}
            # sort values
            self.data = {}
            for k, v in raw_data.items():
                if re.search(r"^Universit", k, re.IGNORECASE):
                    new_key = "Autres projets"
                    self.data[new_key] = self.data.get(new_key, 0) + v
                else:
                    self.data[k] = v
            self.data = {k: v for k, v in sorted(self.data.items(), key=lambda item: item[1])}
            if not self.data:
                self.data_status = DataStatus.NO_DATA
            else:
                self.data_status = DataStatus.OK
            self.generate_plot_info()
            return {"info": self.info}
        except Exception as e:
            return self._handle_fetch_error(e, "Error fetching or formatting European projects data")


class Journals(Biso):
    """
    A class to fetch and generate a table of journals.
    """
    # table to correct values ​​of bso
    COLOR_RULES = [
        {"oa_color": "other",     "is_oa": True, "journal_is_oa": False,  "has_apc": ["missing", "zero", "numeric"], "color_final": "hybrid"},
        
        {"oa_color": "other",     "is_oa": True, "journal_is_oa": True,   "has_apc": "missing",  "color_final": "other"},
        {"oa_color": "other",     "is_oa": True, "journal_is_oa": True,   "has_apc": "zero",  "color_final": "diamond"},
        {"oa_color": "other",     "is_oa": True, "journal_is_oa": True,   "has_apc": "numeric",  "color_final": "gold"},
        
        {"oa_color": "other",     "is_oa": True, "journal_is_oa": None,   "has_apc": "missing",  "color_final": "other"},
        {"oa_color": "other",     "is_oa": True, "journal_is_oa": None,   "has_apc": "zero",  "color_final": "other"},
        {"oa_color": "other",     "is_oa": True, "journal_is_oa": None,   "has_apc": "numeric",  "color_final": "other"}
    ]

    RESOLVE_COLORS = pd.DataFrame.from_records(COLOR_RULES).explode('has_apc')

    # SVG pictograms
    svg_diamond = '<svg style="vertical-align: middle; margin-right: 4px;" height="16" width="16" viewBox="0 0 24 24" fill="#00b4d8"><path d="M12 2L2 12l10 10 10-10L12 2z"/></svg>'
    svg_gold = '<svg style="vertical-align: middle; margin-right: 4px;" height="14" width="14"><circle cx="7" cy="7" r="6" fill="#ffb703"/></svg>'
    svg_check = '<svg style="vertical-align: middle; margin-right: 4px;" height="14" width="14" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>'
    svg_closed = '<svg style="vertical-align: middle; margin-right: 4px;" height="14" width="14" viewBox="0 0 24 24" fill="#ef4444" stroke="#ef4444" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>'
    svg_other = '<svg style="vertical-align: middle; margin-right: 4px;" height="14" width="14" viewBox="0 0 24 24" fill="none" stroke="#6b7280" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>'
    
    legend_html = (
            f"<br/>"
            f"<strong>Légende :</strong> "
            f"{svg_diamond}Revue Diamant | "
            f"{svg_gold}Revue Gold"
            f"<br/>"
        )

    figure_file_extension = "tex"
    html_figure_type = "html_table"

    def __init__(self, entity_id: str, year: int | None = None, **kwargs):
        """
        Initialize the Journals class.

        :param entity_id: The HAL collection identifier. This usually refers to the entity id acronym.
        :type entity_id: str
        :param year: The year for which to fetch data. If None, uses the current year.
        :type year: int | none, optional
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        """
        super().__init__(entity_id, year, **kwargs)



    def fetch_data(self) -> dict[str, Any]:
        """
        Fetch data about journals from the API.

        :return: The info about the fetched data.
        :rtype: dict[str, Any]
        """

        def format_apc(row):
            if pd.notna(row['amount_apc_EUR']):
                return f"{int(row['amount_apc_EUR'])}"
            return None
        
        def format_color(row) -> str:
            """
            Uses the color to determine open access on journal
            Open : diamond, gold, hybrid with apc paid
            Closed : hybrid with 0 apc paid and closed papers
            """
            color = row["color_final"] if pd.notna(row["color_final"]) else row["oa_color"]
            if pd.isna(color):
                return f"{self.svg_other}" # "❓"
            if color=="hybrid":
                if row["has_apc"]=="numeric":
                    return f"{self.svg_check}" # "✅"
                if row["has_apc"]=="zero":
                    return f"{self.svg_closed}" # "❌"
            if color in ["gold", "diamond"]:
                return f"{self.svg_check}" # "✅"
            if color=="closed":
                return f"{self.svg_closed}" # "❌"
            return f"{self.svg_other}" # "❓"

        def format_is_oa_on_repository(row) -> str:
            status=row["is_oa_on_repository"]
            if pd.isna(status) or not status:
                return f"{self.svg_closed}" # "❌"
            return f"{self.svg_check}" # "✅"

        try:
            if self.scanr_api_url is None:
                self.data_status = DataStatus.ERROR
                stats = {
                    'nb_works': self._("Error"),
                    'nb_works_found_in_bso': self._("Error"),
                    'nb_journals': self._("Error"),
                    'bso_version': self.scanr_bso_version,
                    'info': self._("Error")
                }
                return stats
            doi_ids = self.get_all_ids_with_cursor(id_type="doi", doc_types=["ART"])
            hal_ids = self.get_all_ids_with_cursor(id_type="hal", doc_types=["ART"])
            # format IDs for scanr:
            doi_ids = [f"doi{doi_id}" for doi_id in doi_ids]
            hal_ids = [f"hal{hal_id}" for hal_id in hal_ids]
            fields_to_retrieve = [
                "journal_name",
                "publisher",
                f"oa_details.{self.scanr_bso_version}.oa_colors_with_priority_to_publisher",
                f"oa_details.{self.scanr_bso_version}.is_oa",
                f"oa_details.{self.scanr_bso_version}.journal_is_oa",
                "amount_apc_EUR",
                f"oa_details.{self.scanr_bso_version}.oa_host_type",
            ]
            works = self.get_works_from_es_index_from_id_by_chunk(
                self.scanr_bso_index,
                hal_ids + doi_ids,
                fields_to_retrieve
            )

            nb_works = len(hal_ids)
            nb_found_works = len(works)
            print(f"Found {nb_found_works} works out of {nb_works}")

            # Simplify extraction of BSO data from works
            works_clean=[]
            for work in works:
                source=work.get('_source', {})
                bso_data=source.get("oa_details", {}).get(self.scanr_bso_version, {})
                # Fetch unique paper color
                journal_color=bso_data.get("oa_colors_with_priority_to_publisher")
                if isinstance(journal_color, list):
                    journal_color=journal_color[0] if len(journal_color)>0 else None
                # Fetch and split host type
                host_types_raw=bso_data.get("oa_host_type", "")
                host_types=host_types_raw.split(";") if host_types_raw else []

                # Determine if present in openaccess in repository
                is_on_repository="repository" in host_types

                # Determine APC status
                apc_val = source.get("amount_apc_EUR")
                if pd.isna(apc_val):
                    apc_status = "missing"
                elif apc_val == 0:
                    apc_status = "zero"
                else:
                    apc_status = "numeric"

                works_clean.append({

                    "journal_name": source.get("journal_name"),
                    "publisher": source.get("publisher"),
                    "oa_color": journal_color,
                    "is_oa": bso_data.get("is_oa"),
                    "journal_is_oa": bso_data.get("journal_is_oa"),
                    "has_apc": apc_status,
                    "amount_apc_EUR": apc_val,
                    "is_oa_on_repository": is_on_repository,
                })
            works=works_clean

            self.data = pd.DataFrame.from_records(works)

            self.data['oa_color'] = self.data['oa_color'].fillna('other').replace('green_only', 'other')
            self.data = self.data.merge(self.RESOLVE_COLORS, on=["oa_color", "is_oa", "journal_is_oa", "has_apc"], how="left")

            if len(self.data.index) == 0:
                self.data_status = DataStatus.NO_DATA
                self.generate_plot_info()
                stats = {
                    'nb_works': nb_works,
                    'nb_works_found_in_bso': nb_found_works,
                    'nb_journals': 0,
                    'bso_version': self.scanr_bso_version,
                    'info': self.info
                }
                return stats

            self.data['journal_name'] = self.data['journal_name'].fillna(self._("Unspecified journal"))
            self.data['publisher'] = self.data['publisher'].fillna(self._("Unspecified publisher"))

            self.data['color_raw'] = self.data["color_final"].fillna(self.data["oa_color"])
            
            # format values
            self.data['oa_color'] = self.data.apply(format_color, axis=1)
            self.data['paid_apc'] = self.data.apply(format_apc, axis=1)
            self.data.drop(['amount_apc_EUR'], axis=1, inplace=True)
            self.data['is_oa_on_repository'] = self.data.apply(format_is_oa_on_repository, axis=1)

            def merge_cells(group):
                apc_list = group['paid_apc'].dropna().tolist()
                if apc_list:
                    apc_str = f"{', '.join(apc_list)}"
                else:
                    apc_str = ""

                raw_colors = group["color_raw"].dropna().tolist()
                exclusive_svg = ""
                if raw_colors and len(raw_colors) == len(group):
                    # If all diamond -> add diamond pictogram, if all gold -> add gold pictogram, else no pictogram
                    if all(c == "diamond" for c in raw_colors):
                        exclusive_svg = self.svg_diamond
                    elif all(c == "gold" for c in raw_colors):
                        if apc_str:
                            exclusive_svg = self.svg_gold

                merged_data = {
                    "journal_name": group.name,
                    "oa_status_exclusive": exclusive_svg,
                    "publisher": ' ; '.join(group['publisher'].dropna().unique()),
                    "nb_works": len(group),
                    "oa_color": ' '.join(group['oa_color']),
                    "is_oa_on_repository": ' '.join(group['is_oa_on_repository']),
                    "paid_apc": apc_str
                }
                return pd.Series(merged_data)

            self.data = self.data.groupby("journal_name").apply(merge_cells, include_groups=False).reset_index(
                drop=True).sort_values(["nb_works", "oa_status_exclusive", "paid_apc"], ascending=[False, False, False])
            # move unspecified journals to the end
            idx = self.data.index.tolist() # copy index
            # find index of the Unspecified journal
            unspecified_journals_idx = self.data.index[
                self.data["journal_name"] == self._("Unspecified journal")
            ].tolist()
            # if Unspecified journal was found in the index
            if unspecified_journals_idx:
                idx.remove(unspecified_journals_idx[0])
                # reindex the dataframe to move the Unspecified journal to the end
                self.data = self.data.reindex(idx + unspecified_journals_idx)
            nb_journals = (self.data["journal_name"] != self._("Unspecified journal")).sum()

            if len(self.data.index) == 0:
                self.data_status = DataStatus.NO_DATA
            else:
                self.data_status = DataStatus.OK

            self.generate_plot_info()
            stats = {
                'nb_works': nb_works,
                'nb_works_found_in_bso': nb_found_works,
                'nb_journals': int(nb_journals),
                'bso_version': self.scanr_bso_version,
                'info': self.info
            }

            return stats
        except Exception as e:
            return self._handle_fetch_error(e, "Error fetching or formatting journals data", return_full_stats=True)


    def get_figure(self) -> str:
        """
        Generate an HTML table of journals.

        :return: HTML fragment representing the journals data.
        :rtype: str
        """
        if self.data_status == DataStatus.NOT_FETCHED:
            self.fetch_data()
        if self.data_status == DataStatus.NO_DATA:
            return self.get_no_data_html()
        if self.data_status == DataStatus.ERROR:
            return self.get_error_html()

        df = self.data.copy(deep=True)
        df = df.rename(columns={
            "journal_name": self._("Journal"),
            "oa_status_exclusive": " ",
            "publisher": self._("Publisher"),
            "nb_works": self._("Number of works in BSO"),
            "oa_color": self._("Open access on the journal"),
            "is_oa_on_repository": self._("Open access on a repository"),
            "paid_apc": self._("Paid APC (€)"),
        })

        return self.dataframe_to_html_table(
            df,
            caption=(
                self._("List of journals, publishers, open access status and paid APC") + ". " +
                self._("From the list of publications in HAL and the data of the BSO") + " " + self.scanr_bso_version + "." +
                self.legend_html
            ),
            label="journals",
            max_plotted_entities=self.max_plotted_entities,
            escape_html=False,
        )


class JournalsHal(Biso):
    """
    A class to fetch and plot data about journals from HAL data.

    :cvar orientation: Orientation for plots ('h' for horizontal).
    """

    orientation = 'h'

    def __init__(self, entity_id: str, year: int | None = None, **kwargs):
        """
        Initialize the JournalsHal class.

        :param entity_id: The HAL collection identifier. This usually refers to the entity id acronym.
        :type entity_id: str
        :param year: The year for which to fetch data. If None, uses the current year.
        :type year: int | none, optional
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        """
        super().__init__(entity_id, year, **kwargs)


    def fetch_data(self) -> dict[str, Any]:
        """
        Fetch data about Journals from the HAL API.

        :return: The info about the fetched data.
        :rtype: dict[str, Any]
        """
        try:
            facet_url = (
                f"https://api.archives-ouvertes.fr/search/{self.entity_id}/?q=publicationDateY_i:{self.year}&wt=json&rows=0"
                f"&facet=true&facet.field=journalTitle_s&facet.limit={self.max_plotted_entities}&facet.mincount=1&"
                "stats=true&stats.field={!count=true+cardinality=true}journalTitle_s"
            )
            res = requests.get(facet_url).json()
            self.n_entities_found = (res.get('stats', {}).get('stats_fields', {}).get('journalTitle_s', {}).
                                     get('cardinality', 0))
            jounals_list=res.get('facet_counts', {}).get('facet_fields', {}).get('journalTitle_s', [])
            self.data = {
                jounals_list[i][:75]+"... " if len(jounals_list[i]) > 75 else jounals_list[i]: jounals_list[i + 1]
                for i in range(0, len(jounals_list), 2)
            }
            if not self.data:
                self.data_status = DataStatus.NO_DATA
            else:
                self.data = dict(sorted(self.data.items(), key=lambda item: item[1]))
                self.data_status = DataStatus.OK
            self.generate_plot_info()
            full_url = (
                f"https://api.archives-ouvertes.fr/search/{self.entity_id}/?q=publicationDateY_i:{self.year}&wt=json&rows=0"
                f"&facet=true&facet.field=journalTitle_s&facet.mincount=1&"
                "stats=true&stats.field={!count=true+cardinality=true}journalTitle_s"
            )
            if self.n_entities_found > self.max_plotted_entities:
                self.info = (
                    f"Le nombre de revues affichées a été limité à {self.max_plotted_entities}. "
                    f"Dans <a href='{full_url}'>l'API HAL</a>, "
                    f"{self.n_entities_found} revues ont été trouvées."
                )
            return {"info": self.info}
        except Exception as e:
            return self._handle_fetch_error(e, "Error fetching or formatting Hal journals data")


class OpenAccessWorks(Biso):
    """
    A class to fetch and plot data about the open access status of works.

    :cvar default_year_range_difference: Default difference in years for the range when no year range is provided.
    :cvar default_oa_colors: Default colors for different open access statuses.
    """

    default_year_range_difference = 4

    default_oa_colors = {
        "Full text in HAL": "#00807A",
        "OA outside HAL": "#FEBC18",
        "Closed access": "#C60B46"
    }

    def __init__(
            self,
            entity_id: str,
            year: int | None = None,
            year_range: tuple[int, int] | int | None = None,
            colors: Any = None,
            **kwargs
    ):
        """
        Initialize the OpenAccessWorks class.

        :param entity_id: The HAL collection identifier. This usually refers to the entity id acronym.
        :type entity_id: str
        :param year: The year for which to fetch data. If None, uses the current year. Ignored if `year_range` is
            provided. If `year_range` is not provided, `year_range` will be set to
            `[year - self.default_year_range_difference, year]`
        :type year: int | none, optional
        :param year_range: Range of years to fetch data for. If None, fetch the years from
            `self.year - default_year_range_difference` to `self.year`. If only one int is provided, it replaces
            self.year.
        :type year_range: tuple[int, int] | int | None, optional
        :param colors: Colors for different open access statuses.
        :type colors: Any, optional
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        """
        if year is not None and year_range is not None:
            warnings.warn(
                f"You provided year and year_range, so year will be ignored. The plot will use year_range={year_range}."
            )
        super().__init__(entity_id, year, **kwargs)
        if colors is None:
            self.colors = self.default_oa_colors
        else:
            self.colors = colors
        if isinstance(year_range, int):
            self.year = year_range
            year_range = None
        if year_range is None:
            year_range = (self.year - self.default_year_range_difference, self.year)
        self.year_range = year_range


    def fetch_data(self) -> dict[str, Any]:
        """
        Fetch data about open access works from the HAL API.

        This method queries the API to get the count of open access works for each year in the specified year range.
        The data is stored in the `data` attribute as a pandas DataFrame with counts for different open access statuses.

        :return: The info about the fetched data.
        :rtype: dict[str, Any]
        """
        try:
            self.data=pd.DataFrame(
                columns=['ti_dans_hal', 'oa_hors_hal', 'non_oa'],
                index=range(self.year_range[0], self.year_range[1] + 1)
            )
            facet_url = (
                f"https://api.archives-ouvertes.fr/search/{self.entity_id}/?q=publicationDateY_i:[{self.year_range[0]} TO "
                f"{self.year_range[1]}] AND submitType_s:(file OR annex) AND docType_s:(ART OR COMM)&wt=json&"
                f"rows=0&facet=true&facet.field=publicationDateY_i&facet.limit={self.max_plotted_entities}"
            )
            facets = requests.get(facet_url).json()
            ti_numbers = facets.get('facet_counts', {}).get('facet_fields', {}).get('publicationDateY_i', [])
            for ind, i in enumerate(ti_numbers):
                if isinstance(i,str):
                    self.data.loc[int(i),'ti_dans_hal']=ti_numbers[ind+1]
                else:
                    pass

            oa_url = (
                f"https://api.archives-ouvertes.fr/search/{self.entity_id}/?q=publicationDateY_i:[{self.year_range[0]} TO "
                f"{self.year_range[1]}] AND openAccess_bool:true AND submitType_s:notice AND docType_s:(ART OR COMM)&"
                f"wt=json&rows=0&facet=true&facet.field=publicationDateY_i&facet.limit={self.max_plotted_entities}"
            )
            oa = requests.get(oa_url).json()
            oa_numbers = oa.get('facet_counts', {}).get('facet_fields', {}).get('publicationDateY_i', [])
            for ind, i in enumerate(oa_numbers):
                if isinstance(i,str):
                    self.data.loc[int(i),'oa_hors_hal']=oa_numbers[ind+1]
                else:
                    pass

            non_oa_url = (
                f"https://api.archives-ouvertes.fr/search/{self.entity_id}/?q=publicationDateY_i:[{self.year_range[0]} TO "
                f"{self.year_range[1]}] AND openAccess_bool:false AND submitType_s:notice  AND docType_s:(ART OR COMM)&"
                f"wt=json&rows=0&facet=true&facet.field=publicationDateY_i&facet.limit={self.max_plotted_entities}"
            )
            non_oa = requests.get(non_oa_url).json()
            non_oa_numbers = non_oa.get('facet_counts', {}).get('facet_fields', {}).get('publicationDateY_i', [])
            for ind, i in enumerate(non_oa_numbers):
                if isinstance(i,str):
                    self.data.loc[int(i),'non_oa']=int(non_oa_numbers[ind+1])
                else:
                    pass
            self.data = self.data.infer_objects().fillna(0)
            if self.data.sum().sum() == 0:
                self.data_status = DataStatus.NO_DATA
            else:
                self.data_status = DataStatus.OK

            self.generate_plot_info()
            stats = {
                'oa_works_period': f"{self.year_range[0]} - {self.year_range[1]}",
                'info': self.info
            }
            return stats
        except Exception as e:
            return self._handle_fetch_error(e, "Error fetching or formatting open access works data", return_oaworks_stats=True)


    def get_figure(self) -> go.Figure:
        """
        Plot the open access status of works.

        :return: The plotly figure.
        :rtype: go.Figure
        """
        if self.data_status == DataStatus.NOT_FETCHED:
            self.fetch_data()
        if self.data_status == DataStatus.NO_DATA:
            return self.get_no_data_plot()
        if self.data_status == DataStatus.ERROR:
            return self.get_error_plot()

        years=tuple(self.data.index)

        oa_values={
            self._("Full text in HAL"): np.array(self.data['ti_dans_hal']), # TI dans HAL
            self._("OA outside HAL"): np.array(self.data['oa_hors_hal']), # OA hors HAL
            self._("Closed access"): np.array(self.data['non_oa']) # Accès fermé
        }

        translated_colors = {self._(k):v for k,v in self.colors.items()}

        fig = go.Figure()

        # invisible left bars
        for i, (oa_type, count) in enumerate(oa_values.items()):
            fig.add_trace(go.Bar(
                x=years,
                y=count,
                marker_color="rgba(0,0,0,0)",
                offsetgroup=-0.1,
                width=0.1,
                showlegend=False,
                hoverinfo="skip",
            ))

        # Bars
        for i, (oa_type, count) in enumerate(oa_values.items()):
            fig.add_trace(go.Bar(
                x=years,
                y=count,
                name=oa_type,
                marker_color=translated_colors[oa_type],
                insidetextanchor="middle",
                textangle=0,
                cliponaxis=False,
                offsetgroup=0,
            ))

        # invisible right bars with text
        for i, (oa_type, count) in enumerate(oa_values.items()):
            count_to_plot = [str(int(c)) if c > 0 else "" for c in count]
            fig.add_trace(go.Bar(
                x=years,
                y=count_to_plot,
                name=oa_type,
                marker_color="rgba(0,0,0,0)",
                text=count,
                textposition="inside",
                textfont_color="black",
                insidetextanchor="middle",
                textangle=0,
                cliponaxis=False,
                offsetgroup=1,
                showlegend=False,
                hoverinfo="skip",
            ))

        # Update layout for better visualization
        fig.update_layout(
            barmode='stack',
            barcornerradius=self.barcornerradius,
            width=self.width,
            height=self.height,
            template="simple_white",
            uniformtext_minsize=8,
            uniformtext_mode='show',
            bargap=0.0,
            bargroupgap=0.0,
            legend=self.legend_pos,
            margin=self.margin,
        )

        if self.title is not None:
            fig.update_layout(title=self.title)

        return fig


# typologie_1 == "Entreprises" covers: Start-Up, Entreprise, Entreprise étrangère
PRIVATE_SECTOR_TYPOLOGIE_1 = {"Entreprises"}
# Extra typologie_2 values that fall under "Autres" but are genuine companies (ROR/SIRENE)
PRIVATE_SECTOR_TYPOLOGIE_2 = {
    "Entreprise (ROR)",
    "Petite & moyenne entreprise (SIRENE)",
    "Entreprise de taille intermédiaire (SIRENE)",
    "Grande entreprise (SIRENE)",
}


class PrivateSectorCollaborations(Biso):
    """
    A class to fetch and generate a plots with the names of the private sector collaborations.

    :cvar orientation: Orientation for plots ('h' for horizontal).
    """

    orientation = 'h'

    def __init__(self, entity_id: str, year: int | None = None, **kwargs):
        """
        Initialize the PrivateSectorCollaborations class.

        :param entity_id: The HAL collection identifier. This usually refers to the entity id acronym.
        :type entity_id: str
        :param year: The year for which to fetch data. If None, uses the current year.
        :type year: int | none, optional
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        """
        super().__init__(entity_id, year, **kwargs)

    def fetch_data(self) -> dict[str, Any]:
        """
        Fetch data about PrivateSectorCollaborations from the API.

        :return: The info about the fetched data.
        :rtype: dict[str, Any]
        """
        try:
            if self.scanr_api_url is None:
                self.data_status = DataStatus.ERROR
                return {"info": self._("Error")}
            doi_ids = self.get_all_ids_with_cursor(id_type="doi")
            hal_ids = self.get_all_ids_with_cursor(id_type="hal")
            # format IDs for scanr:
            doi_ids = [f"doi{doi_id}" for doi_id in doi_ids]
            hal_ids = [f"hal{hal_id}" for hal_id in hal_ids]
            fields_to_retrieve = [
                "affiliations"
            ]
            works = self.get_works_from_es_index_from_id_by_chunk(
                self.scanr_publications_index,
                hal_ids + doi_ids,
                fields_to_retrieve,
                query_type="private_sector"
            )

            nb_works = len(hal_ids)
            nb_found_works = len(works)
            print(f"Found {nb_found_works} works with private sector collaboration out of {nb_works} queried works")

            # Dictionary to store the count of collaborations per "Secteur privé" institution
            collaborations = defaultdict(int)

            for work in works:
                for affiliation in work.get('_source', {}).get('affiliations', []):
                    t1 = affiliation.get('typologie_1')
                    t2 = affiliation.get('typologie_2')
                    if t1 in PRIVATE_SECTOR_TYPOLOGIE_1 or t2 in PRIVATE_SECTOR_TYPOLOGIE_2:
                        if 'label' in affiliation:
                            name = affiliation['label'].get('default', affiliation['label'].get('fr', affiliation['label'].get('en', 'Unknown')))
                            if len(name) > 75:
                                name = name[:75]+"... "
                            collaborations[name] += 1

            self.data = dict(collaborations)
            # sort values
            self.data = {k: v for k, v in sorted(self.data.items(), key=lambda item: item[1])}

            if not self.data:
                self.data_status = DataStatus.NO_DATA
            else:
                self.data_status = DataStatus.OK

            self.generate_plot_info()
            return {"info": self.info}

        except Exception as e:
            return self._handle_fetch_error(e, "Error fetching or formatting private sector collaborations data")


class WorksBibtex(Biso):
    """
    A class to fetch the works of a HAL collection and render them as an HTML bibliography list.
    """

    figure_file_extension = "bib"
    html_figure_type = "html_list"

    def fetch_data(self) -> dict[str, Any]:
        """
        Fetch the data from HAL and convert it to bibtex.
        The bibtex data returned by HAL is not valid; therefore, we need to create our own bibtex string.
        The bibtex doesn't support mathematical expressions or other latex commands to avoid compilation errors.
        This could be improved in the future to support mathematical expressions and other special characters.

        :return: The info about the fetched data.
        :rtype: dict[str, Any]
        """
        def rep_cyr(text):
            """
            Replace cyrillic characters with question marks. Avoids errors in LaTeX when compiling.
            """
            return re.sub(r'[\u0400-\u04FF]', '?', text)

        try:
            url = (f"https://api.archives-ouvertes.fr/search/{self.entity_id}/?q=publicationDateY_i:{self.year}&"
                   f"wt=json&rows=0")
            self.n_entities_found = requests.get(url).json()["response"]["numFound"]
            if self.max_plotted_entities > 1000:
                logging.warning(
                    f"Max entities set to {self.max_plotted_entities}, but having more than 1000 entities in the "
                    f"bibliography will take too long to compile with LaTeX. "
                    f"Setting self.max_plotted_entities to 1000 and getting only 1000 elements from the API"
                )
                self.max_plotted_entities = 1000
            url = (
                f"https://api.archives-ouvertes.fr/search/{self.entity_id}/?q=publicationDateY_i:{self.year}&wt=json&"
                f"rows={self.max_plotted_entities}&fl=title_s,authFullName_s,uri_s,journalTitle_s,journalPublisher_s,"
                f"volume_s,page_s,publicationDateY_i,doiId_s,halId_s,label_bibtex"
            )
            works = requests.get(url).json().get('response', {}).get('docs', [])
            # Define regex pattern to extract the type of entry
            type_pattern = r'@(\w+)'
            self.data = {}
            for work in works:
                titles = work.get("title_s", [])
                authors = [str(author) for author in work.get("authFullName_s", [""])]
                # Extract the type of entry
                type_match = re.search(type_pattern, str(work.get("label_bibtex", "")))
                if type_match:
                    entry_type = type_match.group(1)
                else:
                    entry_type = "misc"
                ref = {
                    "TITLE": str(titles[0] if len(titles) > 0 else ""),
                    "AUTHOR": " and ".join(authors),
                    "URL": str(work.get("uri_s", "")),
                    "JOURNAL": str(work.get("journalTitle_s", "")),
                    "PUBLISHER": str(work.get("journalPublisher_s", "")),
                    "VOLUME": str(work.get("volume_s", "")),
                    "PAGES": str(work.get("page_s", "")),
                    "YEAR": str(work.get("publicationDateY_i", "")),
                    "DOI": str(work.get("doiId_s", "")),
                    "HAL_ID": str(work.get("halId_s", "")),
                    "bibtex_entry_type": entry_type
                }
                self.data[work['halId_s']] = ref
            if not self.data:
                self.data_status = DataStatus.NO_DATA
            else:
                self.data_status = DataStatus.OK
            self.generate_plot_info()
            return {"info": self.info}
        except Exception as e:
            return self._handle_fetch_error(e, "Error fetching or formatting Hal Bibtex data")


    def get_figure(self) -> str:
        """
        Generate an HTML bibliography list.

        :return: HTML <ol> with one <li> per work.
        :rtype: str
        """
        import html as html_lib
        if self.data_status == DataStatus.NOT_FETCHED:
            self.fetch_data()
        if self.data_status == DataStatus.NO_DATA:
            return f'<p class="dibiso-no-data">{html_lib.escape(self._("No data"))}</p>'
        if self.data_status == DataStatus.ERROR:
            return f'<p class="dibiso-error">{html_lib.escape(self._("Error while making the bibliography"))}</p>'

        items = []
        for work in self.data.values():
            authors = html_lib.escape(work.get("AUTHOR", ""))
            title = html_lib.escape(work.get("TITLE", ""))
            journal = html_lib.escape(work.get("JOURNAL", ""))
            year = html_lib.escape(work.get("YEAR", ""))
            url = html_lib.escape(work.get("URL", ""))
            doi = html_lib.escape(work.get("DOI", ""))
            doi_part = f' DOI: <a href="https://doi.org/{doi}">{doi}</a>' if doi else ""
            url_part = f' <a href="{url}">[HAL]</a>' if url else ""
            items.append(
                f"<li>{authors}. <em>{title}</em>. {journal} ({year}).{doi_part}{url_part}</li>"
            )
        return f'<ol class="dibiso-bibliography">{"".join(items)}</ol>'


class WorksType(Biso):
    """
    A class to fetch and plot data about work types.
    """

    def __init__(self, entity_id, year: int | None = None, **kwargs):
        """
        Initialize the WorksType class.

        :param entity_id: The HAL collection identifier. This usually refers to the entity id acronym.
        :type entity_id: str
        :param year: The year for which to fetch data. If None, uses the current year.
        :type year: int | none, optional
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        """
        super().__init__(entity_id, year, **kwargs)


    def fetch_data(self) -> dict[str, Any]:
        """
        Fetch data about work types from the HAL API.

        This method queries the API to get the list of work types and their counts.
        It processes the data to create a dictionary where keys are work type names and values are their respective
        counts.

        :return: The info about the fetched data.
        :rtype: dict[str, Any]
        """
        try:
            stats_url = (
                f"https://api.archives-ouvertes.fr/search/{self.entity_id}/?q=publicationDateY_i:{self.year} AND "
                "docType_s:(COMM)&wt=json&rows=0&stats=true&stats.field={!count=true+cardinality=true}docType_s"
            )
            res = requests.get(stats_url).json()
            self.n_entities_found = (res.get('stats', {}).get('stats_fields', {}).get('docType_s', {}).
                                     get('cardinality', 0))
            facet_url=(
                f"https://api.archives-ouvertes.fr/search/{self.entity_id}/?q=publicationDateY_i:{self.year} &"
                f"wt=json&rows=0&facet=true&facet.pivot=docType_s&facet.limit={self.max_plotted_entities}"
                "&facet.mincount=1"
            )
            res = requests.get(facet_url).json()
            self.n_entities_found = (res.get('stats', {}).get('stats_fields', {}).get('docType_s', {}).
                                     get('cardinality', 0))
            document_types_list = res.get('facet_counts', {}).get('facet_pivot', {}).get('docType_s', [])
            if not document_types_list:
                self.data_status = DataStatus.NO_DATA
            else:
                self.data = {
                    get_hal_doc_type_name(doc_type['value']): doc_type['count'] for doc_type in document_types_list
                }
                self.data_status = DataStatus.OK
            self.generate_plot_info()
            return {"info": self.info}
        except Exception as e:
            return self._handle_fetch_error(e, "Error fetching or formatting work types data")

class Data(Biso):
    """
    A class to fetch data about shared datasets from the BSO index and the DataCite API
    """
    figure_file_extension = "pdf"
    html_figure_type = "plotly"

    def __init__(self, entity_id: str, year: int | None = None, ror_id: str | None = None,**kwargs):
        """
        Initialize the Data class.
        """
        super().__init__(entity_id, year, **kwargs)
        self.ror_id = ror_id

    def fetch_data(self) -> dict[str, Any]:
        """
        Fetch number of datasets from scanr bso
        Fetch datasets by publishers/licenses from DataCite
        """
        try:
            # BSO
            if self.scanr_api_url is None:
                self.data_status = DataStatus.ERROR
                stats = {
                    'total_bso_pubs': self._("Error"),
                    'nb_pubs_with_data': self._("Error"),
                    'percentage_data': self._("Error"),
                    'bso_datasets_phrase': self._("Error"),
                    'info': self._("Error")
                }
                return stats

            # Taking only articles from bso
            doi_ids = self.get_all_ids_with_cursor(id_type="doi", doc_types=["ART"])
            hal_ids = self.get_all_ids_with_cursor(id_type="hal", doc_types=["ART"])
            
            doi_ids = [f"doi{doi_id}" for doi_id in doi_ids]
            hal_ids = [f"hal{hal_id}" for hal_id in hal_ids]
            
            fields_to_retrieve = [
                "datastet_details.has_shared"
            ]

            works = self.get_works_from_es_index_from_id_by_chunk(
                self.scanr_bso_index,
                hal_ids + doi_ids,
                fields_to_retrieve
            )

            total_bso_pubs = len(works)
            nb_found_datasets=0
            nb_shared_datasets = 0

            for work in works:
                source = work.get('_source', {})
                dataset_obj = source.get("datastet_details")
                if dataset_obj and isinstance(dataset_obj, dict):
                    has_shared = dataset_obj.get("has_shared")
                    if has_shared is not None:
                        nb_found_datasets += 1
                        if has_shared is True:
                            nb_shared_datasets += 1

            percentage_found = (nb_found_datasets / total_bso_pubs * 100) if total_bso_pubs > 0 else 0.0
            percentage_shared_on_found = (nb_shared_datasets / nb_found_datasets * 100) if nb_found_datasets > 0 else 0.0

            bso_datasets_phrase = (
                f"Sur un total de {total_bso_pubs} publications présentes dans le BSO sur l'année {self.year}, "
                f"l'information sur les données a été détectée pour {nb_found_datasets} d'entre elles ({percentage_found:.0f}% des publications). "
                f"Parmi ces publications, {nb_shared_datasets}/{nb_found_datasets} ont effectivement partagé un jeu de données "
                f"({percentage_shared_on_found:.0f}% des publications détectées)."
            )
            self.info = bso_datasets_phrase

            if total_bso_pubs == 0:
                self.data_status = DataStatus.NO_DATA
            else:
                self.data_status = DataStatus.OK

            # DataCite

            if self.ror_id:
                institution_ror = self.ror_id if self.ror_id.startswith("https://ror.org/") else f"https://ror.org/{self.ror_id}"
                url = (
                    f"https://api.datacite.org/dois?resource-type-id=dataset"
                    f"&affiliation-id={institution_ror}"
                    f"&query=!relatedIdentifiers.relationType:IsVersionOf"
                    f"&registered={self.year}"
                    f"&page[size]=1000"
                )
                response = requests.get(url)
                response.raise_for_status()
                datacite_data = response.json()

                datacite_nb_datasets_found = datacite_data.get('meta', {}).get('total', 0)
                datacite_datasets = datacite_data.get('data', [])

                publishers=[]
                licenses=[]

                for dataset in datacite_datasets:
                    attributes = dataset.get('attributes', {})

                    publishers.append(attributes.get('publisher','Unknown'))

                    rights_list=attributes.get('rightsList', [])
                    if rights_list and isinstance(rights_list, list):
                        license_id = rights_list[0].get('rightsIdentifier', '')
                    if re.search(r"CC.{0,3}?BY", license_id, re.IGNORECASE):
                        licenses.append("CC-BY")
                    elif re.search(r"CC.{0,3}?0", license_id, re.IGNORECASE):
                        licenses.append("CC0")
                    else:
                        licenses.append("others")

                # Keeps only the 5 principal publishers (rest goes to "others")
                pub_dict = {p: publishers.count(p) for p in set(publishers)}
                pub_sorted = [(p, count) for count, p in sorted([(count, p) for p, count in pub_dict.items()], reverse=True)]
                top_5 = pub_sorted[:5]
                others_total=sum(count for p, count in pub_sorted[5:])
                self.grouped_publishers = [p for p, count in top_5]
                self.counts_publishers = [count for p, count in top_5]
                if others_total > 0:
                    self.grouped_publishers.append("others")
                    self.counts_publishers.append(others_total)

                self.grouped_licenses = list(set(licenses))
                self.counts_licenses = [licenses.count(l) for l in self.grouped_licenses]

                if datacite_nb_datasets_found == 0 and total_bso_pubs == 0:
                    self.data_status = DataStatus.NO_DATA
                else:
                    self.data_status = DataStatus.OK

            self.generate_plot_info()
            return {
                'total_bso_pubs': total_bso_pubs,
                'nb_found_datasets': nb_found_datasets,
                'bso_datasets_phrase': bso_datasets_phrase,
                'info': self.info
            }

        except Exception as e:
            return self._handle_fetch_error(e, "Error fetching or formatting datasets data")

    def get_figure(self) -> str:
        if self.data_status == DataStatus.NOT_FETCHED:
            self.fetch_data()
        if self.data_status == DataStatus.NO_DATA or not self.ror_id:
            return self.get_no_data_plot()
        if self.data_status == DataStatus.ERROR:
            return self.get_error_plot()
        
        fig=make_subplots(
            rows=2, cols=1,
            subplot_titles=(
                f"{self._('Distribution of datasets by repository')} ({self.year} source: DataCite)",
                f"{self._('Distribution of datasets by license')} ({self.year} source: DataCite)"
            ),
            vertical_spacing=0.2
        )
        bar_width_val = 0.5

        # plot by publishers
        fig.add_trace(
            go.Bar(
                x=self.counts_publishers,
                y=self.grouped_publishers,
                marker_color=self.main_color,
                orientation='h',
                showlegend=False,
                width=bar_width_val,
                text=self.counts_publishers,
                textposition=self.text_position if hasattr(self, 'text_position') else "outside",
                cliponaxis=False
            ),
            row=1, col=1
        )

        # plot by licenses
        fig.add_trace(
            go.Bar(
                x=self.counts_licenses,
                y=self.grouped_licenses,
                marker_color=self.main_color,
                orientation='h',
                showlegend=False,
                width=bar_width_val,
                text=self.counts_licenses,
                textposition=self.text_position if hasattr(self, 'text_position') else "outside",
                cliponaxis=False
            ),
            row=2, col=1
        )

        fig.update_layout(
            width=self.width,
            height=self.height if self.height else 600,
            margin=self.margin,
            template=self.template if hasattr(self, 'template') else "simple_white",
            barmode='stack',
            barcornerradius=self.barcornerradius if hasattr(self, 'barcornerradius') else 10,
            showlegend=False,
            margin_t=30
        )

        # orders plots (with "others" to the end)
        custom_order = list(reversed(self.grouped_publishers))
        if "others" in custom_order:
            custom_order.remove("others")
            custom_order.insert(0, "others")
        fig.update_yaxes(categoryorder='array', categoryarray=custom_order, row=1, col=1)
        fig.update_yaxes(categoryorder="array", categoryarray=["others", "CC0", "CC-BY"], row=2, col=1)

        return fig