# Phase 1: Monorepo Scaffolding (REVISED) - Research

**Researched:** 2026-03-25 (revision 2)
**Domain:** Python monorepo packaging — uv workspaces, hatchling flat layout, libs/apps grouping
**Confidence:** HIGH

## Summary

This revised research covers the re-implementation of Phase 1 with a different directory layout and naming convention than the first attempt. The key structural changes are: (1) `libs/` + `apps/` grouping instead of flat top-level dirs, (2) flat layout (no `src/` directories) instead of src-layout, (3) split into `buildcop_common` + `buildcop_github` instead of monolithic `sonic_buildcop_core`, and (4) `submodule_status` import name instead of `sonic_submodule_status`.

All critical technical questions have been verified with working prototypes: `members = ["libs/*", "apps/*"]` works correctly with uv workspaces; hatchling auto-detects flat layout when the normalized project name matches the directory name (works for `buildcop-common` → `buildcop_common/` and `buildcop-github` → `buildcop_github/`); but `buildcop-submodule-status` requires explicit `[tool.hatch.build.targets.wheel] packages = ["submodule_status"]` since the import name doesn't match the PyPI name.

The implementation starts from the `main` branch (original code). 122 tests across 4 test files need import path updates, with 25 `@patch` decorators requiring `submodule_status.` prefix, 2 source-file cross-imports needing updates, the `sys.path` hack in conftest.py and test_renderer.py needing removal, and the renderer's template path needing a one-level change.

**Primary recommendation:** Start from `main` branch, create new branch. Execute as an atomic migration: create directory structure → move files → update all imports/patches → remove sys.path hacks → create pyproject.toml files → `uv sync` → run tests. Never leave the tree in a half-migrated state.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **libs/apps grouping**: `libs/` for shared libraries, `apps/` for deliverables
- **Flat layout** — no `src/` directories (standard for Python monorepos, less nesting)
- Use uv workspaces with `[tool.uv.workspace]` in root `pyproject.toml`
- Workspace members pattern: `members = ["libs/*", "apps/*"]`
- **Common + clients split**: small utilities (config, models, logging) in one `buildcop-common` package; heavy API clients (GitHub, Azure) as separate packages
- `libs/buildcop-common/` → import as `buildcop_common` — skeleton in Phase 1, filled in Phase 2
- `libs/buildcop-github/` → import as `buildcop_github` — skeleton in Phase 1, filled in Phase 3
- Both are empty skeletons with only `__init__.py` to prove workspace wiring
- `apps/submodule-status/` → import as `submodule_status`
- Flat layout: `apps/submodule-status/submodule_status/collector.py`
- Tests inside app dir: `apps/submodule-status/tests/`
- Move `submodule-status/scripts/*.py` (collector, staleness, enrichment, renderer) into `apps/submodule-status/submodule_status/` as flat modules
- Move `submodule-status/templates/` into `apps/submodule-status/submodule_status/templates/`
- Tests stay at `apps/submodule-status/tests/`
- Existing `submodule-status/requirements.txt` replaced by `pyproject.toml` dependencies
- Lib import names: `buildcop_common`, `buildcop_github` (prefix-based, no namespace packages)
- App import name: `submodule_status` (standalone, no prefix)
- PyPI/pip names: `buildcop-common`, `buildcop-github`, `buildcop-submodule-status`
- Console scripts: `collect-submodules` → `submodule_status.collector:main`, `render-dashboard` → `submodule_status.renderer:main`
- hatchling for all packages (handles flat layout with explicit `packages` config)
- All existing tests must pass after scaffolding — import paths updated accordingly
- The `sys.path.insert` hack in `conftest.py` will be replaced by proper package imports

### Claude's Discretion
- Exact `pyproject.toml` field values (project metadata, classifiers, etc.)
- Whether to include a `py.typed` marker for type-checking support
- `uv.lock` inclusion/exclusion in `.gitignore`
- hatchling `[tool.hatch.build.targets.wheel]` config for flat layout

