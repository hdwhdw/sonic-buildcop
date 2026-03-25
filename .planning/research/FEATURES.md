# Feature Research

**Domain:** Shared Python core package for monorepo API clients (GitHub, Azure DevOps, AI providers)
**Researched:** 2025-07-17
**Confidence:** HIGH (evidence-driven from existing codebase analysis + established Python ecosystem patterns)

## Feature Landscape

### Table Stakes (Downstream Tools Suffer Without These)

Features that **must** exist in the shared core or every deliverable re-implements them badly. Evidence sourced from the current codebase's tech debt and CONCERNS.md.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Centralized GitHub auth & session management** | Currently `GITHUB_TOKEN` env var handling + session headers are in `collector.py:main()`. Every future deliverable would duplicate this. Empty token → malformed `Authorization: token ` header (CONCERNS.md security issue). | LOW | Wrap in a factory: `create_github_session(token=None)` that validates token presence, warns on empty, sets proper headers. Consider PyGithub's built-in auth instead of raw sessions. |
| **Unified constants / configuration** | `API_BASE`, `PARENT_OWNER`/`REPO_OWNER`, `PARENT_REPO` duplicated across 3 files with naming inconsistencies (CONCERNS.md top debt item). | LOW | Single `core.config` module. Use `PARENT_OWNER` consistently. Support env-var overrides for testability. |
| **Structured logging** | All diagnostic output is bare `print()`. Errors in enrichment `except` blocks produce **zero output** — silently return `None`. CI logs show only the final summary line, not which submodules failed or why (CONCERNS.md missing critical feature). | LOW | Python `logging` stdlib. Configure once in core. Deliverables get a child logger: `logging.getLogger("sonic_buildcop.submodule_status")`. Levels: WARNING for caught exceptions, INFO for pipeline progress, DEBUG for API calls. |
| **Retry with exponential backoff (reusable)** | Only `collect_submodule()` has retry logic. All enrichment functions (`staleness.py`, `enrichment.py`) have no retry — a single transient failure → `None` for that field forever. | MEDIUM | Generic retry decorator/utility. Already proven pattern in `collect_submodule()` (3 retries, `2^attempt` backoff). Extract to `core.retry.with_backoff(retries=3, exceptions=(...))`. Integrate with logging. |
| **Rate-limit-aware request handling** | Current code uses hardcoded `time.sleep(0.5)` scattered in 5 locations. Never checks `X-RateLimit-Remaining` or `X-RateLimit-Reset` headers. 403/429 responses treated same as network errors (CONCERNS.md missing critical feature). | MEDIUM | Read rate-limit headers after each response. Sleep only when approaching limit. Handle 403/429 specifically — wait for reset window instead of retrying blindly. Current 240+ calls/run is well within 5000/hr limit, but future deliverables will increase load. |
| **Proper Python packaging (`pyproject.toml`)** | No `__init__.py`, no packaging at all. Tests use `sys.path.insert()` hacks. IDE tooling and linters can't resolve imports. Cross-module imports break if CWD changes (CONCERNS.md tech debt). | MEDIUM | `core/` as installable package with `pyproject.toml`. Deliverables depend on it via `pip install -e ./core`. Eliminates sys.path hacks, enables proper import resolution, version pinning. |
| **Typed data models (dataclasses/TypedDict)** | All submodule data is plain `dict` with implicit schema. Keys accumulate across pipeline stages with no type safety. Typos in key names are invisible bugs. IDE can't autocomplete. (CONCERNS.md tech debt — "Untyped Dict Structures") | MEDIUM | `@dataclass` or `TypedDict` for shared types like `SubmoduleInfo`, `StalenessResult`, `PRInfo`. Core defines base types; deliverables extend. No need to model everything — start with the types that cross module boundaries. |
| **Common error handling patterns** | Same `except (requests.RequestException, KeyError, ValueError)` tuple copy-pasted across 10+ locations. Inconsistent: some return `[]`, some return `None`, some set fields to `None`. No logging in any of them. | LOW | Define standard exception classes in core: `APIError`, `RateLimitError`, `AuthenticationError`. Provide a `safe_api_call()` helper that catches, logs, and returns a typed result. Don't force it — offer it as a utility. |
| **Request timeout configuration** | `requests.Session` created without any timeout. If GitHub API hangs, process blocks indefinitely until 6-hour Actions timeout (CONCERNS.md dependency risk). | LOW | Set default timeout (30s connect, 60s read) on all sessions. Make configurable but always present. |

