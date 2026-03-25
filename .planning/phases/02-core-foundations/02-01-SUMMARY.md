---
phase: 02-core-foundations
plan: 01
subsystem: core
tags: [typeddict, config, python, typing, env-vars]

# Dependency graph
requires:
  - phase: 01-monorepo-scaffolding
    provides: "buildcop-common package skeleton with __init__.py and py.typed"
provides:
  - "Centralized constants module (config.py) with 11 constants and typed get() helper"
  - "TypedDict data models (models.py) with 6 TypedDicts for pipeline stages"
affects: [02-02-PLAN, 03-core-api, 04-migration]

# Tech tracking
tech-stack:
  added: []
  patterns: [typed-env-var-helper, progressive-typeddict, overloaded-function-signatures]

key-files:
  created:
    - libs/buildcop-common/buildcop_common/config.py
    - libs/buildcop-common/buildcop_common/models.py
    - libs/buildcop-common/tests/__init__.py
    - libs/buildcop-common/tests/test_config.py
    - libs/buildcop-common/tests/test_models.py
  modified: []

key-decisions:
  - "BOT_MAINTAINED as frozenset (immutable) instead of set — prevents accidental mutation"
  - "config.get() uses sentinel _MISSING pattern instead of None to distinguish 'no default' from 'default is None'"
  - "models.py has zero cross-module imports — depends only on typing stdlib"
  - "SubmoduleInfo uses NotRequired for pipeline-stage fields — supports progressive construction without total=False"

patterns-established:
  - "Typed env var helper: config.get(name, cast, default) with fail-fast ValueError"
  - "Progressive TypedDict: base fields required, pipeline-stage fields NotRequired"
  - "Overloaded function signatures for required vs optional call conventions"

requirements-completed: [CFG-01, CFG-02, MDL-01]

# Metrics
duration: 3min
completed: 2026-03-25
---

# Phase 02 Plan 01: Config & Data Models Summary

**Centralized 11 constants from 3 source files into config.py with typed get() helper, plus 6 TypedDicts formalizing all pipeline dict shapes**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-25T15:48:34Z
- **Completed:** 2026-03-25T15:51:29Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Eliminated constant duplication across collector.py, staleness.py, and enrichment.py — single source of truth in config.py
- Typed env var helper with overloaded signatures provides fail-fast semantics (ValueError on missing required vars or type coercion failures)
- 6 TypedDicts formalize all 8 implicit dict shapes from the existing pipeline, with SubmoduleInfo supporting progressive field accumulation via NotRequired
- Full TDD coverage: 12 new tests (7 config + 5 models), all 122 existing tests unaffected

## Task Commits

Each task was committed atomically:

1. **Task 1: Config module** - `2681bf7` (test: RED) → `7df2eca` (feat: GREEN)
2. **Task 2: Data models module** - `2e65115` (test: RED) → `3135e87` (feat: GREEN)

## Files Created/Modified
- `libs/buildcop-common/buildcop_common/config.py` — 11 constants + typed get() env var helper
- `libs/buildcop-common/buildcop_common/models.py` — 6 TypedDicts for pipeline data shapes
- `libs/buildcop-common/tests/__init__.py` — Package marker for test discovery
- `libs/buildcop-common/tests/test_config.py` — 7 tests for constants and get() helper
- `libs/buildcop-common/tests/test_models.py` — 5 tests for TypedDict imports and construction

## Deviations from Plan

None — plan executed exactly as written.

## Verification Results

1. ✅ `uv run pytest libs/buildcop-common/tests/ -x -q` — 12 passed
2. ✅ `uv run pytest apps/ -x -q` — 122 passed (no regression)
3. ✅ `from buildcop_common.config import API_BASE` — prints `https://api.github.com`
4. ✅ `from buildcop_common.models import SubmoduleInfo` — shows all 20 field names

## Self-Check: PASSED

All 6 files exist. All 4 commit hashes verified in git log.
