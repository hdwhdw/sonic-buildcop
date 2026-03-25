# Architecture Research

**Domain:** Python monorepo with shared core package — SONiC build infrastructure tools
**Researched:** 2025-06-26
**Confidence:** HIGH (verified with working uv workspace prototype)

## Standard Architecture

### System Overview

```
sonic-buildcop/
┌─────────────────────────────────────────────────────────────────────────┐
│  Workspace Root (pyproject.toml — virtual, non-installable)             │
│  ┌───────────────────────────┐                                          │
│  │   uv.lock (single lockfile │  ← Pins ALL deps for all packages       │
│  │   for entire workspace)    │                                          │
│  └───────────────────────────┘                                          │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                      core/  (installable package)               │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │    │
│  │  │ GitHub   │ │ Azure    │ │ AI       │ │ Config/  │          │    │
│  │  │ Client   │ │ Client   │ │ Client   │ │ Logging  │          │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │    │
│  └──────────────────────────┬──────────────────────────────────────┘    │
│                             │ (dependency)                              │
│  ┌──────────────────────────┴──────────────────────────────────────┐    │
│  │                DELIVERABLES (each an installable package)       │    │
│  │  ┌───────────────────────┐   ┌───────────────────────┐         │    │
│  │  │   submodule-status/   │   │   (future tools)/     │         │    │
│  │  │  collector → staleness│   │   flake-dashboard/    │         │    │
│  │  │  → enrichment → render│   │   test-cop/           │         │    │
│  │  └───────────────────────┘   └───────────────────────┘         │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                .github/workflows/  (CI/CD)                      │    │
│  │  ┌───────────────────┐  ┌───────────────────┐                  │    │
│  │  │ update-dashboard  │  │ (future workflows) │                  │    │
│  │  └───────────────────┘  └───────────────────┘                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **Workspace Root** | Coordinate all packages, define workspace members, hold single lockfile | `pyproject.toml` with `[tool.uv.workspace]`, `uv.lock` |
| **Core Package** | API client wrappers (GitHub, Azure, AI), shared config/constants, logging, retry utilities, common types | Installable Python package via `pyproject.toml` + `hatchling` |
| **Deliverable Packages** | Tool-specific business logic. Depend on core for API plumbing. Each is an independently runnable unit | Installable Python packages, each with own `pyproject.toml` |
| **CI/CD Workflows** | Per-deliverable pipelines. Install workspace, run deliverable-specific scripts | GitHub Actions workflows using `astral-sh/setup-uv` |

## Recommended Project Structure

```
sonic-buildcop/
├── pyproject.toml                          # Workspace root (virtual)
├── uv.lock                                 # Single lockfile for ALL packages
├── .python-version                         # Pin Python version (3.12)
│
├── core/                                   # Shared core package
│   ├── pyproject.toml                      # name = "buildcop-core"
│   └── src/
│       └── buildcop_core/
│           ├── __init__.py
│           ├── github_client.py            # PyGithub wrapper
│           ├── azure_client.py             # Azure DevOps wrapper (stub)
│           ├── ai_client.py                # AI provider interface (stub)
│           ├── config.py                   # Shared constants, env var loading
│           ├── logging.py                  # Structured logging setup
│           ├── retry.py                    # Retry with backoff utility
│           └── types.py                    # Shared TypedDict/dataclass defs
│
├── submodule-status/                       # Deliverable: staleness dashboard
│   ├── pyproject.toml                      # name = "submodule-status", depends on buildcop-core
│   └── src/
│       └── submodule_status/
│           ├── __init__.py
│           ├── collector.py                # Pipeline orchestration
│           ├── staleness.py                # Cadence/threshold classification
│           ├── enrichment.py               # PR/commit enrichment
│           ├── renderer.py                 # Jinja2 HTML rendering
│           └── templates/
│               └── dashboard.html          # Jinja2 template (inside package)
│   └── tests/
│       ├── conftest.py                     # Fixtures (no more sys.path hacks)
│       ├── test_collector.py
│       ├── test_staleness.py
│       ├── test_enrichment.py
│       └── test_renderer.py
│
├── .github/
│   └── workflows/
│       └── update-dashboard.yml            # Updated for uv workspace
│
├── .gitignore
├── LICENSE
└── README.md
```

### Structure Rationale

- **`core/` at top level:** Direct sibling to deliverables, not nested under `packages/`. Keeps the hierarchy flat — adding a new deliverable = adding a new top-level directory. Matches the mental model of "one shared library + N tools."

- **`src/` layout inside each package:** The Python Packaging Authority (PyPA) recommended layout. Prevents accidental imports from the source directory without installation. Forces proper packaging. The import name (`buildcop_core`, `submodule_status`) uses underscores per Python naming conventions, while the directory name (`core/`, `submodule-status/`) uses hyphens for filesystem readability.

- **Templates inside the Python package:** `submodule_status/templates/dashboard.html` lives inside the `src/` tree, making it accessible via `os.path.dirname(__file__)`. No need for `package_data` or `importlib.resources` — Jinja2's `FileSystemLoader` can reference it relative to the module file, exactly like the current code does.

- **Tests outside `src/`:** Tests are not shipped with the package. They live as siblings to `src/` inside each deliverable. `pytest` discovers them from the repo root via standard discovery. No `sys.path` hacks needed because the workspace installs the package in editable mode.

- **Single `uv.lock` at root:** All packages share one lockfile. This prevents version conflicts between core and deliverables (e.g., core pins `PyGithub==2.6.0`, and every deliverable gets the same version).

## Architectural Patterns

### Pattern 1: uv Workspace with Editable Installs

**What:** A `uv` workspace coordinates multiple Python packages in a single repository. Each package has its own `pyproject.toml`. The root `pyproject.toml` declares workspace members. All packages share a single virtual environment and lockfile.

**When to use:** Any Python monorepo with 2+ packages that share dependencies or depend on each other. This is the modern replacement for `pip install -e .` chains.

**Trade-offs:**
- ✅ Single `uv sync` installs everything, no manual install ordering
- ✅ Single lockfile prevents version drift between packages
- ✅ Workspace-aware resolution means adding a dep to core propagates correctly
- ✅ `uv run --package <name>` isolates execution context
- ⚠️ Requires `uv` (not just `pip`). CI must install `uv` via `astral-sh/setup-uv`
- ⚠️ Contributors must use `uv` locally (not raw `pip install -e .`)

**Root `pyproject.toml` example:**
```toml
[project]
name = "sonic-buildcop"
version = "0.1.0"
description = "SONiC build infrastructure tools"
requires-python = ">=3.12"
dependencies = []

