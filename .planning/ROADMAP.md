# Roadmap: sonic-buildcop

## Overview

Transform a single-purpose submodule-staleness repo into a monorepo with a shared core package. The journey: establish proper Python packaging with uv workspaces, build the core library (config, models, logging, API infrastructure), migrate the existing submodule-status tool to consume core, then add interface stubs for future Azure DevOps and AI provider deliverables.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Monorepo Scaffolding** - uv workspace with libs/apps flat layout (RE-PLAN) (completed 2026-03-25)
- [x] **Phase 2: Core Foundations** - Config, data models, and structured logging in core package (completed 2026-03-25)
- [x] **Phase 3: Core API Infrastructure** - GitHub auth, retry, rate-limiting, and typed exceptions (completed 2026-03-25)
- [x] **Phase 4: Submodule-Status Migration** - Migrate existing tool to core, verify identical output (completed 2026-03-25)
- [~] **Phase 5: Future Client Stubs** - ~~Azure DevOps and AI provider protocol interfaces~~ (DROPPED — YAGNI; no concrete consumers exist yet)

## Phase Details

### Phase 1: Monorepo Scaffolding (REVISED — libs/apps flat layout)
**Goal**: Project has a working uv workspace with libs/apps grouping where buildcop-common, buildcop-github, and submodule-status packages can be developed and installed independently
**Depends on**: Nothing (first phase)
**Requirements**: PKG-01, PKG-02, PKG-03
**Success Criteria** (what must be TRUE):
  1. `uv sync` succeeds from the repo root, resolving all workspace member dependencies
  2. Library packages (`buildcop-common`, `buildcop-github`) installable and importable in Python
  3. Submodule-status package depends on buildcop-common in its `pyproject.toml`
  4. Directory structure follows libs/apps layout: `libs/buildcop-common/`, `libs/buildcop-github/`, `apps/submodule-status/`
  5. All 122 existing tests pass with updated import paths
**Plans:** 1/1 plans complete

Plans:
- [ ] 01-01-PLAN.md — Workspace infrastructure + atomic source/test migration to flat layout

### Phase 2: Core Foundations
**Goal**: Core package provides centralized configuration, typed data models, and structured logging that any deliverable can import
**Depends on**: Phase 1
**Requirements**: CFG-01, CFG-02, CFG-03, LOG-01, LOG-02, MDL-01
**Success Criteria** (what must be TRUE):
  1. A single import from core provides all project constants (`API_BASE`, `PARENT_OWNER`, `PARENT_REPO`) — no duplicated values across modules
  2. Environment variable config helper loads typed values with fallback defaults (e.g., `get("TIMEOUT", int, 30)`)
  3. HTTP sessions created through core have timeout defaults applied (30s connect, 60s read)
  4. Core modules use structured `logging` with caught exceptions logged at WARNING — no bare `print()` or silent `None` returns in core
  5. Typed dataclasses (`SubmoduleInfo`, `StalenessResult`, `PRInfo`) are importable from core and pass type-checker validation
**Plans:** 2/2 plans complete

Plans:
- [ ] 02-01-PLAN.md — Config & data models (constants, env var helper, TypedDicts)
- [ ] 02-02-PLAN.md — Logging, HTTP session & package wiring (setup_logging, TimeoutHTTPAdapter, __init__.py re-exports)

### Phase 3: Core API Infrastructure
**Goal**: Core package provides production-ready GitHub API session management with auth, retry, rate-limit handling, and typed exceptions
**Depends on**: Phase 2
**Requirements**: API-01, API-02, API-03, API-04
**Success Criteria** (what must be TRUE):
  1. GitHub session factory creates authenticated sessions and raises `AuthenticationError` on missing or invalid tokens
  2. API calls automatically retry with exponential backoff on transient failures (5xx, network errors)
  3. Rate-limited responses (403/429) are detected via `X-RateLimit-*` headers and handled with `RateLimitError`
  4. All API failures raise typed exceptions (`APIError`, `RateLimitError`, `AuthenticationError`) — no generic `Exception` or raw status codes
**Plans:** 1 plan

Plans:
- [ ] 03-01-PLAN.md — Typed exception hierarchy + GitHub session factory, check_response, retry decorator, __init__.py re-exports

### Phase 4: Submodule-Status Migration
**Goal**: Existing submodule-status tool runs entirely on core package infrastructure with identical output and zero legacy hacks
**Depends on**: Phase 3
**Requirements**: MIG-01, MIG-02, MIG-03, MIG-04, PKG-04
**Success Criteria** (what must be TRUE):
  1. Submodule-status collector, staleness, and enrichment modules import all API, config, model, and logging functionality from core — no local duplicates
  2. All existing tests pass with updated import paths (same assertions, same expected output)
  3. GitHub Actions workflow runs successfully with uv-based setup and updated directory paths
  4. Generated dashboard HTML is identical to pre-migration output for the same input data
  5. Zero `sys.path.insert` calls remain anywhere in the codebase
**Plans:** 3 plans

Plans:
- [ ] 04-01-PLAN.md — Migrate staleness.py + enrichment.py to core (constants, check_response, typed exceptions, logging)
- [ ] 04-02-PLAN.md — Migrate collector.py + renderer.py to core (session factory, retry, env vars, logging)
- [ ] 04-03-PLAN.md — Update GitHub Actions workflow + final migration verification

### Phase 5: Future Client Stubs (DROPPED)
**Status:** Dropped — YAGNI. No ADO or AI consumers exist in the codebase; designing protocol interfaces without concrete use cases leads to wrong abstractions. When a real ADO or AI tool is built, the correct interface will emerge from the concrete work.
**Requirements**: STB-01, STB-02 (deferred to future milestone)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5
(Phase 5 depends only on Phase 2, but executes last since migration validation in Phase 4 is higher priority)

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Monorepo Scaffolding | 1/1 | Complete   | 2026-03-25 |
| 2. Core Foundations | 2/2 | Complete   | 2026-03-25 |
| 3. Core API Infrastructure | 1/1 | Complete   | 2026-03-25 |
| 4. Submodule-Status Migration | 3/3 | Complete   | 2026-03-25 |
| 5. Future Client Stubs | — | Dropped | — |
