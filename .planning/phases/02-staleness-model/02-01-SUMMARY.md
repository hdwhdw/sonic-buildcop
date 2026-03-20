---
phase: 02-staleness-model
plan: 01
subsystem: staleness
tags: [statistics, median, github-api, classification, cadence]

# Dependency graph
requires:
  - phase: 01-data-pipeline-deployment
    provides: "collector.py with session pattern, submodule dict shape, GitHub API infrastructure"
provides:
  - "staleness.py module with 5 exported functions"
  - "Cadence computation via statistics.median"
  - "Threshold derivation (2×/4× median multipliers)"
  - "Green/yellow/red classification with worst-of rule"
  - "Fallback thresholds for sparse repos (<5 commits)"
affects: [02-staleness-model, 03-ui-polish]

# Tech tracking
tech-stack:
  added: [statistics.median]
  patterns: [median-based cadence, worst-of classification, fallback thresholds]

key-files:
  created:
    - scripts/staleness.py
    - tests/test_staleness.py
  modified:
    - tests/conftest.py

key-decisions:
  - "Separate staleness.py module — not integrated into collector.py"
  - "statistics.median for outlier-resistant cadence computation"
  - "1.0-day minimum floor prevents zero-threshold edge case"
  - "Fixed commit thresholds (2/4) complement day-based thresholds"

patterns-established:
  - "TDD: RED tests first, then GREEN implementation"
  - "Cadence pattern: fetch history → compute median → derive thresholds → classify"
  - "Fallback pattern: sparse repos get safe defaults"
  - "Worst-of rule: independent evaluation of days and commits signals"

requirements-completed: [STALE-01, STALE-02, STALE-03, STALE-04]

# Metrics
duration: 3min
completed: 2026-03-20
---

# Phase 2 Plan 1: Staleness Module Summary

**Median-based cadence computation with 2×/4× threshold derivation and worst-of green/yellow/red classification**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-20T19:44:40Z
- **Completed:** 2026-03-20T19:47:32Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Created staleness.py with 5 exported functions: get_commit_dates, compute_cadence, compute_thresholds, classify, enrich_with_staleness
- 20 test functions covering all edge cases: outlier resistance, fallback thresholds, minimum floor, worst-of rule
- Extended conftest.py with 4 new fixtures without breaking existing 23 tests
- All 43 tests pass (14 collector + 9 renderer + 20 staleness)

## Task Commits

Each task was committed atomically:

1. **Task 1: Write failing tests (RED)** - `f2fafb8` (test)
2. **Task 2: Implement staleness.py (GREEN)** - `6ee3272` (feat)

## Files Created/Modified
- `scripts/staleness.py` - Staleness computation module: cadence, thresholds, classification
- `tests/test_staleness.py` - 20 unit tests for all staleness functions
- `tests/conftest.py` - Extended with 4 new fixtures (mock_commits_page_1/2, sample_submodule_ok/unavailable)

## Decisions Made
- Separate `staleness.py` module keeps collector.py unchanged and staleness functions independently testable
- `statistics.median` chosen over mean for natural outlier resistance (single 30-day gap doesn't skew daily repo's threshold)
- 1.0-day minimum floor on median prevents zero-interval bursts from creating impossibly tight thresholds
- Fixed commit thresholds (yellow=2, red=4) complement day-based thresholds via worst-of rule

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness
- staleness.py ready to be imported by collector.py in Plan 02 (pipeline integration)
- enrich_with_staleness function designed to mutate submodule dicts in-place for seamless integration
- Template will need staleness_status field for badge rendering (Phase 02 Plan 02 or Phase 03)

## Self-Check: PASSED

- [x] scripts/staleness.py exists
- [x] tests/test_staleness.py exists
- [x] tests/conftest.py exists
- [x] 02-01-SUMMARY.md exists
- [x] Commit f2fafb8 exists (RED)
- [x] Commit 6ee3272 exists (GREEN)
- [x] All 43 tests pass

---
*Phase: 02-staleness-model*
*Completed: 2026-03-20*
