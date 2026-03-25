---
phase: 04-submodule-status-migration
plan: 01
subsystem: api
tags: [migration, github-api, exceptions, logging, buildcop-common]

# Dependency graph
requires:
  - phase: 02-core-foundations
    provides: "config constants (API_BASE, PARENT_OWNER, etc.), logging setup"
  - phase: 03-core-api-infrastructure
    provides: "check_response(), APIError exception hierarchy"
provides:
  - "staleness.py migrated to buildcop_common imports (constants, check_response, APIError, logging)"
  - "enrichment.py migrated to buildcop_common imports (constants, check_response, APIError, logging)"
  - "9 check_response() calls replacing raise_for_status()"
  - "9 logger.warning() calls with exc_info=True on silent handlers"
affects: [04-submodule-status-migration]

# Tech tracking
tech-stack:
  added: []
  patterns: ["import constants from buildcop_common.config instead of local definitions", "check_response(resp) replaces resp.raise_for_status()", "APIError added to all except clauses alongside requests.RequestException", "logger.warning with exc_info=True on all graceful-degradation handlers"]

key-files:
  created: []
  modified:
    - "apps/submodule-status/submodule_status/staleness.py"
    - "apps/submodule-status/submodule_status/enrichment.py"

key-decisions:
  - "Kept import requests alongside buildcop_common imports — still needed for Session type hints and RequestException"
  - "FALLBACK_THRESHOLDS updated to reference MAX_YELLOW_DAYS/MAX_RED_DAYS constants instead of hardcoded 30/60"

patterns-established:
  - "Migration pattern: add buildcop_common imports, remove local constants, swap raise_for_status→check_response, add APIError+logger.warning to except blocks"

requirements-completed: [MIG-01, MIG-02]

# Metrics
duration: 4min
completed: 2026-03-25
---

# Phase 4 Plan 1: Staleness & Enrichment Migration Summary

**Migrated staleness.py and enrichment.py to buildcop_common — zero local constant duplicates, typed check_response() on 9 API calls, structured logger.warning() on all 9 silent exception handlers**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-25T18:36:29Z
- **Completed:** 2026-03-25T18:40:47Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- staleness.py imports 8 constants from buildcop_common.config, uses check_response() and APIError, has logger.warning() on both silent handlers
- enrichment.py imports 4 constants from buildcop_common.config, replaces all 8 raise_for_status() with check_response(), has logger.warning() on all 7 silent handlers
- All 122 existing tests pass unchanged — zero test file modifications
- Zero local constant definitions remain in either migrated file

## Task Commits

Each task was committed atomically:

1. **Task 1: Migrate staleness.py to core infrastructure** - `e2a0fb2` (feat)
2. **Task 2: Migrate enrichment.py to core infrastructure** - `b7eef48` (feat)

## Files Created/Modified
- `apps/submodule-status/submodule_status/staleness.py` — Migrated to core config, check_response, APIError, structured logging
- `apps/submodule-status/submodule_status/enrichment.py` — Migrated to core config, check_response, APIError, structured logging

## Decisions Made
- Kept `import requests` alongside buildcop_common imports since `requests.Session` type hints and `requests.RequestException` are still needed in except clauses
- Updated FALLBACK_THRESHOLDS to use `MAX_YELLOW_DAYS`/`MAX_RED_DAYS` imported constants instead of hardcoded values 30/60

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None — no external service configuration required.

## Next Phase Readiness
- staleness.py and enrichment.py fully migrated — ready for Plan 02 (collector.py migration: session factory, retry decorator, env vars)
- Migration pattern established: import core → remove locals → swap raise_for_status → add APIError + logger.warning

---
*Phase: 04-submodule-status-migration*
*Completed: 2026-03-25*

## Self-Check: PASSED