[tool.uv.workspace]
members = [
    "core",
    "submodule-status",
]

[dependency-groups]
dev = [
    "buildcop-core",
    "submodule-status",
    "pytest>=8.0",
    "ruff>=0.8",
]

[tool.uv.sources]
buildcop-core = { workspace = true }
submodule-status = { workspace = true }
```

**Core `pyproject.toml` example:**
```toml
[project]
name = "buildcop-core"
version = "0.1.0"
description = "Shared core package for SONiC build infrastructure tools"
requires-python = ">=3.12"
dependencies = [
    "PyGithub>=2.6.0",
    "requests>=2.32.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**Deliverable `pyproject.toml` example:**
```toml
[project]
name = "submodule-status"
version = "0.1.0"
description = "Submodule staleness monitoring dashboard"
requires-python = ">=3.12"
dependencies = [
    "buildcop-core",
    "jinja2>=3.1.0",
]

[project.scripts]
collect-submodules = "submodule_status.collector:main"
render-dashboard = "submodule_status.renderer:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv.sources]
buildcop-core = { workspace = true }
```

### Pattern 2: Core as Thin Client Wrapper

**What:** The core package wraps third-party API clients (PyGithub, azure-devops) behind a simplified interface. Deliverables never import PyGithub directly — they use `buildcop_core.github_client`.

**When to use:** When multiple deliverables need the same API with shared auth, rate limiting, and error handling patterns.

**Trade-offs:**
- ✅ Deliverables don't deal with auth, rate limits, or session management
- ✅ Switching from `requests` to `PyGithub` happens in one place
- ✅ Consistent error handling and retry logic across all tools
- ⚠️ Core must not encode deliverable-specific business logic
- ⚠️ Core's API surface becomes a contract — breaking changes affect all deliverables

**Example — Core's GitHub client:**
```python
# core/src/buildcop_core/github_client.py
from github import Github, Auth

class GitHubClient:
    """Thin wrapper around PyGithub with shared auth and rate-limit awareness."""

    def __init__(self, token: str | None = None):
        token = token or os.environ.get("GITHUB_TOKEN", "")
        self._gh = Github(auth=Auth.Token(token))

    def get_repo(self, owner: str, repo: str):
        return self._gh.get_repo(f"{owner}/{repo}")

    def get_file_content(self, owner: str, repo: str, path: str, ref: str | None = None) -> str:
        repo_obj = self.get_repo(owner, repo)
        content = repo_obj.get_contents(path, ref=ref)
        return content.decoded_content.decode("utf-8")

    @property
    def rate_limit(self):
        return self._gh.get_rate_limit()
```

**Example — Deliverable using core:**
```python
# submodule-status/src/submodule_status/collector.py
from buildcop_core.github_client import GitHubClient
from buildcop_core.config import PARENT_OWNER, PARENT_REPO

def fetch_gitmodules(client: GitHubClient) -> str:
    return client.get_file_content(PARENT_OWNER, PARENT_REPO, ".gitmodules")
```

### Pattern 3: Entry Points for CLI Commands

**What:** Each deliverable registers CLI commands via `[project.scripts]` in its `pyproject.toml`. No more `python scripts/collector.py` — use `uv run collect-submodules` instead.

**When to use:** Always for any script that CI or users invoke directly.

**Trade-offs:**
- ✅ Eliminates working-directory dependency (`python scripts/collector.py` only works from the right CWD)
- ✅ Scripts become proper commands on `$PATH` after install
- ✅ CI workflows become self-documenting (command names describe intent)
- ⚠️ Requires understanding `[project.scripts]` → `module:function` mapping

**Example in pyproject.toml:**
```toml
[project.scripts]
collect-submodules = "submodule_status.collector:main"
render-dashboard = "submodule_status.renderer:main"
```

**CI usage:**
```yaml
- name: Collect submodule data
  run: uv run collect-submodules
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Data Flow

### Current Pipeline (Unchanged)

```
GitHub Actions trigger (cron / push / manual)
    │
    ▼
collector.py:main()
    │
    ├── Fetch .gitmodules from GitHub API ────────────────── [core.github_client]
    ├── parse_gitmodules() ──────────────────────────────── [deliverable logic]
    ├── collect_submodule() × N ─────────────────────────── [core.github_client + core.retry]
    │       └── get_pinned_sha / get_staleness
    │
    ├── enrich_with_staleness(submodules) ───────────────── [deliverable logic + core.github_client]
    │       └── get_bump_dates / compute_cadence / classify
    │
    └── enrich_with_details(submodules) ─────────────────── [deliverable logic + core.github_client]
            └── fetch_open_bot_prs / fetch_merged_bot_prs
            └── fetch_latest_repo_commits / compute_avg_delay
    │
    ▼
data.json (intermediate artifact)
    │
    ▼
renderer.py:main()
    │
    ├── Read data.json ──────────────────────────────────── [stdlib]
    ├── sort_submodules / compute_summary ────────────────── [deliverable logic]
    └── Jinja2 render ──► site/index.html ───────────────── [deliverable logic]
    │
    ▼
GitHub Pages deployment
```

### Dependency Direction (Build Order)

```
buildcop-core           (no internal dependencies — leaf node)
    ▲
    │ depends on
    │
submodule-status        (depends on buildcop-core)
    ▲
    │ depends on
    │
(future deliverables)   (each depends on buildcop-core, NOT on each other)
```

**Critical rule:** Dependencies flow ONE direction: deliverables → core. Core NEVER imports from any deliverable. Deliverables NEVER import from each other. This is a strict DAG.

### What Moves to Core vs Stays in Deliverables

| Current Location | Current Code | After Refactoring | Why |
|---|---|---|---|
| `collector.py` lines 14-16 | `REPO_OWNER`, `PARENT_REPO`, `API_BASE` constants | `buildcop_core.config` | Duplicated in 3 files. Shared constant. |
| `staleness.py` lines 33-35 | `API_BASE`, `PARENT_OWNER`, `PARENT_REPO` | `buildcop_core.config` | Same — deduplicate |
| `enrichment.py` lines 25-27 | `PARENT_OWNER`, `PARENT_REPO`, `API_BASE` | `buildcop_core.config` | Same — deduplicate |
| `collector.py` lines 229-233 | `requests.Session()` setup with auth headers | `buildcop_core.github_client.GitHubClient` | Auth/session is cross-cutting. PyGithub handles this. |
| `collector.py` lines 159-222 | Retry logic in `collect_submodule()` | `buildcop_core.retry` (utility) + deliverable keeps orchestration | Retry is generic. Business logic stays. |
| `collector.py` line 270 | `print()` summary | `buildcop_core.logging` (structured logger) | Logging is cross-cutting |
| All `time.sleep(0.5)` calls | Rate-limit courtesy delays | `buildcop_core.github_client` rate-limit awareness | Rate limiting belongs with the client |
| `collector.py:parse_gitmodules()` | .gitmodules parsing + BOT_MAINTAINED filter | Stays in `submodule_status.collector` | Business logic specific to this deliverable |
| `staleness.py:compute_cadence()` | Median interval computation | Stays in `submodule_status.staleness` | Business logic specific to this deliverable |
| `enrichment.py:match_pr_to_submodule()` | PR title matching | Stays in `submodule_status.enrichment` | Business logic specific to this deliverable |
| `renderer.py` | All rendering logic | Stays in `submodule_status.renderer` | Entirely deliverable-specific |

### Summary Heuristic

> **Core owns the "how" of talking to external APIs. Deliverables own the "what" and "why" of the data they process.**

If you can describe the function without mentioning "submodule" or "staleness" or "dashboard," it probably belongs in core. If the function is meaningless without that domain context, it stays in the deliverable.

## Component Boundaries

### Core Package (`buildcop_core`)

| Module | Responsibility | Public API |
|--------|----------------|------------|
| `github_client.py` | Authenticated GitHub API access via PyGithub. Rate-limit-aware. | `GitHubClient(token?)` with methods for repos, contents, commits, compare, search |
| `azure_client.py` | Azure DevOps API access (stub). | `AzureClient(org, token?)` — interface only for now |
| `ai_client.py` | AI provider abstraction (stub). | `AIClient` protocol/ABC — interface only for now |
| `config.py` | Shared constants + env var loading. | `PARENT_OWNER`, `PARENT_REPO`, `API_BASE`, `load_config()` |
| `logging.py` | Structured logging factory. | `get_logger(name)` returning a configured `logging.Logger` |
| `retry.py` | Generic retry-with-backoff decorator/utility. | `@retry(max_retries, backoff_base, exceptions)` |
| `types.py` | Shared data types used across deliverables. | TypedDict/dataclass for common structures |

### Deliverable: `submodule_status`

| Module | Responsibility | Imports from Core |
|--------|----------------|-------------------|
| `collector.py` | Pipeline orchestration: fetch gitmodules, parse, collect per-submodule, coordinate enrichment, write data.json | `GitHubClient`, `config`, `logging`, `retry` |
| `staleness.py` | Cadence computation, threshold derivation, green/yellow/red classification | `GitHubClient`, `config`, `logging` |
| `enrichment.py` | Bot PR matching, CI status, latest commits, avg delay computation | `GitHubClient`, `config`, `logging` |
| `renderer.py` | Jinja2 HTML rendering, sorting, summary stats | `logging` only (no API calls) |

## CI/CD Architecture

### Current Workflow

```yaml
# .github/workflows/update-dashboard.yml (CURRENT)
jobs:
  build-and-deploy:
    defaults:
      run:
        working-directory: submodule-status    # ← CWD hack
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -r requirements.txt   # ← Unpinned deps
      - run: python scripts/collector.py       # ← Bare script invocation
      - run: python scripts/renderer.py        # ← Bare script invocation
      - uses: actions/deploy-pages@v4
```

### Target Workflow

```yaml
# .github/workflows/update-dashboard.yml (TARGET)
jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up uv
        uses: astral-sh/setup-uv@v4
        with:
          version: ">=0.7"

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install workspace
        run: uv sync                            # ← Single command installs everything

      - name: Collect submodule data
        run: uv run collect-submodules          # ← Entry point, no CWD dependency
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Render dashboard
        run: uv run render-dashboard            # ← Entry point

      - name: Configure Pages
        uses: actions/configure-pages@v5

      - name: Upload Pages artifact
        uses: actions/upload-pages-artifact@v4
        with:
          path: submodule-status/site           # May need adjustment for output path

      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

### Key CI/CD Changes

| Aspect | Current | Target |
|--------|---------|--------|
| Python installer | `pip install -r requirements.txt` | `uv sync` (workspace-aware) |
| Dependency locking | None (unpinned requirements.txt) | `uv.lock` committed to repo |
| Script invocation | `python scripts/collector.py` | `uv run collect-submodules` |
| Working directory | `defaults.run.working-directory: submodule-status` | Not needed — entry points are CWD-agnostic |
| uv installation | N/A | `astral-sh/setup-uv@v4` action |
| Test execution | `python -m pytest submodule-status/tests/` (with sys.path hacks) | `uv run pytest submodule-status/tests/` |
| Adding a new deliverable | New workflow from scratch | New workflow, same `uv sync` pattern |

### Future: Path-Filtered Workflows

When multiple deliverables exist, each can have a dedicated workflow with path filters to avoid unnecessary runs:

```yaml
# .github/workflows/submodule-status.yml
on:
  push:
    branches: [main]
    paths:
      - 'core/**'                    # Rebuild if core changes
      - 'submodule-status/**'        # Rebuild if deliverable changes
      - 'uv.lock'                    # Rebuild if dependencies change
  schedule:
    - cron: '0 */4 * * *'
```

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 1 deliverable (now) | Single workflow, single lockfile, simple structure |
| 2-5 deliverables | Per-deliverable workflow files with path filters. Core changes trigger all workflows. |
| 5+ deliverables | Consider matrix builds in CI. May need to version core independently. |

### Scaling Priorities

1. **First concern: Core API surface stability.** As more deliverables depend on core, breaking changes in core require updating all consumers. Use semantic versioning on core even within the monorepo.
2. **Second concern: CI run time.** `uv sync` installs all packages. For large workspaces, use `uv sync --package submodule-status` to install only one deliverable and its transitive deps.

## Anti-Patterns

### Anti-Pattern 1: Deliverable-to-Deliverable Imports

**What people do:** `from submodule_status.staleness import compute_cadence` inside a different deliverable.
**Why it's wrong:** Creates coupling between deliverables. Cannot build/test one without the other. Prevents independent development.
**Do this instead:** If two deliverables need the same logic, extract it into core. Deliverables only import from `buildcop_core`.

### Anti-Pattern 2: Business Logic in Core

**What people do:** Put `BOT_MAINTAINED` set, `parse_gitmodules()`, or staleness classification in core.
**Why it's wrong:** Core becomes a dumping ground. It grows to contain the entire codebase, defeating the purpose of the split.
**Do this instead:** Core provides generic capabilities (GitHub client, retry, logging). Deliverables contain all domain-specific logic.

### Anti-Pattern 3: Multiple Virtual Environments

**What people do:** Create a separate venv per deliverable (`submodule-status/.venv`, `flake-dashboard/.venv`).
**Why it's wrong:** Version drift between venvs. Can't share core via editable install across multiple venvs cleanly. Wastes disk and CI time.
**Do this instead:** Single workspace venv at root (`.venv/`). `uv sync` manages it. All packages share one environment.

### Anti-Pattern 4: Keeping `sys.path` Hacks

**What people do:** Keep `sys.path.insert(0, ...)` in test conftest after migration, "just in case."
**Why it's wrong:** Masks packaging errors. Tests pass locally but imports break when the package is actually installed.
**Do this instead:** Remove all `sys.path` manipulation. If imports fail, the packaging is wrong — fix `pyproject.toml`, not `sys.path`.

### Anti-Pattern 5: Running Scripts as Files Instead of Modules

**What people do:** `python submodule-status/src/submodule_status/collector.py` from CI.
**Why it's wrong:** Bypasses the package installation. Relative imports break. Templates can't be found.
**Do this instead:** Use `uv run collect-submodules` (entry point) or `uv run python -m submodule_status.collector` (module invocation).

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| GitHub REST API | `buildcop_core.github_client` via PyGithub | Rate-limit-aware. Token from `GITHUB_TOKEN` env var |
| Azure DevOps API | `buildcop_core.azure_client` via azure-devops-python-api | Stub for now. Token from `AZURE_TOKEN` env var |
| GitHub Pages | Static file deployment via GitHub Actions | Output path for `upload-pages-artifact` must point to deliverable's `site/` dir |
| GitHub Actions | `astral-sh/setup-uv@v4` for tooling, `actions/setup-python@v5` for runtime | `uv sync` replaces `pip install -r requirements.txt` |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Core ↔ Deliverable | Python import (`from buildcop_core import ...`) | Deliverable declares `buildcop-core` as dependency in `pyproject.toml` |
| Deliverable ↔ Deliverable | **None** — completely isolated | If shared logic needed, extract to core |
| Collector ↔ Renderer | `data.json` file on disk | Unchanged from current architecture. Collector writes, renderer reads. |
| Workflow ↔ Packages | Entry point commands (`uv run collect-submodules`) | Registered in `[project.scripts]` |

## Migration Path: Key Steps

The refactoring is ordered to maintain backward compatibility at each step:

1. **Initialize workspace root** — Add root `pyproject.toml` with `[tool.uv.workspace]`
2. **Create core package skeleton** — `core/pyproject.toml` + `core/src/buildcop_core/__init__.py`
3. **Extract shared constants** — Move `API_BASE`, `PARENT_OWNER`, `PARENT_REPO` to `buildcop_core.config`
4. **Extract retry utility** — Move retry logic from `collector.py` to `buildcop_core.retry`
5. **Add structured logging** — Create `buildcop_core.logging`, replace `print()` calls
6. **Package submodule-status** — Add `pyproject.toml`, move `scripts/*.py` to `src/submodule_status/`, move templates inside package
7. **Update imports** — Change `from staleness import ...` to `from submodule_status.staleness import ...`
8. **Remove sys.path hacks** — Delete `sys.path.insert` from conftest, verify tests pass with `uv run pytest`
9. **Update CI workflow** — Switch to `uv sync` + entry points
10. **Introduce PyGithub** — Replace `requests.Session` calls with `buildcop_core.github_client` (this is the biggest change, can be phase 2)

**Build order for CI:** `uv sync` handles this automatically — it resolves the dependency graph and installs core before deliverables.

## Sources

- uv workspace support: Verified via working prototype (uv 0.7.20, created and tested workspace with editable cross-package imports)
- Python Packaging Authority src-layout recommendation: PyPA packaging guide (packaging.python.org)
- hatchling build backend: Default for `uv init --package`, used by major Python projects
- `astral-sh/setup-uv` GitHub Action: Official Astral action for CI
- Current codebase analysis: All findings from `.planning/codebase/ARCHITECTURE.md`, `STRUCTURE.md`, `CONCERNS.md`

---
*Architecture research for: Python monorepo with shared core package — sonic-buildcop*
*Researched: 2025-06-26*
