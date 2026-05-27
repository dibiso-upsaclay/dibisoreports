# DiBISO LaTeX templates

LaTeX templates used by the DiBISO at the Université Paris-Saclay to generate reports.

License: LPPL 1.3c or GPL 3.0

## Report types

This repository contains the following templates:

  - `BiSO`: Bilan de la Science Ouverte (open-science report)
  - `PubPart`: Publications & Partnerships

  
## Usage

To compile the templates, you need to use LuaLaTeX.

1. Place the folder `dibiso` where `your-main-file.tex` is located. For  `your-main-file.tex`, you can use an example file from the repository
2. Import the class: if `dibiso` and `your-main-file.tex` are in the same directory, use `\documentclass[french, 11pt]{dibiso/biso}`
3. Compile with: `lualatex your-main-file.tex`


## Previews

### BiSO

[![BiSO report example](docs/images/biso-example/biso-example.png)](examples/biso/biso-main.pdf)


### PubPart

[![PubPart report example](docs/images/pubpart-example/pubpart-example.png)](examples/pubpart/pubpart-main.pdf)



## Authors

This work is dual-licensed under GPL 3.0 (GNU General Public License v3.0 only) or LPPL 1.3c (LaTeX Project Public License v1.3c). You can choose between one of them if you use this work.

Design: Henri Bretel, Robin Millman, Delphine Le Piolet, Laili Rahimie, Romain Thomas

DOI: https://doi.org/10.5281/zenodo.17251825  
Repository: https://github.com/dibiso-upsaclay/dibiso-latex-templates/  
Technical report: https://universite-paris-saclay.hal.science/hal-05336463

Romain THOMAS 2025  
DiBISO (Direction des Bibliothèques, de l'Information et de la Science Ouverte)  
Université Paris-Saclay