### Deferred Ideas (OUT OF SCOPE)
- Namespace packages (`buildcop.config`, `buildcop.github`) — reconsidered and deferred
- Azure DevOps client stub (`buildcop-azure`) — Phase 5, not scaffolded in Phase 1
- AI provider client stub — Phase 5, not scaffolded in Phase 1
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PKG-01 | Monorepo uses uv workspaces with root `pyproject.toml` and per-package `pyproject.toml` files | Verified: `members = ["libs/*", "apps/*"]` glob pattern works with uv 0.7.20. Root pyproject.toml + 3 member pyproject.toml files needed. |
| PKG-02 | Core/common package installable | Verified: `buildcop-common` and `buildcop-github` as flat-layout packages. Hatchling auto-detects for matching names. Empty skeletons with `__init__.py`. |
| PKG-03 | Submodule-status package depends on common, uses proper packaging | Verified: `buildcop-submodule-status` requires explicit `[tool.hatch.build.targets.wheel] packages = ["submodule_status"]`. Workspace dependency via `[tool.uv.sources]`. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| uv | 0.7.20 (installed) | Workspace management, dependency resolution | Native workspace support with glob patterns; single lockfile |
| hatchling | ≥1.27 (build-time) | Build backend for all packages | Zero-config for matching names, explicit `packages` for mismatches. Lightweight. |
| Python | 3.12 (pinned via `.python-version`) | Runtime | Already the project target |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | ≥8.0 | Test runner | Dev dependency in root pyproject.toml |
| jinja2 | ≥3.1 | Template rendering | Runtime dep for submodule-status only |
| requests | ≥2.31 | HTTP client | Runtime dep for submodule-status only |

**Installation:**
```bash
uv sync   # Installs everything from uv.lock
```

## Architecture Patterns

### Recommended Project Structure (NEW — libs/apps flat layout)
```
sonic-buildcop/
├── pyproject.toml                          # Workspace root (virtual)
├── uv.lock                                 # Single lockfile
├── .python-version                         # 3.12
│
├── libs/
│   ├── buildcop-common/                    # Shared utilities (skeleton)
│   │   ├── pyproject.toml                  # name = "buildcop-common"
│   │   └── buildcop_common/
│   │       └── __init__.py
│   │
│   └── buildcop-github/                    # GitHub client (skeleton)
│       ├── pyproject.toml                  # name = "buildcop-github"
│       └── buildcop_github/
│           └── __init__.py
│
├── apps/
│   └── submodule-status/                   # Existing app migrated here
│       ├── pyproject.toml                  # name = "buildcop-submodule-status"
│       ├── submodule_status/
│       │   ├── __init__.py
│       │   ├── collector.py
│       │   ├── staleness.py
│       │   ├── enrichment.py
│       │   ├── renderer.py
│       │   └── templates/
│       │       └── dashboard.html
│       └── tests/
│           ├── conftest.py
│           ├── test_collector.py
│           ├── test_staleness.py
│           ├── test_enrichment.py
│           └── test_renderer.py
│
├── .github/workflows/
│   └── update-dashboard.yml
├── .gitignore
├── LICENSE
└── README.md
```

### Pattern 1: Hatchling Flat Layout Configuration

**What:** Flat layout means the importable package directory sits directly inside the project root (no `src/` wrapper). Hatchling auto-detects when the normalized project name matches the directory name.

**When explicit config is needed:** When the PyPI name and import name diverge.

**Auto-detect works (no config needed):**
```toml
# libs/buildcop-common/pyproject.toml
# "buildcop-common" normalizes to "buildcop_common" which matches the dir name
[project]
name = "buildcop-common"
version = "0.1.0"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
# No [tool.hatch.build.targets.wheel] needed!
```

