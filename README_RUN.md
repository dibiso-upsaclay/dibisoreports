# DiBISOreports — Guide de démarrage et génération de rapports

Ce guide décrit comment démarrer l'application et générer un rapport BiSO.
Deux modes sont disponibles : **Docker** (recommandé pour la production) et **développement local** (Windows, sans Docker).

---

## Prérequis communs

| Outil | Rôle |
|-------|------|
| Git | Cloner le dépôt |
| Docker + Docker Compose | Déploiement recommandé |
| Python 3.12+ | Développement local uniquement |
| Node.js / npm 22+ | Développement local uniquement |

---

## 1. Structure du projet

```
dibisoreports/
├── docker-compose.yml       ← Point d'entrée unique (API + webapp)
├── .env.template            ← Configuration consolidée
├── dibiso-html-templates/   ← Templates Jinja2 HTML (monté en lecture seule)
│   └── dibiso-html/
├── dibiso-reporting-api/    ← FastAPI backend
│   ├── app/
│   │   ├── main.py          ← Point d'entrée API
│   │   ├── auth.py          ← JWT authentification
│   │   └── users.py         ← Gestion utilisateurs (SQLite)
│   ├── docker-compose.yml   ← Compose autonome (usage avancé)
│   ├── Dockerfile
│   └── .env.template
├── dibiso-reporting-webapp/ ← React frontend
│   ├── src/App.jsx          ← Composant unique
│   ├── docker-compose.yml   ← Compose autonome (usage avancé)
│   ├── Dockerfile
│   └── .env.template
├── dibisoreporting/         ← Bibliothèque Python locale
└── dibisoplot/              ← Bibliothèque Python locale
```

---

## 2. Déploiement Docker (recommandé)

### 2.1 Configurer

```bash
# Depuis la racine du dépôt
cp .env.template .env
```

Variables obligatoires à remplir dans `.env` :

```dotenv
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<mot_de_passe>
SECRET_KEY=<générer avec: python -c "import secrets; print(secrets.token_hex(64))">

# URL de l'API telle qu'elle est accessible depuis le navigateur
VITE_API_URL=http://127.0.0.1:8000

# ScanR
SCANR_API_PASSWORD=<mot_de_passe>
SCANR_API_URL=cluster-production.elasticsearch.dataesr.ovh
SCANR_API_USERNAME=paris-saclay
SCANR_BSO_INDEX=bso-publications
SCANR_PUBLICATIONS_INDEX=scanr-publications

# OpenAlex
OPENALEX_API_KEY=<clé_api>
OPENALEX_EMAIL=<email>
```

Les autres variables ont des valeurs par défaut adaptées à un déploiement local.
Si le frontend et l'API sont exposés sur des ports ou domaines différents, ajuster
`API_PORT`, `WEBAPP_PORT` et `CORS_ALLOW_ORIGINS` en conséquence.

### 2.2 Démarrer les services

```bash
# Depuis la racine du dépôt
docker compose up -d --build
```

Les deux services démarrent ensemble. Le frontend attend que le healthcheck de l'API
soit passé avant de démarrer.

- Interface : **http://localhost:8080** (ou `WEBAPP_PORT`)
- API : **http://localhost:8000** (ou `API_PORT`)

Au 1er démarrage :
- La base SQLite est créée dans le volume Docker `api_data`
- L'utilisateur admin est créé automatiquement (depuis `ADMIN_USERNAME`/`ADMIN_PASSWORD`)
- Les templates HTML sont lus depuis `./dibiso-html-templates` (monté en lecture seule)

Vérification :

```bash
curl http://localhost:8000/health
# → {"status":"healthy","message":"API is running"}
```

---

## 3. Développement local (Windows, sans Docker)

> Cette section est destinée au développement sous Windows. En production, utiliser Docker (section 2).

### 3.1 Environnement virtuel Python

```bash
# Depuis la racine du projet
python -m venv .venv

# Activation (Windows PowerShell)
.\.venv\Scripts\Activate.ps1
```

### 3.2 Installer les bibliothèques locales

Les bibliothèques locales `dibisoreporting` et `dibisoplot` contiennent des fonctionnalités
non encore publiées sur PyPI. Les installer en mode développement depuis les sources :

```bash
pip install -e dibisoreporting/ -e dibisoplot/
```

> ⚠️ **Ne pas** faire `pip install dibisoreporting` (version PyPI potentiellement obsolète).

### 3.3 Installer les dépendances de l'API

```bash
pip install -r dibiso-reporting-api/requirements.txt
```

### 3.4 Installer les dépendances du frontend

```bash
cd dibiso-reporting-webapp
npm install
cd ..
```

