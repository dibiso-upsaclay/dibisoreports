%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%                                    %%%%%%%%%%
%%%%%%%%%%  You can reuse this work under:    %%%%%%%%%%
%%%%%%%%%%  LPPL-1.3c OR GPL-3.0-only         %%%%%%%%%%
%%%%%%%%%%                                    %%%%%%%%%%
%%%%%%%%%%  Romain THOMAS 2025                %%%%%%%%%%
%%%%%%%%%%  contact@romainthomas.net          %%%%%%%%%%
%%%%%%%%%%  DiBISO - Université Paris-Saclay  %%%%%%%%%%
%%%%%%%%%%                                    %%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{dibiso/biso}[2025 BiSO template by Romain THOMAS]

\newcommand{\templatetype}{article}

\newcommand{\titlepagelabellogo}{label-science-ouverte.pdf}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%% IMPORTS %%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\RequirePackage{import} % for file imports relative to path

\ifdefined\classdir
  % nothing to do, path already defined
\else
  % set the path to default
  \def\classdir{dibiso}
\fi

\import{\classdir}{biso-colors}
\import{\classdir}{biso-dimensions}
\import{\classdir}{template-base}



%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%% LAST PAGE %%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


\newcommand{\makelastpagecontactus}{
  \subsection*{Contactez-nous !}

  Pour échanger à propos de ce rapport ou tout autre questions liées à la science ouverte et vos publications, n'hésitez pas à contacter votre {\fontseries{sb}\selectfont référent·e laboratoire :}

  \ifx\@reporter\empty\else
    \thereporter
  \fi
  \ifx\@reporter\empty\else
    \ifx\@reporteremail\empty\else
      ~-
    \fi
  \fi
  \ifx\@reporteremail\empty\else
    \href{mailto:\thereporteremail}{\thereporteremail}
  \fi
}


