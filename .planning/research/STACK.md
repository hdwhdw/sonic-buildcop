# Technology Stack

**Project:** sonic-buildcop (monorepo refactoring)
**Researched:** 2026-03-25

## Recommended Stack

### Core Framework

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Python | 3.12+ | Runtime | Already the target. Uses 3.12 syntax (`X \| None`, `str.removesuffix`). No reason to change. | HIGH |
| uv | ≥0.11 | Package/project manager | Replaces pip. Native workspace support for monorepos, lockfile generation (`uv.lock`), 10-100× faster installs, `uv run` for script execution. The 2025/2026 standard for Python project management. | HIGH |
| hatchling | ≥1.29 | Build backend | Lightweight, zero-config for src-layout packages. Used in `pyproject.toml` `[build-system]`. No runtime dependency — build-time only. Simpler than setuptools for pure-Python packages. | HIGH |

### GitHub API Client

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| PyGithub | ≥2.9.0 | GitHub REST API client | **The clear winner.** 7.7k stars, actively maintained (2.9.0 released 2026-03-22), typed return objects, built-in retry (`GithubRetry` with 10 retries default), built-in rate limiting (`seconds_between_requests=0.25`), automatic pagination via `PaginatedList`, and 1:1 mapping to every REST endpoint the project currently uses via raw `requests`. Replaces ~100 lines of manual session/auth/retry code. | HIGH |

### Azure DevOps Client

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| azure-devops | ≥7.1.0b4 | Azure Pipelines interaction | **The only real option**, despite caveats. Official Microsoft client. Provides typed `BuildClient` and `PipelinesClient` with methods for builds, runs, logs, artifacts. Covers the future deliverable needs (CI status, build health). | MEDIUM |

### Templating

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Jinja2 | ≥3.1.6 | HTML dashboard rendering | Already in use. No reason to change — it's the standard for Python HTML templating. Pin the version. | HIGH |

### Logging

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| structlog | ≥25.5.0 | Structured logging | Replaces bare `print()` calls. Stdlib `logging` integration built-in. Processor pipeline (add timestamps, log levels, context). `ConsoleRenderer` for human-readable CI output, `JSONRenderer` for machine parsing. Zero-config for simple cases, composable for complex ones. | HIGH |

### Testing

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| pytest | ≥9.0 | Test runner | Already in use. Pin version. | HIGH |
| pytest-cov | ≥7.1 | Coverage reporting | Adds `--cov` flag to pytest. Needed to track coverage during migration. | HIGH |
| pytest-mock | ≥3.15 | Mock helper | Cleaner `mocker` fixture vs raw `unittest.mock`. Simplifies the extensive mocking already in tests. | HIGH |
| responses | ≥0.26 | HTTP mock library | Mock `requests` calls for testing PyGithub's underlying HTTP. Works with `requests.Session` which PyGithub uses internally. Better than raw `unittest.mock` for HTTP testing. | MEDIUM |

### Dev Tools

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| ruff | ≥0.15.7 | Linter + formatter | Replaces flake8 + black + isort in a single tool. 10-100× faster. Actively maintained (weekly releases). The 2025/2026 standard. | HIGH |
| mypy | ≥1.19 | Type checker | Catches the key issue in CONCERNS.md: dict key typos, missing fields. PyGithub returns typed objects, so mypy can validate the migration. Strict mode for core package, basic for deliverables. | HIGH |

### Infrastructure

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| GitHub Actions | N/A | CI/CD | Already in use. Workflow needs path updates for monorepo structure. | HIGH |
| GitHub Pages | N/A | Static hosting | Already in use. No change needed. | HIGH |

## Stack Decisions with Rationale

### Why PyGithub over alternatives

**PyGithub (RECOMMENDED):**
- **Typed return objects**: `repo.compare()` returns `Comparison` with `.ahead_by`, `.behind_by`, `.commits` — not raw dicts. This directly addresses the "Untyped Dict Structures" concern.
- **Built-in retry**: `GithubRetry(total=10)` handles 403/429/5xx with backoff. Eliminates the project's manual retry loop.
- **Built-in rate limiting**: `seconds_between_requests=0.25` replaces scattered `time.sleep(0.5)` calls. `get_rate_limit()` method for dynamic checking.
- **Automatic pagination**: `PaginatedList` on `get_commits()`, `search_issues()` etc. No manual `?page=` handling.
- **1:1 endpoint coverage**: Every current raw `requests` call maps to a PyGithub method (verified — see Architecture section).
- **Active maintenance**: 2.9.0 released 2026-03-22. 7.7k stars, ~1.9k forks.
- **Auth**: `Auth.Token(os.environ["GITHUB_TOKEN"])` — clean, explicit, no empty-string footgun.

**github3.py (REJECTED):**
- Last release: 4.0.1 on 2023-04-26 — **3 years stale**. No type annotations.
- 1.2k stars, declining activity. Missing `check_runs` support.
- Would require writing our own retry/rate-limit logic.

