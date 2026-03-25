# Phase 3: Core API Infrastructure - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Core package provides production-ready GitHub API session management with auth, retry, rate-limit handling, and typed exceptions. Requirements: API-01, API-02, API-03, API-04. This phase builds on Phase 2's `create_session()` and `config.get()`. Phase 4 will migrate existing code to use these new APIs.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
User deferred all gray areas to Claude. The following are recommended approaches based on codebase analysis:

- **Retry mechanism**: Decorator-based (`@retry`) for reusability across any function. Match existing pattern: 3 retries, exponential backoff (2^n seconds). Retry on 5xx, network errors, and timeouts. Rate-limited (429) responses should NOT be retried by the generic retry decorator — they get separate handling.
- **Rate-limit strategy**: Raise `RateLimitError` immediately with `reset_at` timestamp attached to the exception. Callers decide whether to sleep or abort. This is the simpler, more predictable approach — auto-sleeping can block for minutes and is surprising behavior in a library.
- **Auth factory API**: Support both explicit token parameter AND auto-read from `GITHUB_TOKEN` env var. Signature: `create_github_session(token: str | None = None)`. If `token` is None, reads from env via `config.get("GITHUB_TOKEN", str)`. Raises `AuthenticationError` on missing/empty token either way. Explicit param enables testing.
- **Exception hierarchy**: `APIError` base, `AuthenticationError(APIError)`, `RateLimitError(APIError)` with `reset_at: float` attribute. Consider a `TransientError(APIError)` for 5xx so callers can distinguish retriable from permanent failures.
- **Module placement**: New modules in `buildcop_common`: `exceptions.py` for typed exceptions, `github.py` for GitHub session factory + auth + retry + rate-limit. Extend existing `http.py` if needed.
- **Existing retry extraction**: The retry decorator should be generic enough that Phase 4 can replace `collect_submodule()`'s manual retry loop with it.
- **Backoff defaults**: Base=1s, factor=2, max_delay=30s, max_retries=3. Matches existing 2^n pattern.

</decisions>

<specifics>
## Specific Ideas

No specific requirements — user deferred all decisions to Claude's judgment.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — API-01 through API-04 define exact requirements
- `.planning/ROADMAP.md` §Phase 3 — Success criteria (4 checks that must pass)

### Prior Phase Context
- `.planning/phases/01-monorepo-scaffolding/01-CONTEXT.md` — Package naming, workspace layout
- `.planning/phases/02-core-foundations/02-CONTEXT.md` — Config API (`get()` helper), logging decisions (`setup_logging()`, `getLogger(__name__)`)

### Existing Core Modules (Phase 2 outputs — Phase 3 builds on these)
- `libs/buildcop-common/buildcop_common/http.py` — `create_session()` with `TimeoutHTTPAdapter`, (30s, 60s) defaults
- `libs/buildcop-common/buildcop_common/config.py` — `API_BASE`, `PARENT_OWNER`, `PARENT_REPO` constants + `get()` env var helper
- `libs/buildcop-common/buildcop_common/log.py` — `setup_logging()` for apps, `getLogger(__name__)` pattern for library modules
- `libs/buildcop-common/buildcop_common/models.py` — TypedDicts for pipeline data
- `libs/buildcop-common/buildcop_common/__init__.py` — Re-exports all core modules

### Source Files with Migration Targets (reference for API patterns to support)
- `apps/submodule-status/submodule_status/collector.py` — Current auth setup (L227-233), retry logic (L159-206), session usage pattern
- `apps/submodule-status/submodule_status/enrichment.py` — 6 silent exception handlers, API call patterns
- `apps/submodule-status/submodule_status/staleness.py` — 2 silent exception handlers, API call patterns

### Research
- `.planning/research/PITFALLS.md` — Rate-limit and retry pitfalls
- `.planning/codebase/CONCERNS.md` — Tech debt inventory for API infrastructure

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `create_session()` in `http.py`: Already provides timeout-aware sessions — GitHub session factory should build on this, not replace it
- `config.get("GITHUB_TOKEN", str)`: Ready-made env var reader for token loading
- `setup_logging()` + `getLogger(__name__)`: Logging infrastructure ready for API modules
- Existing retry pattern in `collector.py` (L159-206): 3 retries, 2^n backoff — proven pattern to generalize

### Established Patterns
- All API functions take `session: requests.Session` as parameter — new auth session must be compatible
- All API calls follow: `resp = session.get(url)` → `resp.raise_for_status()` → `resp.json()` — typed exceptions should integrate with `raise_for_status()`
- 8 unique GitHub API endpoint patterns across 3 modules — retry/rate-limit must work for all
- Hardcoded `time.sleep(0.5)` courtesy delays between API calls — may be replaced by rate-limit awareness

### Integration Points
- `buildcop_common.__init__.py` must re-export new exceptions and GitHub session factory
- Phase 4 will import `create_github_session()` to replace manual session setup in `collector.py`
- Phase 4 will use `@retry` decorator to replace manual retry loop in `collect_submodule()`
- Exception types will be caught by enrichment/staleness code in Phase 4

### Quantified Scope
- 1 existing retry implementation to generalize
- 0 rate-limit handling to build from scratch
- 0 auth validation to build from scratch
- 4 typed exceptions to define (APIError, AuthenticationError, RateLimitError, + optional TransientError)
- 8 API endpoint patterns that must work with the new infrastructure
- 8 silent exception handlers that Phase 4 will convert to typed exception usage

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 03-core-api-infrastructure*
*Context gathered: 2026-03-25*
