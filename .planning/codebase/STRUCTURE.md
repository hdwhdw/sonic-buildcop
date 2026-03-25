# Codebase Structure

**Analysis Date:** 2026-03-24

## Directory Layout

```
sonic-buildcop/
├── .github/
│   └── workflows/
│       └── update-dashboard.yml   # CI/CD pipeline (scheduled + manual)
├── .planning/
│   └── codebase/                  # GSD planning documents (gitignored)
├── submodule-status/              # Main project directory
│   ├── scripts/                   # Python pipeline scripts
│   │   ├── collector.py           # Stage 1: Data collection + orchestration
│   │   ├── staleness.py           # Stage 2: Cadence-based staleness classification
│   │   ├── enrichment.py          # Stage 3: Detail enrichment (PRs, commits, delay)
│   │   └── renderer.py            # Stage 4: HTML dashboard rendering
│   ├── templates/
│   │   └── dashboard.html         # Jinja2 HTML template (CSS + JS inline)
│   ├── tests/                     # pytest test suite
│   │   ├── conftest.py            # Shared fixtures (sample data, mock responses)
│   │   ├── test_collector.py      # Tests for collector.py
│   │   ├── test_staleness.py      # Tests for staleness.py
│   │   ├── test_enrichment.py     # Tests for enrichment.py
│   │   └── test_renderer.py       # Tests for renderer.py
│   └── requirements.txt           # Python dependencies (jinja2, requests)
├── .gitignore                     # Ignores site/, data.json, __pycache__, .planning/
├── LICENSE                        # MIT License
└── README.md                      # Project overview and links
```

## Directory Purposes

**`submodule-status/`:**
- Purpose: The main (and only) project — a submodule staleness monitoring tool
- Contains: All source code, templates, tests, and dependencies
- Key files: `scripts/collector.py` (orchestrator), `requirements.txt`

**`submodule-status/scripts/`:**
- Purpose: Python modules forming the data pipeline
- Contains: 4 Python files, each representing a pipeline stage
- Key files: `collector.py` (entry point + orchestrator), `staleness.py`, `enrichment.py`, `renderer.py`

**`submodule-status/templates/`:**
- Purpose: Jinja2 HTML templates for dashboard rendering
- Contains: Single `dashboard.html` template with inline CSS and JavaScript
- Key files: `dashboard.html`

**`submodule-status/tests/`:**
- Purpose: pytest test suite with per-module test files and shared fixtures
- Contains: `conftest.py` + 4 test files (one per script module)
- Key files: `conftest.py` (extensive shared fixtures with mock API responses)

**`.github/workflows/`:**
- Purpose: GitHub Actions CI/CD pipeline definition
- Contains: Single workflow file
- Key files: `update-dashboard.yml`

## Key File Locations

**Entry Points:**
- `submodule-status/scripts/collector.py`: Main data collection entry point — run as `python scripts/collector.py`
- `submodule-status/scripts/renderer.py`: Dashboard rendering entry point — run as `python scripts/renderer.py`

**Configuration:**
- `submodule-status/requirements.txt`: Python dependencies (`jinja2`, `requests`)
- `.github/workflows/update-dashboard.yml`: CI/CD pipeline config (cron schedule, deployment)
- `.gitignore`: Ignore patterns for generated output and caches

**Core Logic:**
- `submodule-status/scripts/collector.py`: Orchestrator + `.gitmodules` parsing + GitHub API collection + retry logic
- `submodule-status/scripts/staleness.py`: Cadence computation + threshold derivation + green/yellow/red classification
- `submodule-status/scripts/enrichment.py`: Bot PR fetching + CI status aggregation + avg delay computation
- `submodule-status/scripts/renderer.py`: Sorting + summary + Jinja2 rendering to static HTML

**Testing:**
- `submodule-status/tests/conftest.py`: All shared fixtures — sample `.gitmodules` content, mock API responses, sample submodule dicts
- `submodule-status/tests/test_collector.py`: Tests for parsing, API helpers, retry logic
- `submodule-status/tests/test_staleness.py`: Tests for cadence computation, thresholds, classification
- `submodule-status/tests/test_enrichment.py`: Tests for PR matching, CI status, delay computation
- `submodule-status/tests/test_renderer.py`: Tests for sorting, summary, HTML rendering, relative time