**ghapi (REJECTED):**
- Returns `fastcore.AttrDict` — **no static typing**. Cannot use mypy to catch key typos.
- Dynamic method generation means no IDE autocomplete for method signatures.
- Smaller community (673 stars). fastai-ecosystem dependency (`fastcore`) is unusual for non-ML projects.
- No built-in retry or rate-limit handling.

### Why azure-devops despite caveats

**azure-devops 7.1.0b4 (RECOMMENDED with caution):**
- **Only official client** for Azure DevOps REST API from Microsoft.
- Covers `BuildClient` (59 build-related methods) and `PipelinesClient` (list_runs, get_run, get_log, etc.).
- Typed client methods with model classes.

**Caveats (documented for roadmap):**
- Still in beta (`b4` since 2023-11-20) — no stable release in 2+ years.
- Depends on `msrest` 0.7.1, which is **officially deprecated** (last release 2022-06-13). Microsoft has migrated other Azure SDKs to `azure-core` directly, but hasn't updated `azure-devops`.
- **Mitigation**: For this project, azure-devops is stub/future use only. The core package should define an abstract interface (`AzureDevOpsClient` protocol) and wrap `azure-devops` behind it. If Microsoft eventually ships a new client, we swap the implementation.
- **Alternative if needed**: Raw `requests` + `azure-identity` for auth. The Azure DevOps REST API is straightforward. But this loses typed models.

### Why uv over alternatives

**uv (RECOMMENDED):**
- **Native workspace support**: `[tool.uv.workspace]` with `members = [...]` in root `pyproject.toml`. Each workspace member gets its own `pyproject.toml`. `uv sync` installs all members with proper dependency resolution.
- **Lockfile**: `uv.lock` — deterministic, cross-platform. Solves the "unversioned dependencies" concern directly.
- **Editable installs by default**: Workspace members are installed in editable mode. `from sonic_buildcop_core import github_client` works without `sys.path` hacks.
- **Speed**: 10-100× faster than pip. `uv sync` in CI takes seconds, not minutes.
- **Script execution**: `uv run python scripts/collector.py` — auto-activates venv, installs deps if needed.
- **Active development**: 0.11.1 released 2026-03-24. Astral (makers of ruff) — strong ecosystem credibility.

**Poetry (REJECTED):**
- Monorepo/workspace support is bolted on and poorly documented.
- Slower than uv by 10-50×.
- `poetry.lock` is Poetry-specific; uv's lock format is becoming the standard.
- Poetry's resolver has known issues with complex workspace graphs.

**Hatch (build tool only — NOT as project manager):**
- Hatch-the-CLI competes with uv for project management, but uv is better at workspaces.
- **Hatchling** (the build backend) is excellent and recommended — but use uv to manage the project.
- This is a common and recommended combination: `uv` for project management + `hatchling` for `[build-system]`.

**pip + setuptools (REJECTED):**
- No lockfile. No workspace support. No editable-install-by-default.
- Would require manual `pip install -e ./packages/core` in CI.
- Doesn't solve any of the concerns; perpetuates them.

### Why structlog over stdlib logging

**structlog (RECOMMENDED):**
- **Key-value pairs**: `log.info("submodule_collected", name=name, commits_behind=n)` — structured, greppable, JSON-serializable.
- **Stdlib bridge**: `structlog.stdlib.ProcessorFormatter` wraps stdlib `logging`. Libraries that use stdlib `logging` (like PyGithub) get the same formatting.
- **CI-friendly**: `ConsoleRenderer()` produces colorized, human-readable output. Switch to `JSONRenderer()` for machine parsing with zero code change.
- **Lightweight**: Single dependency, no transitive deps.
- **Migration path**: Replace `print(f"Collected {n} submodules")` with `log.info("collection_complete", count=n)`. Incremental — can convert one module at a time.

**stdlib logging alone (REJECTED as primary):**
- Adequate for simple cases, but verbose configuration.
- No structured key-value pairs without custom formatters.
- No JSON output without third-party formatter.

### Why ruff replaces everything

**ruff (RECOMMENDED — replaces flake8 + black + isort):**
- Single tool for linting AND formatting.
- Configuration in `pyproject.toml` — no extra config files.
- Understands Python 3.12+ syntax natively.
- 0.15.7 released 2026-03-19 — weekly releases.
- Rules: Enable `I` (isort), `E`/`W` (pycodestyle), `F` (pyflakes), `UP` (pyupgrade), `B` (bugbear), `S` (bandit security), `PT` (pytest style).

