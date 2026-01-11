# DiBISO plot

A Python library for plotting bibliometric research data, developed at the [DiBISO](https://www.bibliotheques.universite-paris-saclay.fr/en/department-libraries-information-and-open-science-dibiso-and-its-missions).

For more details about this project, you can read our [technical report](https://universite-paris-saclay.hal.science/hal-05336463).

Install with:

```bash
pip install dibisoplot
```

The library contains the following submodules:

  - `biso`: plot data for the BiSO (Open-Science Report)
  - `pubpart`: plot data about publications and partnerships


Homepage: https://pypi.org/project/dibisoplot/

Documentation: https://dibiso-upsaclay.github.io/dibisoplot/

Repository URL: https://github.com/dibiso-upsaclay/dibisoplot

Repository DOI: https://doi.org/10.5281/zenodo.17251536

Technical report: https://universite-paris-saclay.hal.science/hal-05336463


## About the BiSO

The BiSO (Bilan Science Ouverte - Open Science Report) is an annual report produced for each research laboratory under 
the responsibility of the Open Science teams (DiBISO) at Université Paris-Saclay. 
Prepared in collaboration with the laboratories, it is based on open data, mainly coming from the [HAL](https://hal.science/) repository but 
also from [OpenAlex](https://openalex.org/), [scanR](https://scanr.enseignementsup-recherche.gouv.fr/) and the [BSO](https://barometredelascienceouverte.esr.gouv.fr/). 
The BiSO presents indicators such as publication types, open access rates, and collaborations. 
Primarily intended for the laboratories under our scope, the report supports the development of open science practices. 
The code and template are shared under open-source licenses, allowing other institutions to reuse and adapt the 
methodology.

## About the Publications and Partnerships

This submodule uses data from [OpenAlex](https://openalex.org/) to make plots about publication topics, institutions, and citations, as 
well as common publication topics and potential collaboration topics with other institutions.

Romain THOMAS 2025  
Department of Libraries, Information and Open Science (DiBISO)  
Université Paris-Saclay