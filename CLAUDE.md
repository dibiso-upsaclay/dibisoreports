# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a multi-module workspace for generating automated bibliometric reports at Université Paris-Saclay's DiBISO department. Two report types are supported:
- **BiSO** (Bilan Science Ouverte): open-science annual reports for research labs
- **PubPart** (Publications & Partnerships): topic/institution/collaboration analysis

The workspace contains 6 subprojects: two Python libraries (`dibisoreporting`, `dibisoplot`), an HTML template collection (`dibiso-html-templates`), a legacy LaTeX template collection (`dibiso-latex-templates`, unused by the current pipeline), a FastAPI backend (`dibiso-reporting-api`), and a React frontend (`dibiso-reporting-webapp`).

## Development Commands

### Python libraries

```bash
# Install in development mode from repo root
pip install -e dibisoreporting/
pip install -e dibisoplot/

# Build a distribution
cd dibisoreporting/   # or dibisoplot/
python -m build
python -m twine upload dist/*
```

### API + Webapp — Docker (recommended)

```bash
# From repo root — deploys both services together
cp .env.template .env   # fill in secrets (see .env.template for required vars)
docker compose up -d --build
# Interface: http://localhost:8080  API: http://localhost:8000
```

### API (`dibiso-reporting-api/`)

```bash
cp .env.template .env   # then fill in secrets
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Webapp (`dibiso-reporting-webapp/`)

```bash
cp .env.template .env   # set VITE_API_URL
npm install
npm run dev      # dev server (http://localhost:3000)
npm run build    # production build
npm run lint     # ESLint
```

There are no automated test suites; validation is done manually via the API and webapp.

## Architecture

### Data flow

```
React Webapp  →  FastAPI  →  background thread:
                               1. fetch data (HAL / OpenAlex / ScanR APIs)
                               2. dibisoplot  → Plotly figures (SVG files)
                               3. dibisoreporting → Jinja2 HTML rendering
                                  (saves figures.json + context.json + inlined HTML for preview)
                             ↓
                          results page: Report PDF / Bibliography PDF / Export ZIP cards
                          (all three available immediately, each rendered on click)
                             ↓
                          GET /download-pdf?file_name=report|biblio
                            → render_from_saved() + WeasyPrint for that one file only
                          POST /export → render_from_saved() + WeasyPrint for both files
                                          + ZIP of the whole project (PyMuPDF optional background overlay)
                             ↓
                          PDF/ZIP download via authenticated endpoint