**Explicit config required:**
```toml
# apps/submodule-status/pyproject.toml
# "buildcop-submodule-status" normalizes to "buildcop_submodule_status"
# but the dir is "submodule_status" — mismatch!
[project]
name = "buildcop-submodule-status"
version = "0.1.0"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["submodule_status"]
```

**Confidence:** HIGH — verified with actual `uv build` on prototype projects.

### Pattern 2: uv Workspace with Glob Patterns

**What:** Workspace members using `["libs/*", "apps/*"]` glob patterns.

**Verified config:**
```toml
# Root pyproject.toml
[project]
name = "sonic-buildcop"
version = "0.1.0"
requires-python = ">=3.12"

[tool.uv.workspace]
members = ["libs/*", "apps/*"]

[dependency-groups]
dev = [
    "buildcop-common",
    "buildcop-github",
    "buildcop-submodule-status",
    "pytest>=8.0",
]

[tool.uv.sources]
buildcop-common = { workspace = true }
buildcop-github = { workspace = true }
buildcop-submodule-status = { workspace = true }

[tool.pytest.ini_options]
testpaths = ["apps", "libs"]
```

**Confidence:** HIGH — verified: `uv sync` resolves all members, editable installs work, `uv run pytest` passes.

### Anti-Patterns to Avoid
- **Half-migrated state:** Never have both `sys.path` hack and package imports active simultaneously. This creates dual import paths where `@patch` targets silently fail to apply.
- **Running pytest outside `uv run`:** Tests must be run via `uv run pytest` (or from the workspace venv) so installed packages are importable.
- **Forgetting `[tool.hatch.build.targets.wheel]` for submodule-status:** Hatchling will fail at build time with a clear error, but this blocks `uv sync` entirely.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Package discovery in flat layout | Custom `find_packages()` logic | hatchling `packages = [...]` | One line vs brittle auto-discovery |
| Workspace member wiring | Manual `pip install -e` chains | `[tool.uv.workspace]` members | uv resolves deps correctly across members |
| Cross-package dependency | `sys.path.insert` hacks | `[tool.uv.sources]` workspace refs | Proper Python packaging, works in CI too |

## Common Pitfalls

### Pitfall 1: Hatchling Auto-Detect Fails for Mismatched Names
**What goes wrong:** `buildcop-submodule-status` (PyPI name) normalizes to `buildcop_submodule_status` but the import dir is `submodule_status`. Hatchling throws `ValueError: Unable to determine which files to ship inside the wheel`.
**Why it happens:** Hatchling auto-detect only works when normalized project name matches directory name.
**How to avoid:** Add `[tool.hatch.build.targets.wheel] packages = ["submodule_status"]` to `apps/submodule-status/pyproject.toml`. The lib skeletons (`buildcop-common`, `buildcop-github`) DON'T need this since their names match.
**Warning signs:** `uv sync` fails during build with hatchling ValueError.

### Pitfall 2: @patch Target Strings Must Use Full Module Path
**What goes wrong:** After migration, `@patch("collector.time.sleep")` silently doesn't patch because the module is now `submodule_status.collector`, not `collector`. Tests pass but with real `time.sleep` calls (slow tests, not broken tests).
**Why it happens:** `@patch` with string targets doesn't validate at import time. Wrong path = no mock applied.
**How to avoid:** Every `@patch("X.Y")` must become `@patch("submodule_status.X.Y")`. See the complete mapping below.
**Warning signs:** Test suite takes much longer than expected (unpatched sleeps).

### Pitfall 3: sys.path Hack Creates Dual Import Paths (Pitfall #8 from PITFALLS.md)
**What goes wrong:** If `conftest.py` still has `sys.path.insert` AND the package is installed, Python sees two different modules. `@patch` targets don't match.
**Why it happens:** sys.path import (`collector`) and package import (`submodule_status.collector`) resolve the same file but are different module objects.
**How to avoid:** Remove sys.path hack AND update all imports in the same commit. Never have a transitional state.

