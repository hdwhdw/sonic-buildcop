---
phase: 06-data-enrichment
plan: 01
subsystem: api
tags: [github-api, search-issues, check-runs, enrichment, bot-prs]

# Dependency graph
requires:
  - phase: 02-staleness-model
    provides: "staleness.py in-place enrichment pattern, enrich_with_staleness()"
  - phase: 01-data-pipeline
    provides: "collector.py constants (REPO_OWNER, PARENT_REPO, API_BASE, BOT_MAINTAINED), submodule dict shape"
provides:
  - "enrichment.py module with 5 exported functions for bot PR, CI status, and commit enrichment"
  - "match_pr_to_submodule for longest-first PR-to-submodule matching"
  - "get_ci_status_for_pr for Check Runs API aggregation"
  - "fetch_open_bot_prs for batch open bot PR search + in-place enrichment"
  - "fetch_merged_bot_prs for batch merged bot PR search + in-place enrichment"
  - "fetch_latest_repo_commits for per-submodule HEAD commit URL and date"
  - "16 unit tests covering ENRICH-01, ENRICH-02, ENRICH-03"
  - "8 conftest fixtures for Search API, Check Runs, commits, PR detail mocks"
affects: [06-02-PLAN, 07-ui-expansion]

# Tech tracking
tech-stack:
  added: []
  patterns: ["batch Search API + client-side title matching for PR-to-submodule association", "longest-first name sorting to avoid prefix collisions", "Check Runs API aggregation (pass/fail/pending/null)"]

key-files:
  created:
    - submodule-status/scripts/enrichment.py
    - submodule-status/tests/test_enrichment.py
  modified:
    - submodule-status/tests/conftest.py

key-decisions:
  - "Batch Search API calls (1 for open, 1 for merged) instead of per-submodule PR lookups"
  - "Longest-first name sorting prevents sonic-swss matching before sonic-swss-common"
  - "Check Runs API aggregation: fail > pending > pass priority, null for no checks or errors"

patterns-established:
  - "Batch Search API + match_pr_to_submodule pattern for PR-to-submodule association"
  - "In-place dict enrichment with None defaults for all fields before processing"

requirements-completed: [ENRICH-01, ENRICH-02, ENRICH-03]

# Metrics
duration: 4min
completed: 2026-03-23
---

# Phase 6 Plan 1: Enrichment Module Summary

**Bot PR search, CI status aggregation, merged PR tracking, and latest repo commits via GitHub Search/Check Runs/Commits APIs with batch fetching and longest-first name matching**

## Performance

- **Duration:** 3m35s
- **Started:** 2026-03-23T16:24:20Z
- **Completed:** 2026-03-23T16:27:55Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Created enrichment.py module with 5 exported functions following staleness.py in-place enrichment pattern
- Batch Search API fetching for open and merged bot PRs (2 API calls instead of 32+)
- Longest-first name sorting prevents prefix collision (sonic-swss vs sonic-swss-common)
- Check Runs API aggregation with fail/pending/pass priority and null fallback
- 16 unit tests covering all ENRICH-01/02/03 behaviors plus error handling
- 8 conftest fixtures for mock Search, Check Runs, commit, and PR responses
- Full test suite: 94 tests passing (78 existing + 16 new)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create enrichment.py with ENRICH-01/02/03 functions** - `96a0517` (feat)
2. **Task 2: Create test_enrichment.py + conftest fixtures** - `41c4f52` (test)

_TDD RED commit: `0bc0fb7` (failing import test before implementation)_

## Files Created/Modified
- `submodule-status/scripts/enrichment.py` - Bot PR search, CI status, merged PR, latest commit enrichment (5 functions)
- `submodule-status/tests/test_enrichment.py` - 16 unit tests covering ENRICH-01/02/03 + error cases
- `submodule-status/tests/conftest.py` - 8 new Phase 6 fixtures for mock API responses

## Decisions Made
- Batch Search API calls (1 for open, 1 for merged) instead of per-submodule PR lookups — minimizes API calls
- Longest-first name sorting prevents sonic-swss matching before sonic-swss-common — critical for correctness
- Check Runs API aggregation: fail > pending > pass priority, null for no checks or errors — matches GitHub UI behavior

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- enrichment.py ready to be integrated into collector.py main() in Plan 06-02
- All 5 functions importable and tested
- conftest fixtures available for future enrichment-related tests

## Self-Check: PASSED

All files exist, all commits verified.

---
*Phase: 06-data-enrichment*
*Completed: 2026-03-23*
