---
phase: 03-core-api-infrastructure
plan: 01
subsystem: api
tags: [github-api, exceptions, retry, rate-limiting, session-factory, tdd]

requires:
  - phase: 02-core-foundations
    provides: "config.get() env var helper, create_session() with TimeoutHTTPAdapter, __init__.py re-export pattern"
provides:
  - "Typed exception hierarchy: APIError → {AuthenticationError, RateLimitError, TransientError}"
  - "GitHub session factory with auth header injection and token validation"
  - "check_response() mapping HTTP status codes to typed exceptions"
  - "retry() decorator with exponential backoff for transient failures"
affects: [04-submodule-status-migration, 05-future-client-stubs]

tech-stack:
  added: []
  patterns: [typed-exception-hierarchy, response-checker-pattern, retry-decorator-with-backoff]

key-files:
  created:
    - libs/buildcop-common/buildcop_common/exceptions.py
    - libs/buildcop-common/buildcop_common/github.py
    - libs/buildcop-common/tests/test_exceptions.py
    - libs/buildcop-common/tests/test_github.py
  modified:
    - libs/buildcop-common/buildcop_common/__init__.py

key-decisions:
  - "RateLimitError default status_code=429 (overridable for 403 rate-limit)"
  - "retry() uses ParamSpec/TypeVar for full type preservation"
  - "403 only treated as rate-limit when X-RateLimit-Remaining header equals '0'"
  - "retry catches TransientError, ConnectionError, Timeout — not RateLimitError or AuthenticationError"

patterns-established:
  - "Typed exception hierarchy: base APIError with status_code/response attrs, specialized subtypes for auth/rate-limit/transient"
  - "Response checker pattern: check_response() replaces raise_for_status() with typed exception routing"
  - "Retry decorator: configurable backoff with selective exception handling via tuple in except clause"

requirements-completed: [API-01, API-02, API-03, API-04]

duration: 3min
completed: 2026-03-25
---

# Phase 3 Plan 1: Core API Infrastructure Summary

**Typed exception hierarchy and GitHub API infrastructure (session factory, response checker, retry) with full TDD coverage — 171 tests pass**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-25T17:26:53Z
- **Completed:** 2026-03-25T17:30:21Z
- **Tasks:** 2/2
- **Files modified:** 5

## Accomplishments

### Task 1: Typed exception hierarchy (TDD)
- Created 4-class exception hierarchy: `APIError` → `{AuthenticationError, RateLimitError, TransientError}`
- `APIError` base stores `status_code` and `response` attributes
- `RateLimitError` adds `reset_at` epoch timestamp and `retry_after` computed property
- All classes properly chain inheritance for `isinstance()` checks
- 8 tests pass covering attributes, defaults, inheritance, and property behavior

### Task 2: GitHub session factory, check_response, retry (TDD)
- `create_github_session()`: creates authenticated sessions via explicit token or `GITHUB_TOKEN` env var; raises `AuthenticationError` on missing/empty/whitespace tokens
- `check_response()`: maps HTTP status codes to typed exceptions (401→AuthenticationError, 429/403+remaining=0→RateLimitError, 5xx→TransientError, other 4xx→APIError)
- `retry()`: decorator with exponential backoff; retries on `TransientError`, `ConnectionError`, `Timeout`; does NOT retry `RateLimitError` or `AuthenticationError`
- Updated `__init__.py` to re-export all 7 new public symbols
- 18 github tests + full regression: 171 tests pass with zero breakage

## Commits

| Hash | Message |
|------|---------|
| 1fbbe23 | test(03-01): add failing tests for exception hierarchy |
| 099fb66 | feat(03-01): implement typed exception hierarchy |
| 63db7aa | test(03-01): add failing tests for github session, check_response, retry |
| 21c0871 | feat(03-01): implement github session factory, check_response, retry |
| 9f7a8c5 | feat(03-01): re-export exceptions and github from __init__.py |

## Deviations from Plan

None — plan executed exactly as written.

**Minor note:** Plan acceptance criteria expected 9 exception tests but test code provided had 8 tests. All 8 match the specified behavior exactly. Plan count was off by one (no missing coverage).

## Test Results

```
171 passed in 0.77s
```

- 8 exception hierarchy tests (test_exceptions.py)
- 18 github infrastructure tests (test_github.py)
- 145 existing tests (zero regression)

## Self-Check: PASSED

All 5 created/modified files exist. All 5 commits verified in git log.