### Differentiators (Nice to Have Shared, Reduce Future Effort)

Features that aren't required for the submodule-status migration but pay dividends when building the next deliverable (flake dashboard, flaky test cop, etc.).

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **PyGithub client wrapper** | PROJECT.md targets PyGithub to replace raw `requests`. PyGithub handles pagination, rate-limit awareness, and typed responses natively. Wrapping it in core means deliverables get these for free. | MEDIUM | Don't wrap PyGithub in another abstraction — expose it directly. Core's value is **configuring** it (auth, retry, logging integration), not hiding it. Provide `core.github.create_client() -> Github` that returns a configured PyGithub instance. |
| **Azure DevOps client wrapper** | Future deliverables (flake dashboard, test cop) need Azure Pipelines data. Setting up auth + client config for `azure-devops-python-api` once saves each tool from figuring it out. | MEDIUM | Stub interface now, implement when first deliverable needs it. Same pattern as GitHub: `core.azure.create_client()` that handles PAT auth, org/project config. |
| **AI provider client interface** | PROJECT.md mentions AI provider stubs. A common interface allows swapping providers (OpenAI, Azure OpenAI, local models) without deliverable changes. | LOW (stub) / HIGH (full) | Define a protocol/ABC: `class AIProvider: def complete(prompt, ...) -> str`. Implement concrete providers later. Don't over-engineer — start with the stub. |
| **Response caching layer** | Current pipeline makes 240+ API calls per run with zero caching. `.gitmodules` and bump history change slowly — caching would dramatically reduce API load and wall-clock time (CONCERNS.md perf bottleneck). | MEDIUM | File-based cache with TTL. Cache key = URL + params hash. Good candidates: `.gitmodules` content (changes rarely), bump history (changes ~daily), repo metadata (default branch — nearly static). NOT for: staleness data, PR status (must be fresh). |
| **Shared test utilities** | Current `conftest.py` has mock API response fixtures that any GitHub-related deliverable would need. Mock response builders, session mocking helpers. | LOW | Extract mock helpers to `core.testing`: `mock_github_response()`, `create_test_session()`. Keep deliverable-specific fixtures (sample submodule data) in deliverable test dirs. |
| **CLI argument parsing framework** | Current scripts have no CLI interface — all config via env vars only. Cannot override verbosity, output path, or retry count from command line (CONCERNS.md missing feature). | LOW | Don't pick a CLI framework for core. Instead, provide config helpers that work with both env vars and CLI args. Let each deliverable choose its own CLI (argparse, click, typer). Core provides: `core.config.get(key, env_var=..., default=...)`. |
| **Health check / diagnostic mode** | No way to verify API connectivity, token validity, or rate-limit headroom before running a full pipeline. Useful for CI debugging. | LOW | `core.health.check_github_auth(token) -> AuthStatus` that validates the token, reports rate-limit remaining, and logs the result. Quick sanity check before expensive pipeline runs. |

### Anti-Features (Deliberately NOT in Core)