**Generated Artifacts (gitignored):**
- `submodule-status/data.json`: Intermediate pipeline output (collector → renderer)
- `submodule-status/site/index.html`: Final rendered HTML dashboard
- `submodule-status/site/.nojekyll`: GitHub Pages marker file

## Naming Conventions

**Files:**
- Python scripts: `snake_case.py` (e.g., `collector.py`, `staleness.py`, `enrichment.py`, `renderer.py`)
- Test files: `test_<module>.py` matching the module they test (e.g., `test_collector.py` tests `collector.py`)
- Templates: `snake_case.html` (e.g., `dashboard.html`)
- Config: Standard names (`requirements.txt`, `.gitignore`, `LICENSE`)

**Directories:**
- All lowercase, plural for collections: `scripts/`, `templates/`, `tests/`
- Workflow dir follows GitHub convention: `.github/workflows/`

**Functions:**
- `snake_case` throughout (e.g., `parse_gitmodules`, `get_pinned_sha`, `compute_cadence`, `enrich_with_staleness`)
- Getter functions prefixed with `get_` (e.g., `get_pinned_sha`, `get_default_branch`, `get_bump_dates`)
- Enrichment functions prefixed with `enrich_` or `fetch_` (e.g., `enrich_with_staleness`, `fetch_open_bot_prs`)
- Compute functions prefixed with `compute_` (e.g., `compute_cadence`, `compute_thresholds`, `compute_avg_delay`)

**Constants:**
- `UPPER_SNAKE_CASE` (e.g., `BOT_MAINTAINED`, `API_BASE`, `PARENT_REPO`, `MIN_BUMPS_FOR_CADENCE`)

## Where to Add New Code

**New Pipeline Stage (e.g., new enrichment):**
- Create a new module: `submodule-status/scripts/<stage_name>.py`
- Export a main enrichment function: `enrich_with_<feature>(session, submodules)`
- Call it from `submodule-status/scripts/collector.py:main()` after existing enrichment calls
- Add tests: `submodule-status/tests/test_<stage_name>.py`
- Add fixtures to `submodule-status/tests/conftest.py`

**New Dashboard Section (UI change):**
- Modify the Jinja2 template: `submodule-status/templates/dashboard.html`
- Ensure the data is available in `data.json` (add to collection/enrichment if needed)
- Add renderer helpers in `submodule-status/scripts/renderer.py` if needed

**New Monitored Submodule:**
- Add the repo name to `BOT_MAINTAINED` set in `submodule-status/scripts/collector.py` (line ~20)

**New Project (sibling to submodule-status):**
- Create a new top-level directory (e.g., `build-health/`)
- Follow the same pattern: `scripts/`, `templates/`, `tests/`, `requirements.txt`
- Add a new GitHub Actions workflow in `.github/workflows/`
- Update `README.md` project table

**New Test:**
- Add test functions to the existing `submodule-status/tests/test_<module>.py` file
- Add shared mock data/fixtures to `submodule-status/tests/conftest.py`
- Test files import from `scripts/` via `sys.path.insert` in `conftest.py`

**New Python Dependency:**
- Add to `submodule-status/requirements.txt`

## Special Directories

**`site/` (generated at runtime):**
- Purpose: Contains the rendered HTML dashboard output
- Generated: Yes — by `renderer.py`
- Committed: No — listed in `.gitignore`
- Deployed to GitHub Pages by the workflow

**`data.json` (generated at runtime):**
- Purpose: Intermediate JSON data passed from collector to renderer
- Generated: Yes — by `collector.py`
- Committed: No — listed in `.gitignore`

**`.planning/`:**
- Purpose: GSD planning and analysis documents
- Generated: Yes — by GSD workflow commands
- Committed: No — listed in `.gitignore`

---

*Structure analysis: 2026-03-24*