### 3.5 Configuration `.env`

**API** — `dibiso-reporting-api/.env` (copier depuis `.env.template`) :

```dotenv
USERS_DATABASE_NAME=users.db
USERS_DATABASE_DIRECTORY=./api_data

ADMIN_USERNAME=username
ADMIN_PASSWORD=password
SECRET_KEY=<générer avec: python -c "import secrets; print(secrets.token_hex(64))">

# Templates HTML — pointer vers le DOSSIER PARENT de dibiso-html/
HTML_TEMPLATE_PATH=C:/path/to/dibisoreports/dibiso-html-templates
HTML_TEMPLATE_URL=https://github.com/dibiso-upsaclay/dibiso-html-templates/releases/latest

OPENALEX_ANALYSIS_CACHE_PATH=C:/path/to/openalex-analysis/data
DATA_FETCHING_TIMEOUT_SECONDS=1200

SCANR_API_PASSWORD=<mot_de_passe>
SCANR_API_URL=cluster-production.elasticsearch.dataesr.ovh
SCANR_API_USERNAME=paris-saclay
SCANR_BSO_INDEX=bso-publications
SCANR_PUBLICATIONS_INDEX=scanr-publications

OPENALEX_API_KEY=<clé_api>
OPENALEX_EMAIL=<email>

CORS_ALLOW_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=*
CORS_ALLOW_HEADERS=*

THREAD_POOL_MAX_WORKERS=4
ACCESS_TOKEN_EXPIRE_HOURS=48
PROJECTS_PERSISTENCE_TIME_HOURS=4
PROJECTS_ANALYSES_RETENTION_DAYS=30
```