Features that seem like they belong in shared infrastructure but would actually harm the project.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Abstract "API client" base class hierarchy** | "All clients should share an interface" | GitHub, Azure, and AI APIs have fundamentally different shapes. Forcing them into a common `BaseClient.get()` abstraction hides useful type information, makes debugging harder, and adds indirection with zero value. PyGithub already provides a typed client — wrapping it in a generic interface loses its advantages. | Configure each client type independently. Shared code is auth/logging/retry patterns, not a polymorphic client interface. |
| **ORM-like query builder for GitHub** | "Make GitHub API calls more Pythonic" | The team is replacing raw `requests` with PyGithub, which already provides Pythonic access (`repo.get_commits(path=...)` etc.). A custom query builder on top adds maintenance burden and learning curve for no gain. | Use PyGithub's native API directly. Document common query patterns in a cookbook, not a wrapper. |
| **Async/concurrent API calls in core** | "Speed up 240+ API calls" | PROJECT.md explicitly says out of scope. Adding asyncio to core forces deliverables to deal with async patterns. The current workload (4-hour cron, ~3 min runtime) doesn't justify the complexity. | Stick with synchronous. If a future deliverable needs concurrency, it can use `concurrent.futures` locally without forcing core to be async. |
| **Database / persistent state management** | "Cache results between runs" | Current architecture is stateless pipeline → static HTML. Adding DB introduces deployment requirements, schema migration, and operational complexity. The 4-hour cron cadence makes fresh-fetch perfectly viable. | Use simple file-based caching (JSON files with TTL) if any caching is needed. No database. |
| **Event/webhook handling** | "React to GitHub events in real-time" | This is a batch pipeline system, not a real-time service. Adding webhook handling requires a running server, authentication, and operational monitoring — a completely different architecture. | Keep the cron-based pipeline model. If real-time is ever needed, build it as a separate service, not core library feature. |
| **Deliverable-specific business logic in core** | "The staleness threshold computation is reusable" | Cadence-based staleness thresholds, PR-to-submodule matching, dashboard rendering — these are submodule-status domain logic. Putting them in core couples all deliverables to one tool's concepts. | Core provides API clients + infrastructure patterns. Each deliverable owns its domain logic entirely. The test is: "Would the flake dashboard need this?" If no, it's not core. |
| **Plugin/extension system** | "Make it easy to add new deliverables" | With only 2-3 planned deliverables, a plugin system is premature abstraction. It adds registry patterns, entry points, and discovery mechanisms that cost more to maintain than they save. | New deliverable = new directory with its own `main()`. Imports from `core` package. No registration, no discovery, no plugins. |
| **Global config file (YAML/TOML)** | "Centralize all configuration" | Multiple config sources (env vars, config file, CLI args) create confusion about precedence. The CI pipeline uses env vars natively. A config file adds a deployment artifact to manage. | Env vars for all config, with sensible defaults. Core provides `core.config.get()` that reads env vars with defaults. Simple, CI-native, no files to deploy. |

## Feature Dependencies

```
[Proper Python Packaging (pyproject.toml)]
    └──enables──> [Centralized Constants/Config]
    └──enables──> [Structured Logging]
    └──enables──> [Typed Data Models]
    └──enables──> [All other core features]

[Centralized GitHub Auth & Session]
    └──enables──> [Rate-Limit-Aware Requests]
    └──enables──> [Request Timeout Config]
    └──enables──> [Retry with Backoff]
                      └──enhances──> [Rate-Limit-Aware Requests]

[Structured Logging]
    └──enhances──> [Retry with Backoff] (log retry attempts)
    └──enhances──> [Rate-Limit-Aware Requests] (log limit status)
    └──enhances──> [Common Error Handling] (log caught exceptions)

[Centralized Constants/Config]
    └──required-by──> [GitHub Auth & Session] (token config)
    └──required-by──> [Azure DevOps Client] (PAT/org config)
    └──required-by──> [AI Provider Interface] (API key config)

[Common Error Handling]
    └──enhances──> [Retry with Backoff]
    └──enhances──> [Rate-Limit-Aware Requests]

[Typed Data Models]
    └──enhances──> [Common Error Handling] (typed error results)

[PyGithub Client Wrapper] ──conflicts──> [Abstract API Client Base Class]
    (PyGithub IS the typed client — don't wrap it in another abstraction)

[Response Caching] ──requires──> [Centralized GitHub Auth & Session]
    (needs to intercept/wrap API calls)
```

### Dependency Notes