### Pitfall 4: Renderer Template Path Changes
**What goes wrong:** Current renderer uses `os.path.dirname(__file__), "..", "templates"` (going up from `scripts/` to `submodule-status/`). After move, templates are a sibling inside the package dir.
**Why it happens:** The relative path relationship changes when files move from `scripts/renderer.py` to `submodule_status/renderer.py` and templates move from `templates/` to `submodule_status/templates/`.
**How to avoid:** Change to `os.path.dirname(__file__), "templates"` (one level, not two). Verified: this is exactly what the previous Phase 1 implementation did correctly.

### Pitfall 5: test_renderer.py Has Its Own sys.path Hack
**What goes wrong:** `test_renderer.py` has a SEPARATE `sys.path.insert` at line 8 (not from conftest.py). If only conftest.py is cleaned up, test_renderer.py still has the dual-import problem.
**Why it happens:** test_renderer.py was written independently with its own sys.path fix.
**How to avoid:** Remove BOTH sys.path hacks: conftest.py line 5 AND test_renderer.py line 8.

## Code Examples

### Complete @patch Target Mapping (main → new)

Source: Verified from `main` branch `grep -rn '@patch' submodule-status/tests/`

**test_collector.py (4 patches):**
| Old Target | New Target |
|-----------|-----------|
| `"collector.datetime"` | `"submodule_status.collector.datetime"` |
| `"collector.time.sleep"` (×3) | `"submodule_status.collector.time.sleep"` |

**test_staleness.py (4 patches):**
| Old Target | New Target |
|-----------|-----------|
| `"staleness.time.sleep"` (×2) | `"submodule_status.staleness.time.sleep"` |
| `"staleness.get_bump_dates"` (×2) | `"submodule_status.staleness.get_bump_dates"` |

**test_enrichment.py (17 patches):**
| Old Target | New Target |
|-----------|-----------|
| `"enrichment.time.sleep"` (×12) | `"submodule_status.enrichment.time.sleep"` |
| `"enrichment.get_ci_status_for_pr"` (×1) | `"submodule_status.enrichment.get_ci_status_for_pr"` |
| `"enrichment.compute_avg_delay"` (×1) | `"submodule_status.enrichment.compute_avg_delay"` |
| `"enrichment.fetch_latest_repo_commits"` (×1) | `"submodule_status.enrichment.fetch_latest_repo_commits"` |
| `"enrichment.fetch_merged_bot_prs"` (×1) | `"submodule_status.enrichment.fetch_merged_bot_prs"` |
| `"enrichment.fetch_open_bot_prs"` (×1) | `"submodule_status.enrichment.fetch_open_bot_prs"` |

**test_renderer.py (0 patches):** No @patch decorators.

**Total: 25 @patch strings to update.**

### Import Statement Mapping (main → new)

**Test files:**
| File | Old Import | New Import |
|------|-----------|-----------|
| test_collector.py | `from collector import (...)` | `from submodule_status.collector import (...)` |
| test_collector.py | `import collector` (line 58) | `from submodule_status import collector` |
| test_staleness.py | `from staleness import (...)` | `from submodule_status.staleness import (...)` |
| test_enrichment.py | `from enrichment import (...)` | `from submodule_status.enrichment import (...)` |
| test_renderer.py | `from renderer import render_dashboard, ...` | `from submodule_status.renderer import render_dashboard, ...` |
| test_renderer.py | `from renderer import format_relative_time` | `from submodule_status.renderer import format_relative_time` |

**Source files (cross-module imports):**
| File | Old Import | New Import |
|------|-----------|-----------|
| collector.py | `from staleness import enrich_with_staleness` | `from submodule_status.staleness import enrich_with_staleness` |
| collector.py | `from enrichment import enrich_with_details` | `from submodule_status.enrichment import enrich_with_details` |

