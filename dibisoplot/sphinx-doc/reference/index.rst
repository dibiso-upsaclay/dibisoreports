Reference
=========

.. toctree::
   :maxdepth: 1

   dibisoplot
   biso
   pubpart
   translation
   utils


dibisoplot
----------

.. currentmodule:: dibisoplot.dibisoplot

.. autosummary::

   DataStatus
   Dibisoplot
   Dibisoplot.__init__
   Dibisoplot.generate_plot_info
   Dibisoplot.get_no_data_plot
   Dibisoplot.get_error_plot
   Dibisoplot.get_figure


Biso
----

.. currentmodule:: dibisoplot.biso

.. autosummary::

   Biso.__init__
   Biso.get_all_ids_with_cursor
   Biso.connect_to_elasticsearch
   Biso.get_works_from_es_index_from_id
   Biso.get_works_from_es_index_from_id_and_private_sector
   Biso.get_works_from_es_index_from_id_by_chunk
   AnrProjects.__init__
   AnrProjects.fetch_data
   Chapters.__init__
   Chapters.fetch_data
   Chapters.get_figure
   CollaborationMap.__init__
   CollaborationMap.fetch_data
   CollaborationMap.get_figure
   CollaborationNames.__init__
   CollaborationNames.fetch_data
   Conferences.__init__
   Conferences.fetch_data
   EuropeanProjects.__init__
   EuropeanProjects.fetch_data
   Journals.__init__
   Journals.fetch_data
   Journals.get_figure
   JournalsHal.__init__
   JournalsHal.fetch_data
   OpenAccessWorks.__init__
   OpenAccessWorks.fetch_data
   OpenAccessWorks.get_figure
   PrivateSectorCollaborations.__init__
   PrivateSectorCollaborations.fetch_data
   WorksBibtex.fetch_data
   WorksBibtex.get_figure
   WorksType.__init__
   WorksType.fetch_data


PubPart
-------

.. currentmodule:: dibisoplot.pubpart

.. autosummary::

   PubPart.__init__
   PubInstitutions.__init__
   PubInstitutions.fetch_data
   PubTopics.fetch_data
   Collaborations.__init__
   Collaborations.fetch_collab_data
   InstitutionsLineageCollaborations.fetch_data
   TopicsCollaborations.fetch_data
   TopicsPotentialCollaborations.fetch_data
   WorksCollaborations.__init__
   WorksCollaborations.fetch_data


translation
-----------

.. currentmodule:: dibisoplot.translation

.. autosummary::

   get_translator


utils
-----

.. currentmodule:: dibisoplot.utils

.. autosummary::

   get_hal_doc_type_name
   get_empty_plot_with_message
   get_bar_width
   format_structure_name
