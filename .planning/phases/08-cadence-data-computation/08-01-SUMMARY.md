---
phase: 08-cadence-data-computation
plan: 01
subsystem: staleness
tags: [github-api, cadence, pointer-bumps, sonic-buildimage, staleness]

# Dependency graph
requires:
  - phase: 02-staleness-model
    provides: "Original staleness computation with get_commit_dates, compute_cadence, compute_thresholds, classify"
  - phase: 06-enrichment-pipeline
    provides: "Enrichment pipeline with bump commits API pattern (compute_avg_delay_for_submodule)"
provides:
  - "get_bump_dates() fetching pointer bump history from sonic-buildimage"
  - "Bump-based cadence computation replacing repo commit-based cadence"
  - "Updated enrich_with_staleness() using bump dates instead of repo commits"
affects: [09-thresholds-classification-validation, staleness, renderer]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Bump-based cadence: query sonic-buildimage commits touching submodule path"]

key-files:
  created: []
  modified:
    - submodule-status/scripts/staleness.py
    - submodule-status/tests/test_staleness.py
    - submodule-status/tests/conftest.py

key-decisions:
  - "Cadence computed from pointer bump intervals in sonic-buildimage, not submodule repo commit intervals"
  - "NUM_BUMPS=30 default to get sufficient history for reliable median computation"
  - "Return dict key kept as commit_count for backwards compatibility with renderer/data.json"

patterns-established:
  - "Bump-based cadence: use /repos/sonic-net/sonic-buildimage/commits?path={submodule_path} for cadence"
  - "isinstance guard on API response before iteration"

requirements-completed: [DATA-01, DATA-02, CAD-01, CAD-02]

# Metrics
duration: 8min
completed: 2026-03-24
---

# Phase 08 Plan 01: Cadence Data Source Swap Summary

**Replaced repo commit-based cadence with pointer bump-based cadence from sonic-buildimage, using get_bump_dates() querying commits that touched each submodule path**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-24T03:32:13Z
- **Completed:** 2026-03-24T03:40:34Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Replaced `get_commit_dates()` with `get_bump_dates()` that queries sonic-buildimage for pointer bump history
- Updated `enrich_with_staleness()` to use bump dates via `get_bump_dates(session, sub["path"])`
- Renamed `MIN_COMMITS_FOR_CADENCE` → `MIN_BUMPS_FOR_CADENCE`, removed unused constants (`LOOKBACK_DAYS`, `MAX_PAGES`)
- Added `PARENT_OWNER`, `PARENT_REPO`, `NUM_BUMPS` constants
- Updated all 19 staleness tests to use bump-based data source, full suite (117 tests) passes

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement get_bump_dates() and refactor staleness.py** - `18a0695` (test: TDD RED), `f9eea18` (feat: TDD GREEN)
2. **Task 2: Update tests and fixtures for bump-based cadence** - `6fc4b84` (test)

_Note: TDD tasks have multiple commits (test → feat)_

## Files Created/Modified
- `submodule-status/scripts/staleness.py` - Replaced get_commit_dates with get_bump_dates, updated constants and enrich function
- `submodule-status/tests/test_staleness.py` - Replaced old get_commit_dates tests with 4 get_bump_dates tests, updated mock patches
- `submodule-status/tests/conftest.py` - Added mock_bump_response fixture with unsorted dates

## Decisions Made
- Cadence computed from pointer bump intervals in sonic-buildimage (not submodule repo commits) — measures how quickly drift gets resolved
- NUM_BUMPS=30 provides sufficient history for reliable median computation
- Return dict key kept as `commit_count` for backwards compatibility with renderer/data.json

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Staleness module fully migrated to bump-based cadence computation
- Ready for Phase 09 (thresholds, classification, and validation)
- `compute_cadence()`, `compute_thresholds()`, and `classify()` logic unchanged — just receives bump dates instead of repo commit dates

---
*Phase: 08-cadence-data-computation*
*Completed: 2026-03-24*