**sys.path hacks to REMOVE:**
| File | Line | Content |
|------|------|---------|
| conftest.py | 3-5 | `import sys, os; sys.path.insert(0, ...)` |
| test_renderer.py | 5-8 | `import sys, os; sys.path.insert(0, ...)` |

### Root pyproject.toml
```toml
[project]
name = "sonic-buildcop"
version = "0.1.0"
description = "SONiC build infrastructure tools"
requires-python = ">=3.12"

[tool.uv.workspace]
members = ["libs/*", "apps/*"]

[dependency-groups]
dev = [
    "buildcop-common",
    "buildcop-github",
    "buildcop-submodule-status",
    "pytest>=8.0",
]

[tool.uv.sources]
buildcop-common = { workspace = true }
buildcop-github = { workspace = true }
buildcop-submodule-status = { workspace = true }

[tool.pytest.ini_options]
testpaths = ["apps", "libs"]
```

### libs/buildcop-common/pyproject.toml (skeleton)
```toml
[project]
name = "buildcop-common"
version = "0.1.0"
description = "Shared utilities for SONiC build infrastructure tools"
requires-python = ">=3.12"
dependencies = []

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### libs/buildcop-github/pyproject.toml (skeleton)
```toml
[project]
name = "buildcop-github"
version = "0.1.0"
description = "GitHub API client for SONiC build infrastructure tools"
requires-python = ">=3.12"
dependencies = ["buildcop-common"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv.sources]
buildcop-common = { workspace = true }
```

### apps/submodule-status/pyproject.toml
```toml
[project]
name = "buildcop-submodule-status"
version = "0.1.0"
description = "Submodule staleness monitoring dashboard for SONiC"
requires-python = ">=3.12"
dependencies = [
    "buildcop-common",
    "jinja2>=3.1",
    "requests>=2.31",
]

[project.scripts]
collect-submodules = "submodule_status.collector:main"
render-dashboard = "submodule_status.renderer:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["submodule_status"]

[tool.uv.sources]
buildcop-common = { workspace = true }
```

### Renderer Template Path Fix
```python
# OLD (in scripts/renderer.py):
template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")

# NEW (in submodule_status/renderer.py):
template_dir = os.path.join(os.path.dirname(__file__), "templates")
```

## File Move Mapping (main → new)

| Source (main branch) | Destination |
|---------------------|------------|
| `submodule-status/scripts/collector.py` | `apps/submodule-status/submodule_status/collector.py` |
| `submodule-status/scripts/staleness.py` | `apps/submodule-status/submodule_status/staleness.py` |
| `submodule-status/scripts/enrichment.py` | `apps/submodule-status/submodule_status/enrichment.py` |
| `submodule-status/scripts/renderer.py` | `apps/submodule-status/submodule_status/renderer.py` |
| `submodule-status/templates/dashboard.html` | `apps/submodule-status/submodule_status/templates/dashboard.html` |
| `submodule-status/tests/conftest.py` | `apps/submodule-status/tests/conftest.py` |
| `submodule-status/tests/test_collector.py` | `apps/submodule-status/tests/test_collector.py` |
| `submodule-status/tests/test_staleness.py` | `apps/submodule-status/tests/test_staleness.py` |
| `submodule-status/tests/test_enrichment.py` | `apps/submodule-status/tests/test_enrichment.py` |
| `submodule-status/tests/test_renderer.py` | `apps/submodule-status/tests/test_renderer.py` |

**Files to DELETE after move:**
- `submodule-status/scripts/` (entire directory)
- `submodule-status/templates/` (entire directory)
- `submodule-status/requirements.txt` (replaced by pyproject.toml)

**New files to CREATE:**
- `apps/submodule-status/submodule_status/__init__.py`
- `libs/buildcop-common/buildcop_common/__init__.py`
- `libs/buildcop-github/buildcop_github/__init__.py`
- All 4 `pyproject.toml` files (root + 3 members)
- `.python-version` (already exists on main, keep it)

## State of the Art

| Old Approach (previous Phase 1) | Current Approach (revised) | Impact |
|--------------------------------|---------------------------|--------|
| `src/` layout | Flat layout | Less nesting, simpler config (no `src/` prefix in wheel `packages`) |
| Single `sonic_buildcop_core` package | `buildcop_common` + `buildcop_github` split | Better separation of concerns; GitHub client is heavy |
| `sonic_submodule_status` import name | `submodule_status` import name | Shorter, cleaner |
| `members = ["core", "submodule-status"]` | `members = ["libs/*", "apps/*"]` | Scalable — new packages auto-discovered |
| No grouping directories | `libs/` + `apps/` grouping | Clear categorization |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest ≥8.0 |
| Config file | Root `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest apps/submodule-status/tests/ -x` |
| Full suite command | `uv run pytest -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PKG-01 | uv workspace resolves all members | smoke | `uv sync && uv run python -c "import buildcop_common; import buildcop_github; import submodule_status"` | ❌ Wave 0 |
| PKG-02 | Lib skeletons importable | smoke | `uv run python -c "import buildcop_common; import buildcop_github"` | ❌ Wave 0 |
| PKG-03 | submodule-status installable with deps, all tests pass | unit | `uv run pytest apps/submodule-status/tests/ -x` | ✅ (migrated from main) |

