---
phase: 04-submodule-status-migration
plan: 02
subsystem: api
tags: [github-api, session-factory, retry-decorator, check-response, logging, config]

# Dependency graph
requires:
  - phase: 02-core-foundations
    provides: "config.py (API_BASE, PARENT_OWNER, PARENT_REPO, BOT_MAINTAINED, get()), log.py (setup_logging)"
  - phase: 03-core-api-infrastructure
    provides: "github.py (create_github_session, check_response, retry), exceptions.py (APIError, TransientError)"
provides:
  - "collector.py using core session factory, retry decorator, check_response, config constants, logging"
  - "renderer.py using core config.get(), setup_logging, logging"
  - "Updated retry tests compatible with @retry decorator"
affects: [04-submodule-status-migration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "@retry decorator replaces manual retry loops"
    - "check_response() replaces raise_for_status()"
    - "create_github_session() replaces manual session+token setup"
    - "config.get() replaces os.environ.get()"
    - "setup_logging() + logger.info/warning replaces print()"

key-files:
  created: []
  modified:
    - "apps/submodule-status/submodule_status/collector.py"
    - "apps/submodule-status/submodule_status/renderer.py"
    - "apps/submodule-status/tests/test_collector.py"

key-decisions:
  - "Split collect_submodule into _collect_submodule_data (@retry) + collect_submodule (error handler) for clean separation"
  - "Used @retry(max_retries=2) to match original 3 total attempts"
  - "Replaced requests.RequestException with requests.ConnectionError in tests to match @retry catch list"

patterns-established:
  - "Entry-point migration pattern: setup_logging() + create_github_session() at top of main()"
  - "Test migration pattern: patch buildcop_common.github.time.sleep instead of module-local time.sleep"

requirements-completed: [MIG-01, MIG-02, PKG-04]

# Metrics
duration: 5min
completed: 2026-03-25
---

# Phase 04 Plan 02: Entry-Point Migration Summary

**Migrated collector.py and renderer.py to core package infrastructure — session factory, @retry decorator, check_response, config constants, structured logging**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-25T18:36:07Z
- **Completed:** 2026-03-25T18:41:56Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- collector.py fully migrated: create_github_session(), @retry decorator, check_response() (5 sites), config constants, setup_logging(), logger
- renderer.py fully migrated: config_get() for env vars, setup_logging(), logger.info() replacing print()
- All 122 tests pass — zero regressions
- Zero sys.path.insert, raise_for_status, os.environ.get, print() in migrated code

## Task Commits

Each task was committed atomically:

1. **Task 1: Migrate collector.py to core infrastructure + update test_collector.py** - `b3cbbe4` (feat)
2. **Task 2: Migrate renderer.py to core infrastructure** - `21d03c7` (feat)

**Plan metadata:** _(pending)_ (docs: complete plan)

## Files Created/Modified
- `apps/submodule-status/submodule_status/collector.py` - Migrated to core session factory, retry decorator, check_response, config constants, logging
- `apps/submodule-status/submodule_status/renderer.py` - Migrated to core config.get(), setup_logging, logging
- `apps/submodule-status/tests/test_collector.py` - Updated retry tests: buildcop_common.github.time.sleep patch, ConnectionError instead of RequestException

## Decisions Made
- Split collect_submodule into _collect_submodule_data (decorated with @retry) + collect_submodule (outer error handler) for clean separation of retry logic from error recovery
- Used @retry(max_retries=2) giving 3 total attempts matching original range(3) loop
- Replaced requests.RequestException with requests.ConnectionError in test side_effects since @retry catches ConnectionError/Timeout but not generic RequestException

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Both entry points (collector.py, renderer.py) now use core infrastructure
- Ready for Plan 04-03 (staleness.py, enrichment.py migration) or CI workflow setup
- All 122 tests passing, zero legacy patterns remaining in entry points

---
*Phase: 04-submodule-status-migration*
*Completed: 2026-03-25*

## Self-Check: PASSED

All files exist, all commits verified.
