---
phase: 01-monorepo-scaffolding
plan: "01"
subsystem: packaging
tags: [uv-workspace, monorepo, migration, python-packaging]
dependency_graph:
  requires: []
  provides: [buildcop-common, buildcop-github, submodule-status-package, uv-workspace]
  affects: [all-future-phases]
tech_stack:
  added: [uv-workspaces, hatchling]
  patterns: [flat-layout, libs-apps-grouping]
key_files:
  created:
    - pyproject.toml
    - .python-version
    - libs/buildcop-common/pyproject.toml
    - libs/buildcop-common/buildcop_common/__init__.py
    - libs/buildcop-common/buildcop_common/py.typed
    - libs/buildcop-github/pyproject.toml
    - libs/buildcop-github/buildcop_github/__init__.py
    - libs/buildcop-github/buildcop_github/py.typed
    - apps/submodule-status/pyproject.toml
    - apps/submodule-status/submodule_status/__init__.py
    - apps/submodule-status/submodule_status/py.typed
    - uv.lock
  modified:
    - .gitignore
    - apps/submodule-status/submodule_status/collector.py
    - apps/submodule-status/submodule_status/renderer.py
    - apps/submodule-status/tests/conftest.py
    - apps/submodule-status/tests/test_collector.py
    - apps/submodule-status/tests/test_staleness.py
    - apps/submodule-status/tests/test_enrichment.py
    - apps/submodule-status/tests/test_renderer.py
decisions:
  - "uv workspaces with libs/apps flat layout for package organization"
  - "hatchling as build backend for all workspace members"
  - "uv.lock committed for reproducible builds"
  - "py.typed PEP 561 markers in all packages"
metrics:
  duration: 6min
  completed: "2026-03-25T13:19:00Z"
---

# Phase 01 Plan 01: Workspace Infrastructure + Atomic Source/Test Migration Summary

uv workspace monorepo with 3 installable packages (buildcop-common, buildcop-github, buildcop-submodule-status) using libs/apps flat layout, all 122 tests passing with fully-qualified imports and zero sys.path hacks.

## What Was Done

### Task 1: Create workspace infrastructure (705eae8)

Created the uv workspace monorepo structure from scratch on the `main` branch:

- **Root `pyproject.toml`**: Workspace configuration with `members = ["libs/*", "apps/*"]`, dev dependency group including all 3 packages + pytest, `[tool.uv.sources]` workspace refs, and `[tool.pytest.ini_options]` testpaths
- **`.python-version`**: Pinned to 3.12
- **`libs/buildcop-common/`**: Shared utilities package skeleton with `__init__.py` (`__version__ = "0.1.0"`), `py.typed` marker, hatchling build backend
- **`libs/buildcop-github/`**: GitHub API client package depending on buildcop-common via workspace ref
- **`apps/submodule-status/pyproject.toml`**: App package with `[tool.hatch.build.targets.wheel] packages = ["submodule_status"]` to handle PyPI name vs import name mismatch, console entry points for `collect-submodules` and `render-dashboard`
- **`.gitignore`**: Added `.venv/` entry

### Task 2: Atomic source/test migration with import rewrites (a31a892)

Migrated all source and test files from `submodule-status/scripts/` to the new package layout in a single atomic commit:

- **4 source files** moved to `apps/submodule-status/submodule_status/`
- **Import rewrites in `collector.py`**: `from staleness import` → `from submodule_status.staleness import`, same for enrichment
- **Renderer template path fixed**: Removed `".."` from template_dir since templates/ is now inside the package
- **5 test files** migrated to `apps/submodule-status/tests/`
- **25 @patch decorators** updated to use `submodule_status.*` module paths
- **2 sys.path.insert hacks** removed (conftest.py and test_renderer.py)
- **`uv.lock`** committed for reproducible builds
- **Old `submodule-status/`** directory removed entirely

## Verification Results

| Check | Result |
|-------|--------|
| `uv sync` resolves all 3 workspace members | ✅ |
| 122 tests pass | ✅ |
| `import buildcop_common` works | ✅ (v0.1.0) |
| `import buildcop_github` works | ✅ (v0.1.0) |
| `import submodule_status` works | ✅ |
| Entry points resolve | ✅ |
| Zero sys.path.insert calls | ✅ (0 matches) |
| 25 @patch with submodule_status prefix | ✅ |
| No old directories (core/, submodule-status/) | ✅ |

## Deviations from Plan

None — plan executed exactly as written.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | 705eae8 | feat(01-01): create uv workspace infrastructure with libs/apps layout |
| 2 | a31a892 | feat(01-01): atomic source/test migration with import rewrites |
