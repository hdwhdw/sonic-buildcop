---
phase: 06-data-enrichment
plan: 02
subsystem: api
tags: [github-api, commits-api, contents-api, average-delay, enrichment, integration]

# Dependency graph
requires:
  - phase: 06-data-enrichment
    plan: 01
    provides: "enrichment.py with 5 functions (fetch_open_bot_prs, fetch_merged_bot_prs, fetch_latest_repo_commits, match_pr_to_submodule, get_ci_status_for_pr)"
  - phase: 02-staleness-model
    provides: "staleness.py enrich_with_staleness(), statistics.mean pattern"
  - phase: 01-data-pipeline
    provides: "collector.py main(), submodule dict shape, session setup"
provides:
  - "compute_avg_delay_for_submodule for bump history → delay computation"
  - "compute_avg_delay for batch in-place avg_delay_days enrichment"
  - "enrich_with_details as single entry point for all enrichment"
  - "collector.py integration — enrichment runs automatically in data pipeline"
  - "7 new unit tests covering ENRICH-04 edge cases"
  - "3 new conftest fixtures for bump/contents/commit mocks"
affects: [07-ui-expansion]

# Tech tracking
tech-stack:
  added: []
  patterns: ["bump history via Commits API path filter", "Contents API ref param for point-in-time SHA lookup", "negative delay filtering for clock skew protection"]

key-files:
  created: []
  modified:
    - submodule-status/scripts/enrichment.py
    - submodule-status/scripts/collector.py
    - submodule-status/tests/test_enrichment.py
    - submodule-status/tests/conftest.py

key-decisions:
  - "isinstance guard on bump commits response for API robustness"
  - "Minimum 2 valid data points required for avg_delay_days (else None)"
  - "enrich_with_details is the single orchestrator calling all 4 enrichment sub-functions"

patterns-established:
  - "Commits API path filter for pointer bump history retrieval"
  - "Contents API ref parameter for point-in-time submodule SHA resolution"

requirements-completed: [ENRICH-04]

# Metrics
duration: 4min
completed: 2026-03-23
---

# Phase 6 Plan 2: Average Delay + Integration Summary

**Average delay computation via bump history analysis (Commits API path filter + Contents API ref lookup), enrich_with_details entry point, and collector.py integration — completing all 4 ENRICH requirements**

## Performance

- **Duration:** 4m19s
- **Started:** 2026-03-23T16:31:48Z
- **Completed:** 2026-03-23T16:36:07Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Added compute_avg_delay_for_submodule: fetches last 5 pointer bump commits via Commits API path filter, resolves submodule SHAs at each bump via Contents API ref parameter, computes mean delay
- Added compute_avg_delay: batch in-place enrichment with avg_delay_days for all submodules
- Added enrich_with_details: single entry point orchestrating all 4 enrichment functions (open bot PRs, merged bot PRs, latest commits, avg delay)
- Wired enrichment into collector.py main() — runs automatically after enrich_with_staleness
- Negative delay filtering prevents clock skew from corrupting averages
- isinstance guard on API response for robustness against unexpected JSON
- 7 new tests + 3 new fixtures covering all ENRICH-04 edge cases
- Full test suite: 101 tests passing (78 existing + 16 from Plan 01 + 7 new)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add compute_avg_delay + enrich_with_details to enrichment.py** — `9b5d8d8` (feat)
2. **Task 2: Add ENRICH-04 tests + wire enrichment into collector.py** — `d25be27` (test)

_TDD RED commit: `805af17` (failing imports before implementation)_

## Files Created/Modified
- `submodule-status/scripts/enrichment.py` — Added 3 functions: compute_avg_delay_for_submodule, compute_avg_delay, enrich_with_details + import statistics
- `submodule-status/scripts/collector.py` — Added `from enrichment import enrich_with_details` and call in main()
- `submodule-status/tests/test_enrichment.py` — 7 new tests for ENRICH-04 (now 23 total enrichment tests)
- `submodule-status/tests/conftest.py` — 3 new fixtures: mock_bump_commits, mock_contents_at_bump, mock_sub_commit_dates

## Decisions Made
- isinstance guard on bump commits response for API robustness — prevents crash on unexpected dict responses
- Minimum 2 valid data points required for avg_delay_days (else None) — avoids unreliable single-sample averages
- enrich_with_details is the single orchestrator calling all 4 enrichment sub-functions — clean integration point

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Added isinstance check on bump commits response**
- **Found during:** Task 2 verification
- **Issue:** If API returned a dict instead of a list, `len(dict)` could pass the `< 2` check, causing iteration over string keys
- **Fix:** Added `not isinstance(bumps, list)` guard before length check
- **Files modified:** submodule-status/scripts/enrichment.py
- **Commit:** d25be27

## Issues Encountered
None

## User Setup Required
None — no external service configuration required.

## Next Phase Readiness
- All 4 ENRICH requirements complete (ENRICH-01 through ENRICH-04)
- enrichment.py fully integrated into collector.py data pipeline
- data.json now includes: open_bot_pr, last_merged_bot_pr, latest_repo_commit, avg_delay_days per submodule
- Ready for Phase 07 (UI expansion) to render the new enrichment data

## Self-Check: PASSED

All files exist, all commits verified.

---
*Phase: 06-data-enrichment*
*Completed: 2026-03-23*
