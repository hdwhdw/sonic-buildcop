---
phase: 01-data-pipeline-deployment
plan: 01
subsystem: data-collection
tags: [python, github-api, configparser, requests, pytest, submodules]

# Dependency graph
requires: []
provides:
  - "scripts/collector.py — complete data collection pipeline for 10 sonic-net submodules"
  - "tests/test_collector.py + tests/conftest.py — 14-test unit suite with mock API fixtures"
  - "data.json output schema (generated_at, submodules array with staleness fields)"
affects: [01-02-renderer, 01-03-workflow, 02-staleness-model]

# Tech tracking
tech-stack:
  added: [requests, configparser, pytest]
  patterns: [retry-with-exponential-backoff, TDD-red-green, Contents-API-for-pinned-SHA, Compare-API-for-commits-behind]

key-files:
  created:
    - scripts/collector.py
    - tests/test_collector.py
    - tests/conftest.py
  modified: []

key-decisions:
  - "Used configparser (stdlib) for .gitmodules parsing — verified working on actual 49-entry file"
  - "Used removesuffix('.git') instead of rstrip('.git') to avoid mangling repo names like sonic-gnmi"
  - "days_behind = HEAD commit date - pinned commit date (not now() - pinned date per Pitfall 8)"
  - "Exponential backoff (2^attempt seconds) with 3 retries before marking unavailable"

patterns-established:
  - "Mock-based API testing: unittest.mock.MagicMock for requests.Session with side_effect chains"
  - "Per-submodule error isolation: failures marked unavailable, never crash entire pipeline"
  - "Branch resolution: .gitmodules branch field first, fallback to default_branch via API"

requirements-completed: [DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-06, CICD-04]

# Metrics
duration: 3min
completed: 2026-03-20
---

# Phase 1 Plan 1: Data Collector Summary

**Python collector for 10 sonic-net submodules with configparser parsing, Contents/Compare API staleness, exponential backoff retry, and 14-test TDD suite**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-20T17:28:38Z
- **Completed:** 2026-03-20T17:32:20Z
- **Tasks:** 2/2
- **Files created:** 3

## Accomplishments

- Built `scripts/collector.py` (239 lines) with 7 exported functions implementing the full data collection pipeline
- Created comprehensive test suite (14 tests) covering parsing, API calls, staleness computation, retry logic, and graceful failure
- Correctly handles all domain pitfalls: .git URL suffix normalization, name≠path mismatches, dynamic branch resolution, correct days-behind math (HEAD date - pinned date), and per-submodule error isolation

## Task Commits

Each task was committed atomically:

1. **Task 1: Create test infrastructure and collector test suite** — `3add533` (test)
2. **Task 2: Implement collector.py — make all tests pass** — `884abde` (feat, TDD green)

## Files Created/Modified

- `scripts/collector.py` — Complete data collection pipeline: parses .gitmodules, fetches pinned SHAs via Contents API, computes staleness via Compare API, writes data.json
- `tests/test_collector.py` — 14 unit tests covering all collector functions and error paths
- `tests/conftest.py` — Shared pytest fixtures: sample .gitmodules (12 entries), mock API responses

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

- pytest not pre-installed on system Python — installed via pip (standard dev dependency, no plan deviation)

## Next Phase Readiness

- `scripts/collector.py` produces `data.json` with the documented schema — ready for Plan 02 (HTML renderer)
- Test fixtures in `tests/conftest.py` reusable by renderer tests
- All DATA requirements and CICD-04 (graceful failure) verified by tests

---
*Phase: 01-data-pipeline-deployment*
*Plan: 01*
*Completed: 2026-03-20*
