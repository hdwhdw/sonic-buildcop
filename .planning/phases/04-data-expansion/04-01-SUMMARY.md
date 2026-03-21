---
phase: 04-data-expansion
plan: 01
subsystem: data-pipeline
tags: [gitmodules, filtering, collector, sonic-net]

# Dependency graph
requires:
  - phase: 01-data-pipeline
    provides: parse_gitmodules function with TARGET_SUBMODULES filtering
provides:
  - Owner-based submodule filtering (owner == REPO_OWNER)
  - Fixture with non-sonic-net entries for exclusion testing
affects: [04-data-expansion, collector, dashboard]

# Tech tracking
tech-stack:
  added: []
  patterns: [owner-based filtering instead of hardcoded lists]

key-files:
  created: []
  modified:
    - scripts/collector.py
    - tests/conftest.py
    - tests/test_collector.py

key-decisions:
  - "Filter by owner == REPO_OWNER instead of hardcoded TARGET_SUBMODULES list"

patterns-established:
  - "Owner-based filtering: new sonic-net submodules are automatically included without code changes"

requirements-completed: [DATA-09]

# Metrics
duration: 3min
completed: 2026-03-21
---

# Phase 4 Plan 1: Owner-based Submodule Filtering Summary

**Replace hardcoded TARGET_SUBMODULES list with dynamic owner-based filtering (owner == REPO_OWNER) to track all sonic-net submodules automatically**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-21T05:30:07Z
- **Completed:** 2026-03-21T05:33:29Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Removed TARGET_SUBMODULES hardcoded list from collector.py
- Implemented owner-based filtering: `if owner == REPO_OWNER:` instead of slug matching
- Added non-sonic-net fixture entries (p4lang/p4rt-app, Azure/sonic-build-tools) for exclusion testing
- Added test_parse_gitmodules_excludes_non_sonic_net to verify filtering
- Updated all existing tests for 12-entry expectations (was 10)
- All 58 tests pass

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Add failing test for owner-based filtering** - `425ea56` (test)
2. **Task 1 (GREEN): Implement owner-based submodule filtering** - `ddb0242` (feat)
3. **Task 2: Update tests for owner-based filtering** - `30a5bb2` (feat)

_Note: Task 1 used TDD — RED commit for failing test, GREEN commit for implementation._

## Files Created/Modified
- `scripts/collector.py` - Removed TARGET_SUBMODULES, changed filter to owner == REPO_OWNER
- `tests/conftest.py` - Added 2 non-sonic-net entries to fixture (14 total: 12 sonic-net + 2 non-sonic-net)
- `tests/test_collector.py` - Updated 4 tests, added 1 new test, removed TARGET_SUBMODULES references

## Decisions Made
- Filter by owner == REPO_OWNER instead of hardcoded TARGET_SUBMODULES list — eliminates maintenance burden as sonic-buildimage adds new submodules

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Owner-based filtering is in place; collector will now pick up all sonic-net submodules
- Ready for Phase 4 Plan 2 (template/rendering updates if needed for additional submodules)

---
*Phase: 04-data-expansion*
*Completed: 2026-03-21*

## Self-Check: PASSED