```

WeasyPrint is never invoked during the initial background compilation — only HTML
(for the edit view) and a ZIP of the raw project are produced there. Each of the three
download buttons triggers its own render: `/download-pdf` re-renders and produces just
the requested PDF, `/export` re-renders and produces both PDFs plus the bundled ZIP.
Each click re-renders from the latest saved analyses, so edits are always reflected.

Reports have a single success status (`completed`) once data fetching + HTML rendering
succeed. `failed` covers data/HTML errors.

### Key class hierarchy

**`DibisoReporting`** (`dibisoreporting/dibisoreporting/dibisoreporting.py`)
- Manages Jinja2 HTML template directory (local path or GitHub release URL)
- Orchestrates figure generation by instantiating `dibisoplot` classes
- `generate_report()` saves SVG figures, `figures.json`, `context.json`, and rendered HTML
- `render_from_saved(root_path, analyses)` re-renders HTML from saved data (used for the edit/export flow)
- `Biso` and `PubPart` subclasses live in their respective subdirectories

**`Dibisoplot`** (`dibisoplot/dibisoplot/dibisoplot.py`)
- Base for all chart types; wraps Plotly with consistent styling
- Tracks per-figure data status: `NOT_FETCHED`, `OK`, `NO_DATA`, `ERROR`
- Dynamic height calculation for horizontal bar charts
- 12 BiSO visualization subclasses in `dibisoplot/dibisoplot/biso/biso.py` (e.g. `AnrProjects`, `CollaborationMap`, `Journals`, `WorksType`)

**FastAPI app** (`dibiso-reporting-api/app/main.py`)
- JWT auth (48-hour tokens, `OAuth2PasswordBearer`)
- Report jobs run in a `ThreadPoolExecutor` (default 4 workers, configurable via env)
- `REPORT_SECTIONS` registry defines the ordered sections for BiSO and PubPart
- Compilation status tracked with progress % and current step; supports cancellation
- Auto-cleanup of old temp directories (prefix `html_output_`, configurable retention)
- SVG style-to-attribute conversion (`_convert_svg_style_to_attrs`) for WeasyPrint compatibility
- CSS/asset inlining (`_inline_assets_in_html`) for self-contained HTML export
- Key endpoints:
  - `POST /generate-report` — start report generation
  - `GET /compilation-status/{comp_id}` — poll progress
  - `POST /cancel-compilation/{comp_id}` — cancel running job
  - `GET /report-sections/{comp_id}` — list editable sections after generation
  - `GET/PUT /analyses/{comp_id}/{section_id}` — load/save per-section Markdown analyses
  - `GET /figures/{comp_id}/{figure_name}` — serve SVG figure for editor preview
  - `POST /export/{comp_id}` — re-render HTML with analyses + produce PDF+ZIP (backs the "Export ZIP" button)
  - `GET /download-pdf?temp_id={comp_id}&file_name=report|biblio` — re-render with analyses + produce just that PDF, then download it (backs the "Report PDF" / "Bibliography PDF" buttons)
  - `GET /download-zip`, `GET /download-html` — download already-produced outputs
  - `GET /hal-collections?q=` — autocomplete HAL collection codes (min. 3 chars); backed by a local copy of the HAL OAI `ListSets` "collection:" sets (`app/hal_collections.py`, stored in `USERS_DATABASE_DIRECTORY`, fetched at startup if missing/stale and refreshed nightly)
  - `GET /template-assets/{file_path}` — serve CSS/image assets from the HTML template (public, restricted to `css/` and `assets/`)

**React frontend** (`dibiso-reporting-webapp/src/App.jsx`)
- Single-file component; EN/FR toggle via `TRANSLATIONS` object
- Handles: auth, report form, status polling, downloads, admin user management
- After generation: shows edit view with per-section Markdown editor and figure preview
- "Export ZIP" button re-renders HTML with analyses (inlined CSS, embedded SVGs) via `/export`

### HTML template pipeline

`dibiso-html-templates/` contains the Jinja2 templates and CSS. The template directory is:
- **Docker**: bind-mounted read-only at `/html_templates` (from repo root `./dibiso-html-templates`)
- **Local dev**: pointed to by `HTML_TEMPLATE_PATH` in `.env`
- **Fallback**: downloaded from GitHub release URL (`HTML_TEMPLATE_URL`)

The template directory must have a `dibiso-html/` subdirectory inside it (i.e. `HTML_TEMPLATE_PATH` points to the **parent** of `dibiso-html/`).

### External API dependencies

- **HAL** (`https://api.archives-ouvertes.fr/`) — publication metadata and collection validation
- **OpenAlex** — bibliometric analysis (via `openalex-analysis` / `pyalex`)
- **ScanR** — French research project data (ANR, European projects, BSO journals)
- **GitHub API** — fetching latest HTML template releases (fallback only)

### Environment configuration

The recommended way is to copy `.env.template` (at the repo root) to `.env` and fill in the secrets — this single file drives both the root `docker-compose.yml` and has comments explaining every variable.

For local dev, each service has its own `.env.template`:
- `dibiso-reporting-api/.env.template` — API-specific settings
- `dibiso-reporting-webapp/.env.template` — `VITE_API_URL` only

Key variables (all have defaults except those marked required):
- `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `SECRET_KEY` — **required**
- `SCANR_API_PASSWORD`, `SCANR_API_URL`, `SCANR_API_USERNAME`, `SCANR_BSO_INDEX`, `SCANR_PUBLICATIONS_INDEX` — **required**
- `OPENALEX_API_KEY`, `OPENALEX_EMAIL` — recommended for rate limits
- `HTML_TEMPLATE_PATH` — local path to `dibiso-html-templates/`; if absent, template is downloaded from `HTML_TEMPLATE_URL`
- `DATA_FETCHING_TIMEOUT_SECONDS` — default 1200 (needed for large labs)
- `VITE_API_URL` — URL the browser uses to reach the API (baked into the webapp at build time)

The SQLite user database schema: `id, username, email, hashed_password, role (user|admin), is_active, created_at, first_name, last_name`.