\newcommand{\makelastpagedatasources}{
  \subsection*{Source des données:}
  
  \begin{description}[leftmargin=0cm, font=\fontseries{sb}\selectfont]
    \conditionalitem{\href{https://hal.science/}{HAL}:}{fig_jorunals_hal,fig_conferences,fig_doc_type,fig_open_access_works,fig_collab_map,fig_collab_map_europe,fig_collab_names,fig_private_collab,fig_eu_projects,fig_anr_projects}{tab_chapters,tab_journals}

    \conditionalitem{\href{https://openalex.org/}{OpenAlex}:}{fig_collab_map,fig_collab_map_europe}{}

    \conditionalitem{\href{https://scanr.enseignementsup-recherche.gouv.fr/}{scanR}:}{fig_private_collab}{}

    \conditionalitem{\href{https://barometredelascienceouverte.esr.gouv.fr/}{Baromètre français de la Science Ouverte}:}{}{tab_journals}
    
    % Add fallback item if no items were added
    \ifnum\value{descriptionitems}=0
      \item[No data sources]
    \fi
  \end{description}

  \vspace{-1ex}
  Données téléchargées le : \datafetchdate
}


% icons from https://simpleicons.org/
\newcommand{\makelastpagecode}{
  \subsection*{Code:}
    {\fontseries{sb}\selectfont Analyses et visualisations:} \begin{description}[labelsep=2ex]
      \item \raisebox{-0.2\baselineskip}{\includegraphics[height=\the\baselineskip, width=\the\baselineskip, keepaspectratio]{\classdir /icons/pypi.eps}} ~ \href{https://pypi.org/project/dibisoplot/}{\texttt{dibisoplot}} v\dibisoplotversion
      \item \raisebox{-0.2\baselineskip}{\includegraphics[height=\the\baselineskip, width=\the\baselineskip, keepaspectratio]{\classdir /icons/doi.eps}} ~ \href{https://doi.org/10.5281/zenodo.17251536}{\texttt{10.5281/zenodo.17251536}}
      \item \raisebox{-0.2\baselineskip}{\includegraphics[height=\the\baselineskip, width=\the\baselineskip, keepaspectratio]{\classdir /icons/github.eps}} ~ \url{https://github.com/dibiso-upsaclay/dibisoplot}
    \end{description}
    {\fontseries{sb}\selectfont Modèle \LaTeX:} \begin{description}[labelsep=2ex]
      \item \raisebox{-0.2\baselineskip}{\includegraphics[height=\the\baselineskip, width=\the\baselineskip, keepaspectratio]{\classdir /icons/doi.eps}} ~ \href{https://doi.org/10.5281/zenodo.17251825}{\texttt{10.5281/zenodo.17251825}}
      \item \raisebox{-0.2\baselineskip}{\includegraphics[height=\the\baselineskip, width=\the\baselineskip, keepaspectratio]{\classdir /icons/github.eps}} ~ \url{https://github.com/dibiso-upsaclay/dibiso-latex-templates}
    \end{description}
    {\fontseries{sb}\selectfont Génération du rapport:} \begin{description}[labelsep=2ex]
      \item \raisebox{-0.2\baselineskip}{\includegraphics[height=\the\baselineskip, width=\the\baselineskip, keepaspectratio]{\classdir /icons/pypi.eps}} ~ \href{https://pypi.org/project/dibisoreporting/}{\texttt{dibisoreporting}} v\dibisoreportingversion

      \item \raisebox{-0.2\baselineskip}{\includegraphics[height=\the\baselineskip, width=\the\baselineskip, keepaspectratio]{\classdir /icons/doi.eps}} ~ \href{https://doi.org/10.5281/zenodo.17251577}{\texttt{10.5281/zenodo.17251577}}
      \item \raisebox{-0.2\baselineskip}{\includegraphics[height=\the\baselineskip, width=\the\baselineskip, keepaspectratio]{\classdir /icons/github.eps}} ~ \url{https://github.com/dibiso-upsaclay/dibisoreporting}
    \end{description}
    {\fontseries{sb}\selectfont API application web:} \begin{description}[labelsep=2ex]
      \item \raisebox{-0.2\baselineskip}{\includegraphics[height=\the\baselineskip, width=\the\baselineskip, keepaspectratio]{\classdir /icons/github.eps}} ~ \url{https://github.com/dibiso-upsaclay/dibiso-reporting-api}
    \end{description}
    {\fontseries{sb}\selectfont Application web:} \begin{description}[labelsep=2ex]
      \item \raisebox{-0.2\baselineskip}{\includegraphics[height=\the\baselineskip, width=\the\baselineskip, keepaspectratio]{\classdir /icons/github.eps}} ~ \url{https://github.com/dibiso-upsaclay/dibiso-reporting-webapp}
    \end{description}
    {\fontseries{sb}\selectfont Rapport technique:} \begin{description}[labelsep=2ex]
      \item \raisebox{-0.2\baselineskip}{\includegraphics[height=\the\baselineskip, width=\the\baselineskip, keepaspectratio]{\classdir /icons/hal.eps}} ~ \url{https://universite-paris-saclay.hal.science/hal-05336463}
    \end{description}
}


\newcommand{\makelastpageauthors}{
  \vspace{10mm}

  % hide reporter name if not specified
  \ifthenelse{\equal{\thereporter}{}}{}{Rédaction : \thereporter \\}
  Conception : Henri Bretel \orcidlink{0000-0001-6922-0915}, Delphine Le Piolet \orcidlink{0000-0001-9756-4408}, Laili Rahimie \orcidlink{0009-0007-7119-215X}, Romain Thomas \orcidlink{0009-0008-9900-1930} \\
  Programmation : Romain Thomas \orcidlink{0009-0008-9900-1930}
}



\newcommand{\makelastpagefooter}{
  \vfill
  
  \raggedright
  {\Large\titlefont\fontseries{sb}\selectfont L'équipe Science Ouverte}
  \begin{tikzpicture}[every node/.style={inner sep=0,outer sep=0}]
    \node[shading=axis, rounded rectangle, left color=titlepagegradientcolora, right color=titlepagegradientcolorb, shading angle=90, minimum width=\textwidth, minimum height=\logorulewidth] {};
  \end{tikzpicture}
  
  \begin{minipage}{8cm}
    \small
    \smallskip
    
    \href{mailto:science.ouverte@universite-paris-saclay.fr}{science.ouverte@universite-paris-saclay.fr}
    
    \smallskip
    
    \url{https://www.universite-paris-saclay.fr/recherche/science-ouverte}
  \end{minipage}
  \hfill
  \begin{minipage}{6cm}
    \small
    % https://simpleicons.org/
    \includegraphics[height=\the\baselineskip, width=\the\baselineskip, keepaspectratio]{\classdir /icons/bluesky.eps} ~ \href{https://bsky.app/profile/so-upsaclay.bsky.social}{@so-upsaclay.bsky.social}
    
    \smallskip
    
    \includegraphics[height=\the\baselineskip, width=\the\baselineskip, keepaspectratio]{\classdir /icons/mastodon.eps} ~ \href{https://social.sciences.re/@SO_UPSaclay}{social.sciences.re/@SO\_UPSaclay}
  \end{minipage}
  
  \vspace{2mm}
  
  \includegraphics[width=\linewidth]{\classdir /frise_upsaclay.eps}
  
  \vspace{2mm}
  
  \newcommand{\licenceslogo}{
    \href{https://creativecommons.org/licenses/by/4.0/}{\includegraphics[height=\the\dimexpr 2\baselineskip \relax]{\classdir /icons/by.eps}}
    \hspace{3mm}
    \href{https://www.etalab.gouv.fr/licence-ouverte-open-licence/}{\includegraphics[height=\the\dimexpr 2\baselineskip \relax]{\classdir /icons/etalab_licence.png}}
  }
  
  \begin{minipage}[c][\the\dimexpr 2\baselineskip \relax][c]{.47\linewidth}
    \begin{flushleft}
      \small Direction des Bibliothèques, de l'Information et de la Science Ouverte (DiBISO)
    \end{flushleft}
  \end{minipage}
  \hfill
  \begin{minipage}[c][\the\dimexpr 2\baselineskip \relax][c]{\widthof{\licenceslogo}}
    \licenceslogo
  \end{minipage}
  
  \vspace{-1cm}
}


\newcommand{\makelastpagereport}{
  \pagebreak
  \small
  \vspace*{-15mm}
  
  \thispagestyle{empty}
  
  \makelastpagecontactus
  
  \makelastpagedatasources
  
  \makelastpagecode
  
  \makelastpageauthors
  
  \makelastpagefooter
}


\newcommand{\makelastpagebiblio}{
  \pagebreak
  \small
  \vspace*{-15mm}
  
  \thispagestyle{empty}
  
  \subsection*{Source des données:}
  \begin{description}
    \item[\href{https://hal.science/}{HAL}:] Références
  \end{description}
  \vspace{-1ex}
  Données téléchargées le : \datafetchdate
  
  \makelastpagecode
  
  \vfill
  \vfill
  \vfill
  
  \makelastpageauthors
  
  \makelastpagefooter
}

