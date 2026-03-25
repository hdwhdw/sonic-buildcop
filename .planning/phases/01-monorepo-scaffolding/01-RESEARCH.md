# Phase 1: Monorepo Scaffolding - Research

**Researched:** 2026-03-25
**Domain:** Python monorepo scaffolding with uv workspaces, hatchling build backend, src-layout packaging
**Confidence:** HIGH

## Summary

Phase 1 converts a flat single-tool repository into a uv workspace monorepo with two packages: a minimal `core` skeleton and the existing `submodule-status` tool restructured into proper Python packaging. This is a purely structural phase — no business logic changes, no new dependencies beyond what already exists, no API client wiring. The core package is an empty shell with just `__version__`; real code arrives in Phases 2-3.

The main technical challenge is the atomic migration of existing code into src-layout while simultaneously updating all import paths in both source and test files, removing `sys.path.insert` hacks, and updating `@patch` decorator target strings. The template path resolution in `renderer.py` must also change because `templates/` moves from being a sibling of `scripts/` to being inside the package directory.

**Primary recommendation:** Execute the directory restructure, import rewrite, and sys.path removal as a single atomic operation. Never have a transitional state where both old and new import paths work simultaneously — that causes dual-import bugs (Pitfall #8 from research).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Core Python import name: `sonic_buildcop_core`
- Submodule-status Python import name: `sonic_submodule_status`
- Top-level directory names: `core/` and `submodule-status/` (unchanged from current dir name)
- Use uv workspaces with `[tool.uv.workspace]` in root `pyproject.toml`
- Both packages use src-layout (PyPA standard, hatchling default)
- Core layout: `core/src/sonic_buildcop_core/__init__.py`
- Submodule-status layout: `submodule-status/src/sonic_submodule_status/`
- Move `submodule-status/scripts/*.py` (collector, staleness, enrichment, renderer) into `submodule-status/src/sonic_submodule_status/` as flat modules
- Move `submodule-status/templates/` into `submodule-status/src/sonic_submodule_status/templates/` (included in package via `__file__`)
- Tests stay at `submodule-status/tests/` (standard pytest layout, outside src/)
- Existing `submodule-status/requirements.txt` replaced by `pyproject.toml` dependencies
- Core skeleton: just `__init__.py` with a `__version__` string — no placeholder modules
- Console script entry points: `collect-submodules` → `sonic_submodule_status.collector:main`, `render-dashboard` → `sonic_submodule_status.renderer:main`
- Build backend: hatchling (uv default, handles src-layout natively)
- All existing tests must pass after scaffolding — import paths updated accordingly
- The `sys.path.insert` hack in `conftest.py` (and `test_renderer.py`) will be replaced by proper package imports

### Claude's Discretion
- Exact `pyproject.toml` field values (project metadata, classifiers, etc.)
- Whether to include a `py.typed` marker for type-checking support
- `uv.lock` inclusion/exclusion in `.gitignore`

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PKG-01 | Monorepo uses uv workspaces with root `pyproject.toml` and per-package `pyproject.toml` files | Root workspace config pattern documented in Architecture Patterns; `[tool.uv.workspace]` with `members = ["core", "submodule-status"]` |
| PKG-02 | Core package (`sonic-buildcop-core`) installable with `uv pip install -e ./core` | Core pyproject.toml with hatchling build backend + src-layout documented; minimal `__init__.py` with `__version__` |
| PKG-03 | Submodule-status package depends on core, uses src-layout | Deliverable pyproject.toml with `[tool.uv.sources]` workspace reference + `[project.scripts]` entry points |
</phase_requirements>

## Standard Stack

### Core (Phase 1 only — scaffolding tools)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| uv | ≥0.7 (locally 0.7.20) | Package/project manager with workspace support | Native workspace support, single lockfile, editable installs by default |
| hatchling | ≥1.27 | Build backend for both packages | Zero-config src-layout support, uv default, lightweight |
| Python | ≥3.12 | Runtime | Already the project target |

### Supporting (existing deps migrated to pyproject.toml)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| jinja2 | ≥3.1 | HTML template rendering | Submodule-status dependency (existing) |
| requests | ≥2.31 | HTTP client | Submodule-status dependency (existing) |
| pytest | ≥8.0 | Test runner | Dev dependency for test suite |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| hatchling | setuptools | More config needed, heavier — hatchling is simpler for pure-Python src-layout |
| uv workspaces | Poetry workspaces | Slower, weaker workspace support, Poetry-specific lockfile |

**Installation (after scaffolding):**
```bash
# From repo root
uv sync
```

## Architecture Patterns

### Target Project Structure
```
sonic-buildcop/
├── pyproject.toml                              # Workspace root (virtual, non-installable)
├── uv.lock                                     # Auto-generated lockfile
├── .python-version                             # Pin to 3.12
│
├── core/                                       # Shared core package
│   ├── pyproject.toml                          # name = "sonic-buildcop-core"
│   └── src/
│       └── sonic_buildcop_core/
│           └── __init__.py                     # Just __version__ = "0.1.0"
│
├── submodule-status/                           # Deliverable package
│   ├── pyproject.toml                          # name = "sonic-submodule-status", depends on sonic-buildcop-core
│   ├── src/
│   │   └── sonic_submodule_status/
│   │       ├── __init__.py
│   │       ├── collector.py                    # Was scripts/collector.py
│   │       ├── staleness.py                    # Was scripts/staleness.py
│   │       ├── enrichment.py                   # Was scripts/enrichment.py
│   │       ├── renderer.py                     # Was scripts/renderer.py
│   │       └── templates/
│   │           └── dashboard.html              # Was templates/dashboard.html
│   └── tests/
│       ├── conftest.py                         # NO sys.path hack — proper imports
│       ├── test_collector.py
│       ├── test_staleness.py
│       ├── test_enrichment.py
│       └── test_renderer.py
│
├── .github/
│   └── workflows/
│       └── update-dashboard.yml                # Updated for uv workspace
│
├── .gitignore                                  # Updated for uv artifacts
├── LICENSE
└── README.md
```

### Pattern 1: Root Workspace pyproject.toml
**What:** The root `pyproject.toml` is a virtual (non-installable) project that declares workspace members and shared dev dependencies.
**When to use:** Always — this is the workspace entry point.
**Example:**
```toml
[project]
name = "sonic-buildcop"
version = "0.1.0"
description = "SONiC build infrastructure tools"
requires-python = ">=3.12"

[tool.uv.workspace]
members = [
    "core",
    "submodule-status",
]

[dependency-groups]
dev = [
    "sonic-buildcop-core",
    "sonic-submodule-status",
    "pytest>=8.0",
]

[tool.uv.sources]
sonic-buildcop-core = { workspace = true }
sonic-submodule-status = { workspace = true }
```

### Pattern 2: Core Package pyproject.toml (Minimal Skeleton)
**What:** The core package is installable but empty for Phase 1 — just proves the workspace wiring works.
**Example:**
```toml
[project]
name = "sonic-buildcop-core"
version = "0.1.0"
description = "Shared core package for SONiC build infrastructure tools"
requires-python = ">=3.12"
dependencies = []

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### Pattern 3: Deliverable Package pyproject.toml
**What:** Submodule-status depends on core and declares console script entry points.
**Example:**
```toml
[project]
name = "sonic-submodule-status"
version = "0.1.0"
description = "Submodule staleness monitoring dashboard for SONiC"
requires-python = ">=3.12"
dependencies = [
    "sonic-buildcop-core",
    "jinja2>=3.1",
    "requests>=2.31",
]

[project.scripts]
collect-submodules = "sonic_submodule_status.collector:main"
render-dashboard = "sonic_submodule_status.renderer:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv.sources]
sonic-buildcop-core = { workspace = true }
```

### Pattern 4: Import Path Migration (Source Files)
**What:** All inter-module imports change from bare module names to fully qualified package paths.
**Example — collector.py:**
```python
# BEFORE (scripts/collector.py):
from staleness import enrich_with_staleness
from enrichment import enrich_with_details

# AFTER (src/sonic_submodule_status/collector.py):
from sonic_submodule_status.staleness import enrich_with_staleness
from sonic_submodule_status.enrichment import enrich_with_details
```

### Pattern 5: Import Path Migration (Test Files)
**What:** Tests remove sys.path hacks and use package imports. All @patch target strings must be updated.
**Example — test_collector.py:**
```python
# BEFORE:
from collector import parse_gitmodules, get_pinned_sha, ...
@patch("collector.time.sleep")

# AFTER:
from sonic_submodule_status.collector import parse_gitmodules, get_pinned_sha, ...
@patch("sonic_submodule_status.collector.time.sleep")
```

### Pattern 6: Template Path Resolution Fix
**What:** The template directory moves from a sibling of `scripts/` to inside the package directory, changing the relative path.
**Example — renderer.py:**
```python
# BEFORE (template_dir was ../templates relative to scripts/):
template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")

# AFTER (templates/ is now a subdirectory of the package):
template_dir = os.path.join(os.path.dirname(__file__), "templates")
```

### Anti-Patterns to Avoid
- **Transitional sys.path coexistence:** Never keep `sys.path.insert` alongside proper package imports — causes dual-import bugs where mocks don't apply
- **Partial import rewrite:** Don't update source imports without also updating test `@patch` strings in the same commit
- **Flat-layout packaging:** Don't use flat layout (no `src/` dir) — src-layout prevents accidental local imports from non-installed source

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Workspace dependency resolution | Custom pip install scripts | `uv sync` with `[tool.uv.workspace]` | uv handles editable installs, version resolution, single lockfile automatically |
| Build backend config for src-layout | Manual MANIFEST.in, setup.py | hatchling with default src-layout detection | hatchling auto-detects `src/` layout with zero config |
| Entry point creation | Wrapper shell scripts | `[project.scripts]` in pyproject.toml | Standard Python packaging — creates proper CLI commands on install |
| Test import resolution | `sys.path.insert` hacks | `uv sync` editable install + standard imports | Editable install makes all workspace packages importable natively |

**Key insight:** The entire scaffolding phase is about replacing hand-rolled solutions (sys.path hacks, requirements.txt, working-directory constraints) with standard Python packaging infrastructure.

## Common Pitfalls

### Pitfall 1: Dual Import Paths from sys.path + Package Install
**What goes wrong:** If `sys.path.insert` remains in conftest.py/test_renderer.py alongside the new package install, Python can import the same module via two paths (e.g., `collector` and `sonic_submodule_status.collector`). These are treated as *different modules*, so `@patch("collector.time.sleep")` doesn't affect code running under the package import.
**Why it happens:** Developers add pyproject.toml but forget to remove the sys.path hack, or do it in separate commits.
**How to avoid:** Remove ALL `sys.path.insert` calls in the SAME commit that creates pyproject.toml and updates imports. Never have a transitional state.
**Warning signs:** Tests pass but with warnings about duplicate modules; unpatched `time.sleep` calls make tests slow.

### Pitfall 2: @patch Target Strings Not Updated
**What goes wrong:** `@patch("collector.time.sleep")` silently does nothing because the module is now `sonic_submodule_status.collector`. The test doesn't error — it just runs with the real function.
**Why it happens:** `@patch` target is a plain string, not validated at import time. Wrong path = mock doesn't apply, no error.
**How to avoid:** Grep all `@patch` decorators and update systematically. There are 25+ `@patch` decorators across the test suite (confirmed). After migration, run tests with `--timeout=5` to catch any unpatched `time.sleep`.
**Warning signs:** Tests take much longer than before; tests pass but make real API calls.

### Pitfall 3: Template Path Goes Wrong After Move
**What goes wrong:** `renderer.py` uses `os.path.join(os.path.dirname(__file__), "..", "templates")` to find templates. After moving renderer.py to `src/sonic_submodule_status/renderer.py` and templates to `src/sonic_submodule_status/templates/`, the `..` traversal goes to the wrong directory.
**Why it happens:** The relative path `../templates` was correct when scripts/ and templates/ were siblings. Now templates/ is a child of the package directory.
**How to avoid:** Change to `os.path.join(os.path.dirname(__file__), "templates")` — drop the `..` since templates is now a subdirectory.
**Warning signs:** `FileNotFoundError: [Errno 2] No such file or directory` when rendering dashboard; `TemplateNotFound: dashboard.html`.

### Pitfall 4: conftest.py Not the Only sys.path Hack
**What goes wrong:** CONTEXT.md mentions conftest.py has the sys.path hack, but test_renderer.py ALSO has its own `sys.path.insert` on line 8. If only conftest.py is cleaned, test_renderer.py still creates a dual-import path.
**Why it happens:** test_renderer.py added its own sys.path hack independently (possibly added later).
**How to avoid:** Grep for ALL `sys.path.insert` calls: there are exactly 2 locations confirmed:
  - `submodule-status/tests/conftest.py` line 5
  - `submodule-status/tests/test_renderer.py` lines 7-8
Both must be removed.
**Warning signs:** Same as Pitfall 1.

### Pitfall 5: Working Directory Assumptions in Existing Code
**What goes wrong:** `collector.py` writes `data.json` to CWD with a bare relative path. `renderer.py` reads from `data.json` in CWD. After restructuring, the working directory context may differ.
**Why it happens:** Both `main()` functions use `os.environ.get("DATA_PATH", "data.json")` — they're CWD-dependent. The CI workflow sets `working-directory: submodule-status` to make this work.
**How to avoid:** For Phase 1, the entry points and CI workflow update handle this. The `main()` functions' CWD-relative behavior is acceptable as long as CI sets the right working directory or uses absolute paths via env vars. This is a Phase 4 concern.

## Code Examples

### Complete Import Rewrite Map (Source Files)

```python
# collector.py — line 11-12:
# BEFORE:
from staleness import enrich_with_staleness
from enrichment import enrich_with_details
# AFTER:
from sonic_submodule_status.staleness import enrich_with_staleness
from sonic_submodule_status.enrichment import enrich_with_details
```

Note: `staleness.py` and `enrichment.py` have no cross-module imports — they only use stdlib and `requests`. No import changes needed in those files beyond the package `__init__.py` existing.

### Complete Import Rewrite Map (Test Files)

```python
# conftest.py — REMOVE lines 2-5:
# import sys
# import os
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

# test_collector.py — line 5:
# BEFORE: from collector import (parse_gitmodules, get_pinned_sha, ...)
# AFTER:  from sonic_submodule_status.collector import (parse_gitmodules, get_pinned_sha, ...)

# test_staleness.py — line 7:
# BEFORE: from staleness import (get_bump_dates, compute_cadence, ...)
# AFTER:  from sonic_submodule_status.staleness import (get_bump_dates, compute_cadence, ...)

# test_enrichment.py — line 6:
# BEFORE: from enrichment import (match_pr_to_submodule, ...)
# AFTER:  from sonic_submodule_status.enrichment import (match_pr_to_submodule, ...)

# test_renderer.py — REMOVE lines 5-8, line 10-12:
# REMOVE: import sys, os; sys.path.insert(...)
# BEFORE: from renderer import render_dashboard, sort_submodules, compute_summary
# AFTER:  from sonic_submodule_status.renderer import render_dashboard, sort_submodules, compute_summary
```

### Complete @patch Rewrite Map

All 25+ `@patch` decorators must be updated. Pattern:
```
@patch("MODULE.target") → @patch("sonic_submodule_status.MODULE.target")
```

Affected files and their patch targets:
```
test_collector.py (3 patches):
  @patch("collector.datetime")     → @patch("sonic_submodule_status.collector.datetime")
  @patch("collector.time.sleep")   → @patch("sonic_submodule_status.collector.time.sleep")

test_staleness.py (4 patches, 2 doubled):
  @patch("staleness.time.sleep")       → @patch("sonic_submodule_status.staleness.time.sleep")
  @patch("staleness.get_bump_dates")   → @patch("sonic_submodule_status.staleness.get_bump_dates")

test_enrichment.py (18+ patches):
  @patch("enrichment.time.sleep")                → @patch("sonic_submodule_status.enrichment.time.sleep")
  @patch("enrichment.get_ci_status_for_pr", ...) → @patch("sonic_submodule_status.enrichment.get_ci_status_for_pr", ...)
  @patch("enrichment.compute_avg_delay")         → @patch("sonic_submodule_status.enrichment.compute_avg_delay")
  @patch("enrichment.fetch_latest_repo_commits") → @patch("sonic_submodule_status.enrichment.fetch_latest_repo_commits")
  @patch("enrichment.fetch_merged_bot_prs")      → @patch("sonic_submodule_status.enrichment.fetch_merged_bot_prs")
  @patch("enrichment.fetch_open_bot_prs")        → @patch("sonic_submodule_status.enrichment.fetch_open_bot_prs")
```

### Minimal core/__init__.py

```python
"""Shared core package for SONiC build infrastructure tools."""

__version__ = "0.1.0"
```

### Minimal submodule-status/__init__.py

```python
"""Submodule staleness monitoring dashboard for SONiC."""
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `pip install -r requirements.txt` | `uv sync` with workspace | uv 0.3+ (2024) | Single command installs all workspace packages with lockfile |
| `sys.path.insert` for test imports | Editable install via workspace | Always was wrong — proper fix | Eliminates dual-import bugs, enables proper @patch |
| `setup.py` / `setup.cfg` | `pyproject.toml` with hatchling | PEP 621 (2021), hatchling 1.0+ | Single config file, zero boilerplate for src-layout |
| `python scripts/collector.py` | `uv run collect-submodules` (entry point) | PEP 517/621 | CWD-independent, discoverable, standard |

## Open Questions

1. **Whether to include `py.typed` marker**
   - What we know: A `py.typed` file in the package root enables PEP 561 type-checking support by external consumers
   - What's unclear: Whether any tool will consume core as a typed library in Phase 1
   - Recommendation: Include it — costs nothing, enables mypy in later phases. Create empty `core/src/sonic_buildcop_core/py.typed`

2. **Whether to commit `uv.lock`**
   - What we know: `uv.lock` provides reproducible builds; recommended for applications. Some disagree for libraries.
   - What's unclear: Whether to gitignore it
   - Recommendation: Commit `uv.lock` — this is an application monorepo (CI must be reproducible), not a library published to PyPI. Add `uv.lock` to version control, do NOT gitignore it.

3. **Whether to update the CI workflow in Phase 1**
   - What we know: The workflow currently uses `pip install -r requirements.txt` and `python scripts/collector.py`. After scaffolding, these paths are wrong.
   - What's unclear: CONTEXT.md mentions the workflow but doesn't explicitly include it in Phase 1 scope. ROADMAP says MIG-03 (workflow update) is Phase 4.
   - Recommendation: Do NOT update the CI workflow in Phase 1 — that's Phase 4 (MIG-03). However, the workflow will be broken after Phase 1's restructure. This is acceptable since Phase 1-3 are structural/internal — the workflow should be fixed in Phase 4 as part of migration. Document this as a known temporary breakage.

4. **What to do with the `submodule-status/scripts/` and `submodule-status/requirements.txt` directories after moving**
   - What we know: Code moves from `scripts/` into `src/sonic_submodule_status/`. The old `scripts/` directory and `requirements.txt` become obsolete.
   - Recommendation: Delete `scripts/` directory and `requirements.txt` after moving code. Keep the git history via `git mv` where possible.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest ≥8.0 |
| Config file | None currently — will add `[tool.pytest.ini_options]` in root `pyproject.toml` |
| Quick run command | `uv run pytest submodule-status/tests/ -x` |
| Full suite command | `uv run pytest submodule-status/tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PKG-01 | `uv sync` succeeds from repo root | smoke | `cd <root> && uv sync && echo "PASS"` | ❌ Wave 0 — manual verification |
| PKG-02 | Core package installable and importable | smoke | `uv run python -c "from sonic_buildcop_core import __version__; print(__version__)"` | ❌ Wave 0 |
| PKG-03 | Submodule-status depends on core, uses src-layout | smoke | `uv run python -c "import sonic_submodule_status"` | ❌ Wave 0 |
| PKG-03 | Entry points wired correctly | smoke | `uv run python -c "from sonic_submodule_status.collector import main; from sonic_submodule_status.renderer import main"` | ❌ Wave 0 |
| (implicit) | All existing tests pass with new imports | regression | `uv run pytest submodule-status/tests/ -v` | ✅ (5 existing test files, updated imports) |

### Sampling Rate
- **Per task commit:** `uv run pytest submodule-status/tests/ -x`
- **Per wave merge:** `uv run pytest submodule-status/tests/ -v`
- **Phase gate:** Full suite green + all smoke checks pass before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] Root `pyproject.toml` — workspace configuration (no existing config)
- [ ] `core/pyproject.toml` — core package build configuration
- [ ] `submodule-status/pyproject.toml` — deliverable build configuration
- [ ] `[tool.pytest.ini_options]` — pytest config in root pyproject.toml (optional but useful)
- [ ] Framework install: `uv sync` — creates virtual env and installs all packages

## Sources

### Primary (HIGH confidence)
- Existing codebase analysis — verified all 4 source files, 5 test files, conftest.py, workflow, gitignore
- `.planning/research/ARCHITECTURE.md` — uv workspace patterns, directory layout, pyproject.toml examples
- `.planning/research/PITFALLS.md` — Pitfalls #5 (test import paths), #8 (dual import paths), #10 (CI editable install)
- `.planning/research/STACK.md` — uv 0.11+, hatchling 1.29+, version pinning strategy
- `.planning/codebase/STRUCTURE.md` — current directory layout documentation
- `.planning/codebase/CONCERNS.md` — "No Proper Python Packaging" tech debt section
- `.planning/codebase/CONVENTIONS.md` — import patterns, naming conventions, function design
- Local uv 0.7.20 verified installed and working

### Secondary (MEDIUM confidence)
- `.planning/research/STACK.md` examples for pyproject.toml — verified patterns but naming differs from CONTEXT.md decisions (architecture used `buildcop_core`, context decided `sonic_buildcop_core`)

### Tertiary (LOW confidence)
- None — all findings verified against codebase and research artifacts

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — uv, hatchling, src-layout are well-documented in research artifacts and verified locally
- Architecture: HIGH — directory structure and pyproject.toml patterns confirmed against uv documentation and research
- Pitfalls: HIGH — dual-import and @patch issues verified against actual codebase (confirmed 2 sys.path hacks, 25+ @patch decorators)
- Import migration: HIGH — all import paths audited against actual source files

**Research date:** 2026-03-25
**Valid until:** 2026-04-25 (stable domain — Python packaging conventions change slowly)
