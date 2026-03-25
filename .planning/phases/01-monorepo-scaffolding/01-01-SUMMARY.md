---
phase: 01-monorepo-scaffolding
plan: 01
subsystem: infra
tags: [uv, hatchling, monorepo, python-packaging, src-layout, workspace]

# Dependency graph
requires: []
provides:
  - "uv workspace with root pyproject.toml and [tool.uv.workspace] config"
  - "core package skeleton (sonic-buildcop-core) with hatchling build backend"
  - "submodule-status package (sonic-submodule-status) with src-layout and entry points"
  - "all source/test files migrated to proper Python packaging"
affects: [02-core-foundations, 03-core-api-infrastructure, 04-submodule-status-migration]

# Tech tracking
tech-stack:
  added: [uv 0.7, hatchling, pytest>=8.0]
  patterns: [uv-workspace, src-layout, fully-qualified-imports]

key-files:
  created:
    - pyproject.toml
    - .python-version
    - core/pyproject.toml
    - core/src/sonic_buildcop_core/__init__.py
    - core/src/sonic_buildcop_core/py.typed
    - submodule-status/pyproject.toml
    - submodule-status/src/sonic_submodule_status/__init__.py
    - uv.lock
  modified:
    - .gitignore
    - submodule-status/src/sonic_submodule_status/collector.py
    - submodule-status/src/sonic_submodule_status/renderer.py
    - submodule-status/tests/conftest.py
    - submodule-status/tests/test_collector.py
    - submodule-status/tests/test_staleness.py
    - submodule-status/tests/test_enrichment.py
    - submodule-status/tests/test_renderer.py

key-decisions:
  - "uv.lock committed for reproducible builds (not gitignored)"
  - "py.typed marker included in core for PEP 561 type-checking support"

patterns-established:
  - "Workspace members: core/ and submodule-status/ as [tool.uv.workspace] members"
  - "src-layout: all packages use src/package_name/ directory structure"
  - "Fully qualified imports: all cross-module imports use sonic_submodule_status.module syntax"
  - "Entry points: console scripts declared in pyproject.toml [project.scripts]"

requirements-completed: [PKG-01, PKG-02, PKG-03]

# Metrics
duration: 23min
completed: 2026-03-25
---

# Phase 1 Plan 1: Monorepo Scaffolding Summary

**uv workspace monorepo with core skeleton and submodule-status migrated to src-layout — 122 tests passing with zero sys.path hacks**

## Performance

- **Duration:** 23 min
- **Started:** 2026-03-25T03:13:08Z
- **Completed:** 2026-03-25T03:36:08Z
- **Tasks:** 2
- **Files modified:** 20

## Accomplishments
- Created uv workspace with root pyproject.toml declaring core and submodule-status as workspace members
- Built core package skeleton (sonic-buildcop-core v0.1.0) with hatchling build backend and py.typed marker
- Created submodule-status package (sonic-submodule-status) with dependencies on core, jinja2, requests, and wired entry points (collect-submodules, render-dashboard)
- Atomically migrated all 4 source files from scripts/ to src-layout, moved templates into package, rewrote all 25 @patch decorators, removed both sys.path.insert hacks
- All 122 existing tests pass with new fully qualified import paths

## Task Commits

Each task was committed atomically:

1. **Task 1: Create workspace pyproject.toml files, core skeleton, and package structure** - `1acd4e0` (feat)
2. **Task 2: Atomic migration — move source files, rewrite all imports, remove sys.path hacks** - `7baed1b` (feat)

## Files Created/Modified
- `pyproject.toml` - Workspace root with [tool.uv.workspace] members, dev dependency-group, pytest config
- `.python-version` - Python 3.12 pinned for uv
- `.gitignore` - Added .venv/ exclusion
- `core/pyproject.toml` - Core package build config with hatchling
- `core/src/sonic_buildcop_core/__init__.py` - Core package with __version__ = "0.1.0"
- `core/src/sonic_buildcop_core/py.typed` - PEP 561 type-checking marker
- `submodule-status/pyproject.toml` - Deliverable package with core dependency and entry points
- `submodule-status/src/sonic_submodule_status/__init__.py` - Package marker
- `submodule-status/src/sonic_submodule_status/collector.py` - Migrated from scripts/, imports updated
- `submodule-status/src/sonic_submodule_status/staleness.py` - Migrated from scripts/
- `submodule-status/src/sonic_submodule_status/enrichment.py` - Migrated from scripts/
- `submodule-status/src/sonic_submodule_status/renderer.py` - Migrated from scripts/, template path fixed
- `submodule-status/src/sonic_submodule_status/templates/dashboard.html` - Moved into package
- `submodule-status/tests/conftest.py` - sys.path.insert hack removed
- `submodule-status/tests/test_collector.py` - Imports and @patch targets updated
- `submodule-status/tests/test_staleness.py` - Imports and @patch targets updated
- `submodule-status/tests/test_enrichment.py` - Imports and @patch targets updated
- `submodule-status/tests/test_renderer.py` - sys.path hack removed, imports updated
- `uv.lock` - Lockfile for reproducible builds

## Decisions Made
- Committed uv.lock for reproducible builds (per research recommendation — not gitignored)
- Included py.typed PEP 561 marker in core package for type-checking support (per CONTEXT.md discretion)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all tasks completed without errors.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Workspace infrastructure complete: `uv sync` installs both packages, all tests pass
- Core package skeleton ready for Phase 2 (config, data models, logging)
- Submodule-status package correctly depends on core via workspace reference
- Entry points wired and importable for Phase 4 migration

---
*Phase: 01-monorepo-scaffolding*
*Completed: 2026-03-25*

## Self-Check: PASSED

All created files verified present. All commit hashes verified in git log.