## Alternatives Considered (Full Matrix)

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| GitHub client | PyGithub 2.9 | github3.py 4.0 | 3 years stale, no types, no retry/rate-limit |
| GitHub client | PyGithub 2.9 | ghapi 1.0 | No static typing (AttrDict), no retry, fastcore dep |
| GitHub client | PyGithub 2.9 | Raw requests | Manual auth/retry/pagination/rate-limit — what we're migrating FROM |
| Azure client | azure-devops 7.1 | Raw requests + azure-identity | Loses typed models; acceptable fallback if needed |
| Package mgr | uv 0.11 | Poetry ≥2.0 | Slower, weaker workspace support |
| Package mgr | uv 0.11 | pip + setuptools | No lockfile, no workspaces |
| Build backend | hatchling 1.29 | setuptools | More config, heavier, less modern |
| Build backend | hatchling 1.29 | flit | Less flexible for monorepo layouts |
| Logging | structlog 25.5 | stdlib logging | Verbose config, no structured output |
| Linter | ruff 0.15 | flake8 + black + isort | Three tools vs one, slower |
| Type checker | mypy 1.19 | pyright/pylance | mypy is better for CI (no node dep), more mature |
| Test mocking | responses 0.26 | respx 0.22 | respx is for httpx, not requests; responses works with requests which PyGithub uses |

## Dependency Inventory (Full)

### Runtime Dependencies (core package)

```
PyGithub ≥2.9.0
├── requests ≥2.14
├── PyJWT ≥2.4
├── PyNaCl ≥1.4
├── typing-extensions ≥4.5
└── urllib3 ≥1.26

azure-devops ≥7.1.0b4
└── msrest ≥0.7.1 (deprecated — see caveats)
    ├── azure-core ≥1.24
    ├── requests-oauthlib ≥0.5
    └── requests ~=2.16

structlog ≥25.5.0
  (no transitive deps)

jinja2 ≥3.1.6
└── MarkupSafe ≥2.0
```

### Dev Dependencies (workspace-level)

```
pytest ≥9.0
pytest-cov ≥7.1
pytest-mock ≥3.15
responses ≥0.26
ruff ≥0.15
mypy ≥1.19
```

## Installation

```bash
# Install uv (if not present)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Initialize workspace and install all deps
uv sync

# Run a deliverable
uv run python -m submodule_status.main

# Run tests
uv run pytest

# Run linter + formatter
uv run ruff check .
uv run ruff format .

# Type check
uv run mypy packages/core/

# Add a new dependency to core
uv add --package sonic-buildcop-core PyGithub
```

## Monorepo pyproject.toml Structure

### Root: `pyproject.toml`

```toml
[project]
name = "sonic-buildcop"
version = "0.1.0"
requires-python = ">=3.12"

[tool.uv.workspace]
members = ["packages/*", "deliverables/*"]

[tool.uv]
dev-dependencies = [
    "pytest>=9.0",
    "pytest-cov>=7.1",
    "pytest-mock>=3.15",
    "responses>=0.26",
    "ruff>=0.15",
    "mypy>=1.19",
]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "W", "F", "I", "UP", "B", "S", "PT"]

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.pytest.ini_options]
testpaths = ["packages", "deliverables"]
addopts = "--cov --cov-report=term-missing"
```

### Core: `packages/core/pyproject.toml`

```toml
[project]
name = "sonic-buildcop-core"
version = "0.1.0"
description = "Shared API clients and utilities for SONiC build infrastructure tools"
requires-python = ">=3.12"
dependencies = [
    "PyGithub>=2.9",
    "azure-devops>=7.1.0b4",
    "structlog>=25.5",
    "jinja2>=3.1",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### Deliverable: `deliverables/submodule-status/pyproject.toml`

```toml
[project]
name = "submodule-status"
version = "0.1.0"
description = "Submodule staleness monitoring dashboard"
requires-python = ">=3.12"
dependencies = [
    "sonic-buildcop-core",
]

[tool.uv.sources]
sonic-buildcop-core = { workspace = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

## Version Pinning Strategy

| Scope | Strategy | Rationale |
|-------|----------|-----------|
| `pyproject.toml` | Minimum compatible (`>=2.9`) | Allows patch updates; broad compatibility |
| `uv.lock` | Exact pins (auto-generated) | Reproducible CI builds; deterministic |
| CI workflow | `uv sync --frozen` | Uses lockfile exactly; fails if lock is stale |

## GitHub Actions CI Update

```yaml
# Key changes for monorepo migration
- name: Install uv
  uses: astral-sh/setup-uv@v5

- name: Install dependencies
  run: uv sync --frozen

- name: Run collector
  run: uv run python -m submodule_status.main
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Sources

| Source | Confidence | What it verified |
|--------|------------|------------------|
| PyPI API (live queries) | HIGH | All version numbers, release dates, dependency trees |
| PyGithub source (installed 2.9.0) | HIGH | API surface, method signatures, retry/rate-limit defaults, Auth classes |
| azure-devops source (installed 7.1.0b4) | HIGH | Client methods, Connection API, msrest dependency |
| ghapi source (installed 1.0.13) | HIGH | AttrDict returns, no typing, dynamic dispatch |
| github3.py source (installed 4.0.1) | HIGH | Limited method set, no check_runs, stale |
| GitHub API (repo stats) | HIGH | Stars, last push dates, archive status |
| uv CLI help (0.11.1) | HIGH | Workspace support, init flags |
| msrest PyPI metadata | HIGH | Deprecation notice confirmed |

---

*Stack research: 2026-03-25*
