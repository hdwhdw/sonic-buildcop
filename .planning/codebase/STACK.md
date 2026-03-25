# Technology Stack

**Analysis Date:** 2025-03-24

## Languages

**Primary:**
- Python 3.12 - All application logic (`submodule-status/scripts/*.py`), tests (`submodule-status/tests/*.py`)

**Secondary:**
- HTML/CSS/JavaScript - Dashboard template (`submodule-status/templates/dashboard.html`)
- YAML - CI/CD workflow (`.github/workflows/update-dashboard.yml`)

## Runtime

**Environment:**
- Python 3.12 (specified in `.github/workflows/update-dashboard.yml` via `actions/setup-python@v5`)
- CPython (standard)

**Package Manager:**
- pip (no pinned versions in `submodule-status/requirements.txt`)
- Lockfile: **missing** — `requirements.txt` lists bare package names without version pins

## Frameworks

**Core:**
- No web framework — this is a CLI data pipeline (scripts run via `python scripts/collector.py` and `python scripts/renderer.py`)

**Templating:**
- Jinja2 (latest) - HTML dashboard rendering (`submodule-status/scripts/renderer.py`)

**Testing:**
- pytest - Test runner and fixtures (`submodule-status/tests/conftest.py`, `submodule-status/tests/test_*.py`)
- unittest.mock (stdlib) - Mocking HTTP responses

**Build/Dev:**
- GitHub Actions - CI/CD pipeline (`.github/workflows/update-dashboard.yml`)
- No local build tool (Makefile, tox, etc.)

## Key Dependencies

**Critical:**
- `requests` (unpinned) - All GitHub API communication. Used via `requests.Session` with auth headers. Every script module imports it.
- `jinja2` (unpinned) - Dashboard HTML rendering from `submodule-status/templates/dashboard.html`

**Standard Library (notable usage):**
- `json` - Data serialization (`data.json` intermediate format)
- `configparser` - `.gitmodules` INI parsing in `submodule-status/scripts/collector.py`
- `statistics` - Median/mean computation in `submodule-status/scripts/staleness.py` and `submodule-status/scripts/enrichment.py`
- `base64` - Decoding GitHub API file content responses
- `datetime` - Timezone-aware timestamp handling throughout
- `time` - Rate-limit courtesy delays (`time.sleep(0.5)`)

**Infrastructure:**
- pytest (dev dependency, not in `submodule-status/requirements.txt`) - Must be installed separately for testing

## Configuration

**Environment:**
- `GITHUB_TOKEN` - GitHub API authentication token (set by GitHub Actions `${{ secrets.GITHUB_TOKEN }}`)
- `DATA_PATH` - Optional override for data.json input path (default: `"data.json"`, used in `submodule-status/scripts/renderer.py`)
- `SITE_DIR` - Optional override for output directory (default: `"site"`, used in `submodule-status/scripts/renderer.py`)

**Build:**
- `.github/workflows/update-dashboard.yml` - Single GitHub Actions workflow
- `submodule-status/requirements.txt` - Python dependency list (2 packages)

**No configuration files for:**
- Linting (no `.flake8`, `pyproject.toml`, `ruff.toml`)
- Formatting (no `.style.yapf`, `black` config)
- Type checking (no `mypy.ini`, `py.typed`)

## Platform Requirements

**Development:**
- Python 3.12+ (uses `str.removesuffix()`, `list[dict]` type hints, `X | None` union syntax)
- pip for dependency installation
- pytest for running tests (install separately: `pip install pytest`)

**Production:**
- GitHub Actions runner (`ubuntu-latest`)
- GitHub Pages for static site hosting
- No server runtime — output is a static HTML file (`site/index.html`)

---

*Stack analysis: 2025-03-24*