- **Packaging enables everything:** Without `pyproject.toml` and proper `core/` package structure, nothing else can be imported. This is phase 1, non-negotiable.
- **Config enables auth, auth enables rate limiting:** Natural dependency chain. Build config first, then auth on top, then rate-limit-aware requests on top of that.
- **Logging enhances everything:** Not a hard dependency for anything, but every other feature is better with structured logging. Add early so retry, rate-limit, and error handling all log from the start.
- **PyGithub conflicts with abstract base class:** These are mutually exclusive approaches. PyGithub provides the typed, pagination-aware client. Building an abstract base class on top is anti-pattern — it hides PyGithub's strengths.
- **Caching is independent but requires auth:** Can be added later without changing other features. Depends on having a centralized session/client to intercept.

## MVP Definition

### Phase 1: Packaging + Foundation (v0.1)

Minimum to unblock the submodule-status migration without breaking existing behavior.

- [x] `pyproject.toml` for core package with proper `__init__.py` — **eliminates sys.path hacks, enables editable install**
- [x] `core.config` module with centralized constants (`API_BASE`, `PARENT_OWNER`, `PARENT_REPO`) — **fixes the #1 tech debt item (duplicated constants)**
- [x] `core.config.get()` helper for env-var-based config with defaults — **replaces scattered `os.environ.get()` calls**
- [x] `core.logging` setup with Python `logging` stdlib — **replaces bare `print()`, makes caught exceptions visible**
- [x] Request timeout defaults on sessions — **fixes the hanging request risk**

### Phase 2: API Infrastructure (v0.2)

Make the GitHub client robust and reusable. This is where the real shared value lives.

- [ ] `core.github.create_session()` with validated auth, proper headers, timeout — **consolidates session creation from collector.py main()**
- [ ] `core.retry.with_backoff()` decorator/utility — **extracts pattern from collect_submodule(), makes it available to all enrichment functions**
- [ ] `core.ratelimit` module that reads `X-RateLimit-*` headers, handles 403/429 — **fixes the #2 missing critical feature**
- [ ] `core.errors` with `APIError`, `RateLimitError`, `AuthenticationError` — **replaces the broad except tuple copy-pasted everywhere**
- [ ] Typed data models for cross-boundary types (`SubmoduleInfo`, `StalenessResult`) — **replaces untyped dicts at module boundaries**

### Phase 3: Migration + Verification (v0.3)

Migrate submodule-status to use the core package. Prove the architecture works.

- [ ] Migrate `collector.py` to import from `core` (config, auth, retry) — **first consumer validates the core API**
- [ ] Migrate `staleness.py` and `enrichment.py` to use core retry + error handling — **enrichment functions get retry for free**
- [ ] All existing tests pass with adapted imports — **backward compatibility proven**
- [ ] GitHub Actions workflow updated for new directory structure — **deployment still works**

### Future Consideration (v1.0+)

Features to add when the next deliverable (flake dashboard) is started.

- [ ] PyGithub integration — **defer until submodule-status migration is stable; raw requests → PyGithub is a separate, larger change**
- [ ] Azure DevOps client wrapper — **no consumer exists yet; build when flake dashboard starts**
- [ ] AI provider interface stubs — **no consumer exists yet; design when requirements are clear**
- [ ] Response caching — **optimization; current performance is acceptable for 4-hour cron**
- [ ] Shared test utilities — **extract when second deliverable duplicates test patterns**
- [ ] Health check / diagnostic mode — **nice-to-have; add when CI debugging becomes painful**

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority | Phase |
|---------|------------|---------------------|----------|-------|
| Python packaging (pyproject.toml) | HIGH | LOW | **P1** | 1 |
| Centralized config/constants | HIGH | LOW | **P1** | 1 |
| Structured logging | HIGH | LOW | **P1** | 1 |
| Request timeout defaults | HIGH | LOW | **P1** | 1 |
| GitHub auth & session factory | HIGH | LOW | **P1** | 2 |
| Reusable retry with backoff | HIGH | MEDIUM | **P1** | 2 |
| Rate-limit-aware requests | HIGH | MEDIUM | **P1** | 2 |
| Common error types | MEDIUM | LOW | **P1** | 2 |
| Typed data models (core types) | MEDIUM | MEDIUM | **P2** | 2 |
| Submodule-status migration | HIGH | MEDIUM | **P1** | 3 |
| PyGithub integration | MEDIUM | HIGH | **P3** | Future |
| Azure DevOps client | MEDIUM | MEDIUM | **P3** | Future |
| AI provider interface | LOW | LOW (stub) | **P3** | Future |
| Response caching | MEDIUM | MEDIUM | **P3** | Future |
| Shared test utilities | LOW | LOW | **P3** | Future |
| CLI framework in core | LOW | LOW | **P3** | Never (let deliverables choose) |