### Sampling Rate
- **Per task commit:** `uv run pytest apps/submodule-status/tests/ -x`
- **Per wave merge:** `uv run pytest -v`
- **Phase gate:** Full suite green + `uv sync --frozen` succeeds

### Wave 0 Gaps
- [ ] Root `pyproject.toml` with pytest config — covers test discovery
- [ ] `uv sync` must succeed — proves workspace wiring (PKG-01, PKG-02)
- [ ] All 122 existing tests pass after migration (PKG-03)

## Open Questions

1. **`uv.lock` in `.gitignore`?**
   - Previous Phase 1 committed `uv.lock` (not gitignored). This is the recommended approach for reproducible CI builds.
   - Recommendation: Keep `uv.lock` committed, add `.venv/` to `.gitignore`.

2. **`py.typed` marker for skeletons?**
   - Previous Phase 1 included `py.typed` in core. Useful for downstream type checking.
   - Recommendation: Include in all 3 packages. Zero cost, enables `mypy` later.

3. **Should `buildcop-github` depend on `buildcop-common` in Phase 1?**
   - CONTEXT.md says `buildcop-github` is a separate package for heavy API clients.
   - Recommendation: Yes, add the dependency now (it's a skeleton, costs nothing). This proves cross-lib dependency works in the workspace.

## Sources

### Primary (HIGH confidence)
- **Local prototype testing** — verified uv workspace with `libs/*`/`apps/*` glob patterns, hatchling flat layout auto-detect behavior, and explicit `packages` config. All tests run on uv 0.7.20.
- **Codebase analysis** — complete mapping of all imports, @patch targets, and sys.path hacks from `main` branch source files.

### Secondary (MEDIUM confidence)
- `.planning/research/PITFALLS.md` — Pitfalls #5 (test import paths) and #8 (dual import paths) directly applicable. Other pitfalls (PyGithub-related) not relevant to Phase 1.
- `.planning/research/ARCHITECTURE.md` — uv workspace patterns verified and updated for libs/apps layout.
- `.planning/research/STACK.md` — uv and hatchling recommendations still current.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — uv 0.7.20 verified locally, hatchling flat layout verified with prototypes
- Architecture: HIGH — full directory structure and pyproject.toml configs verified with working builds
- Import mapping: HIGH — complete grep of all test files on main branch, every @patch counted
- Pitfalls: HIGH — critical pitfalls verified with prototype failures (hatchling auto-detect, dual imports)

**Research date:** 2026-03-25
**Valid until:** 2026-04-25 (stable domain, versions pinned)