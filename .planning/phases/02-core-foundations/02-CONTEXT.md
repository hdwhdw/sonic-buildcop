# Phase 2: Core Foundations - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Core package provides centralized configuration, typed data models, and structured logging that any deliverable can import. Requirements: CFG-01, CFG-02, CFG-03, LOG-01, LOG-02, MDL-01. No business logic changes — this phase builds the foundation layer in `buildcop-common`.

</domain>

<decisions>
## Implementation Decisions

### Data model scope
- Formalize all 8 dict shapes as TypedDicts now (not deferred to Phase 4)
- One flat `SubmoduleInfo` TypedDict with ALL fields (base + staleness + enrichment), `Optional` for fields not yet populated at each pipeline stage
- `StalenessData` dissolves into `SubmoduleInfo` fields directly (`commits_behind`, `days_behind`)
- Small nested TypedDicts: `OpenBotPR`, `LastMergedBotPR`, `LatestRepoCommit`, `Cadence`, `Thresholds`
- TypedDict chosen over dataclass for dict-compatibility — existing code uses `sub["field"]` access throughout, Phase 4 migration becomes mechanical (add type annotations, swap imports)

### Logging behavior
- Human-readable format for GitHub Actions console readability
- Default log level: INFO — matches current `print()` behavior (progress messages stay visible)
- Core provides a `setup_logging()` convenience function that apps call in their `main()`
- Consistent format across all apps: timestamp, level, module name, message
- Library modules use `logging.getLogger(__name__)` internally

### Config access pattern
- Fixed constants exposed as module attributes: `from buildcop_common.config import API_BASE, PARENT_OWNER, PARENT_REPO`
- Dynamic env-var-backed config via typed helper: `config.get("GITHUB_TOKEN", str)`, `config.get("TIMEOUT", int, 30)`
- Missing required env vars (called without default) raise `ValueError` immediately with clear message — fail fast, no silent failures
- Constants to centralize: `API_BASE`, `PARENT_OWNER`, `PARENT_REPO`, `BOT_AUTHOR`, `BOT_MAINTAINED` set, `MIN_BUMPS_FOR_CADENCE`, `NUM_BUMPS`, `MAX_YELLOW_DAYS`, `MAX_RED_DAYS`

### Claude's Discretion
- Exact TypedDict field names and Optional annotations
- `setup_logging()` function signature and configurable parameters
- Log format string details (timestamp format, separator style)
- Internal module organization within `buildcop_common` (flat vs subpackages)
- HTTP session factory placement (common vs github package)
- Whether to add `NotRequired` (Python 3.11+) vs `Optional` for progressive fields

</decisions>

<specifics>
## Specific Ideas

- SubmoduleInfo should be a single flat TypedDict that accumulates fields as data flows through collector → staleness → enrichment pipeline, not a hierarchy of types
- The `get()` helper calling convention signals intent: `get("TOKEN", str)` = required, `get("TIMEOUT", int, 30)` = optional with default
- Logging should be a drop-in replacement for the 3 existing print statements — same information, proper logging

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — CFG-01 through CFG-03, LOG-01, LOG-02, MDL-01 define exact requirements
- `.planning/ROADMAP.md` §Phase 2 — Success criteria (5 checks that must pass)

### Prior Phase Context
- `.planning/phases/01-monorepo-scaffolding/01-CONTEXT.md` — Package naming (`buildcop_common`, `buildcop_github`), workspace layout, build backend decisions

### Codebase Analysis
- `.planning/codebase/ARCHITECTURE.md` — Current module pipeline: collector → staleness → enrichment → renderer
- `.planning/codebase/STRUCTURE.md` — Current directory layout after Phase 1 migration
- `.planning/codebase/CONCERNS.md` — Tech debt: duplicated constants, no logging, silent failures

### Source Files with Migration Targets
- `apps/submodule-status/submodule_status/collector.py` — Constants (L14-16), session creation (L227-229), print (L270), dict shapes (L73-80, L188-222)
- `apps/submodule-status/submodule_status/enrichment.py` — Constants (L25-28), 6 silent exception handlers, dict shapes (L160-164, L218-221, L251-254)
- `apps/submodule-status/submodule_status/staleness.py` — Constants (L22-36), 2 silent exception handlers, Cadence/Thresholds dicts (L81-129)
- `apps/submodule-status/submodule_status/renderer.py` — Env var access (L107-108), print (L101-102)

### Research
- `.planning/research/STACK.md` — uv workspace config, hatchling build backend
- `.planning/research/PITFALLS.md` — Packaging pitfalls relevant to adding modules to core

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Session creation pattern in `collector.py` (L227-229): single session with auth header, passed to all functions — good pattern to wrap in factory
- Exception handling pattern: `except (requests.RequestException, KeyError, ValueError)` — consistent across 8 handlers, can be standardized

### Established Patterns
- All API functions take `session: requests.Session` as first parameter — core factory must return compatible type
- Dict mutation pattern: functions receive a submodule dict and add fields to it — TypedDict with Optional fields fits this exactly
- Env var access: `os.environ.get("VAR", "default")` — 3 occurrences to consolidate into `config.get()`

### Integration Points
- `buildcop_common` package currently has only `__init__.py` with `__version__` — ready for new modules
- `buildcop_github` package same — HTTP session factory may land here or in common
- All 5 production modules in `apps/submodule-status/submodule_status/` will eventually import from core (Phase 4), so core API must be designed for that

### Quantified Scope
- 11 hardcoded constants to centralize (3 duplicated across 3 files)
- 8 dict shapes to formalize as TypedDicts
- 3 print statements to replace with logging
- 8 silent exception handlers to augment with WARNING-level logging
- 3 env var access points to consolidate

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-core-foundations*
*Context gathered: 2026-03-25*