**Priority key:**
- P1: Must have — blocks migration or fixes critical tech debt
- P2: Should have — improves DX and maintainability
- P3: Future — no consumer yet, build when needed

## Existing Pattern Analysis (What to Extract vs Leave)

Analysis of current code to determine what crosses the core/deliverable boundary.

| Current Pattern | Location | Extract to Core? | Rationale |
|----------------|----------|-------------------|-----------|
| `requests.Session` creation + auth headers | `collector.py:main()` L229-233 | **YES** | Every deliverable needs authenticated GitHub sessions |
| `API_BASE` constant | 3 files, duplicated | **YES** | Textbook constant duplication |
| `PARENT_OWNER` / `REPO_OWNER` | 3 files, inconsistent names | **YES** | Fix naming, centralize |
| `PARENT_REPO` constant | 3 files, duplicated | **YES** | Same as above |
| `time.sleep(0.5)` courtesy delays | 5 locations across 3 files | **YES** → replace with rate-limit-aware handler | Scattered sleep is the wrong pattern |
| Retry logic in `collect_submodule()` | `collector.py` L159-222 | **YES** (extract the retry pattern) | The retry logic is generic; the collect logic is specific |
| `(requests.RequestException, KeyError, ValueError)` catch tuple | 10+ locations | **YES** (common error handling) | Same tuple everywhere = extractable pattern |
| `BOT_MAINTAINED` set | `collector.py` L20-37 | **NO** | Submodule-status-specific filter list |
| `BOT_AUTHOR` constant | `enrichment.py` L28 | **NO** | Submodule-status-specific |
| `parse_gitmodules()` | `collector.py` L40-82 | **NO** | Domain logic specific to submodule tracking |
| `compute_cadence()` / `compute_thresholds()` | `staleness.py` | **NO** | Staleness classification is domain logic |
| `match_pr_to_submodule()` | `enrichment.py` L34-48 | **NO** | PR matching is submodule-status-specific |
| `sort_submodules()` / `compute_summary()` | `renderer.py` | **NO** | Dashboard rendering logic |
| `format_relative_time()` | `renderer.py` L42-67 | **MAYBE** | Generic utility, but only one consumer. Extract if second deliverable needs it. |
| `GITHUB_TOKEN` env var handling | `collector.py` L227 | **YES** | Auth config should be in core |
| Jinja2 rendering pattern | `renderer.py` | **NO** | Not all deliverables will render HTML |

## Sources

- **Primary:** Existing codebase analysis — `collector.py`, `staleness.py`, `enrichment.py`, `renderer.py` (direct code review)
- **Primary:** `.planning/codebase/CONCERNS.md` — documented tech debt, security issues, performance bottlenecks, missing features
- **Primary:** `.planning/codebase/ARCHITECTURE.md` — pipeline architecture, data flow, cross-cutting concerns
- **Primary:** `.planning/PROJECT.md` — requirements (validated + active), constraints, key decisions
- **Primary:** `.planning/codebase/STACK.md` — current technology stack, dependency analysis
- **Primary:** `.planning/codebase/CONVENTIONS.md` — coding patterns, naming conventions, error handling patterns
- **Reference:** Python `logging` stdlib — standard approach for structured logging in Python applications (HIGH confidence)
- **Reference:** PyGithub library patterns — typed GitHub API client with built-in pagination and rate limiting (HIGH confidence, well-established library)
- **Reference:** Python packaging with `pyproject.toml` — PEP 517/518/621 standard, editable installs via `pip install -e .` (HIGH confidence, Python standard)

---
*Feature research for: sonic-buildcop shared core package*
*Researched: 2025-07-17*