> **Attention aux chemins Windows** : utiliser des slashes (`/`) ou des doubles
> anti-slashes (`\\`). Les anti-slashes simples (`\`) provoquent des erreurs
> `SyntaxError: unicode escape` dans le sous-processus Python.

**Frontend** — `dibiso-reporting-webapp/.env` :

```dotenv
VITE_API_URL=http://127.0.0.1:8000
```

### 3.6 Démarrer les services

```powershell
# API — depuis dibiso-reporting-api/ (important : ne pas lancer depuis la racine)
cd dibiso-reporting-api
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

```bash
# Frontend
cd dibiso-reporting-webapp
npm run dev
```

L'interface est accessible sur **http://localhost:3000**.

---

## 4. Génération d'un rapport BiSO — exemple LGI 2024

### 4.1 Se connecter

Ouvrir l'interface → cliquer **Login** → saisir les identifiants admin.

### 4.2 Remplir le formulaire

| Champ | Valeur (exemple LGI) |
|-------|---------------------|
| Année | 2024 |
| Acronyme | LGI |
| Nom complet | Laboratoire Génie Industriel |
| Collection HAL | LGI |
| Max entités | 500 |

> Le champ **Collection HAL** est l'identifiant utilisé dans l'URL HAL :
> `https://hal.science/search/index/?q=*&collCode_s=LGI`

### 4.3 Déroulement du processus

```
1. Vérification de la collection HAL  (2%)
2. Démarrage du sous-processus         (5%)
3. Récupération des données            (10%)   ← LONG (voir ci-dessous)
   ├── HAL API — publications, revues, conférences
   ├── OpenAlex — analyse bibliométrique, collaborations
   └── ScanR — projets ANR et européens
4. Génération des figures Plotly       (10-70%)
5. Rendu HTML via Jinja2               (72%)
6. Conversion HTML → PDF (WeasyPrint)  (80-88%)
7. Création de l'archive ZIP           (98%)
8. Terminé                            (100%)
```

### 4.4 Durée estimée

| Situation | Durée approximative |
|-----------|-------------------|
| 1ère exécution (aucun cache OpenAlex) | ~5 min pour LGI/2024 (169 pubs) |
| Exécutions suivantes (cache OpenAlex) | ~2–3 min |
| Labo avec > 500 publications | 15–40 min (1ère exécution) |

### 4.5 Télécharger les résultats

Après complétion :
- **Download PDF** — rapport principal
- **Download Biblio PDF** — bibliographie
- **Download ZIP** — projet complet (figures SVG + HTML rendu + données)

### 4.6 Éditer le rapport (facultatif)

Cliquer **Edit Report** pour accéder à l'éditeur Markdown :
- Chaque section affiche la figure correspondante
- Les analyses textuelles sont sauvegardées automatiquement
- Cliquer **Export PDF & HTML** pour régénérer les PDFs avec les analyses

---

## 5. Bugs Windows corrigés lors de la mise en place

Les bugs suivants ont été identifiés et corrigés pour faire fonctionner l'application
en développement local sous Windows. Ils ne se produisent pas en production Docker.

### Bug 1 — Chemins Linux dans `.env` (erreur au démarrage)

**Symptôme** : `sqlite3.OperationalError: unable to open database file`

**Cause** : `USERS_DATABASE_DIRECTORY=/api_data` est un chemin absolu Linux invalide sous Windows.

**Correction** :
```dotenv
USERS_DATABASE_DIRECTORY=./api_data
OPENALEX_ANALYSIS_CACHE_PATH=C:/Users/<username>/AppData/Local/Temp/openalex-analysis-cache
```

### Bug 2 — Anti-slashes Windows dans le sous-processus Python

**Symptôme** :
```
SyntaxError: (unicode error) 'unicodeescape' codec can't decode bytes
in position 2-3: truncated \UXXXXXXXX escape
```

**Cause** : Le chemin du répertoire de travail (ex: `C:\Users\<username>\...`) est
injecté via f-string dans du code Python sans échappement. Python interprète `\U`
comme une séquence Unicode.

**Correction** dans `app/main.py` — utiliser `json.dumps()` pour échapper les chemins :
```python
import json as _json
_cwd = _json.dumps(os.getcwd())
_project_dir = _json.dumps(str(project_dir))
```

### Bug 3 — Version PyPI de `dibisoreporting` obsolète

**Symptôme** :
```
TypeError: Biso.__init__() got an unexpected keyword argument 'html_template_url'
AttributeError: type object 'DibisoReporting' has no attribute 'render_from_saved'
```

**Correction** :
```bash
pip install -e dibisoreporting/ -e dibisoplot/
```

### Bug 4 — Kaleido 0.2.1 bloque sous Windows

**Symptôme** : Le sous-processus se bloque indéfiniment après la récupération des données.

**Cause** : `kaleido 0.2.1` utilise un sous-processus Node.js qui bloque définitivement sur Windows.

**Correction** :
```bash
pip install "kaleido>=1.0.0"
```

> Note : `openalex-analysis` déclare `kaleido<1.0` comme dépendance mais ne l'utilise
> pas activement ici. Le conflit peut être ignoré.

### Bug 5 — Timeout trop court pour la récupération des données

**Symptôme** : `Process timeout - data fetching took too long` après 5 minutes.

**Correction** dans `.env` :
```dotenv
DATA_FETCHING_TIMEOUT_SECONDS=1200
```

### Bug 6 — Dossier `.git` inclus dans le ZIP généré

**Symptôme** : Le ZIP contient des fichiers `.git/...` du template HTML.

**Correction** dans `dibisoreporting/dibisoreporting/dibisoreporting.py` :
```python
_skip = {".git", ".hg", ".svn", "__pycache__"}
for item in os.listdir(self.html_template_path):
    if item in _skip:
        continue
```

### Limitation — PDF non disponible sous Windows (GTK manquant)

**Symptôme** : `status=partial`. Pas de bouton "Download PDF".

**Cause** : WeasyPrint nécessite les bibliothèques GTK3 non disponibles sur Windows par défaut.

**En développement Windows** : le statut `partial` est attendu. Télécharger le ZIP
et ouvrir `report.html` dans un navigateur.

**Pour activer le PDF sur Windows** :
```powershell
# Via Chocolatey (nécessite droits admin)
choco install gtk-runtime -y
# Puis ajouter C:\Program Files\GTK3-Runtime Win64\bin\ au PATH
```

---

## 6. Architecture du flux de génération

```
Utilisateur (navigateur)
    │  POST /generate-report
    ▼
FastAPI (app/main.py)
    │  asyncio.create_task → ThreadPoolExecutor
    ▼
run_compilation()
    ├── Vérification HAL (requests)
    └── generate_report_project()
            │  subprocess.Popen(python -c "...")
            ▼
        Sous-processus isolé :
            ├── openalex_analysis_config
            ├── Biso("LGI", 2024, ...)
            └── biso.generate_report()
                    ├── WorksType   → HAL API
                    ├── Journals    → HAL + BSO (ScanR)
                    ├── CollaborationMap → OpenAlex
                    ├── AnrProjects → ScanR
                    └── ... (12 visualisations)
            ▼
        Répertoire temporaire :
            ├── figures/           ← SVG Plotly
            ├── report.html        ← Jinja2 rendu
            ├── biblio.html
            ├── figures.json
            └── context.json
    ▼
render_html_to_pdf() → WeasyPrint → report.pdf + biblio.pdf
    ▼
create_zip_archive() → project.zip
    ▼
GET /download-pdf  (authentifié)
GET /download-zip  (authentifié)
```
