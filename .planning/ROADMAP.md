# Roadmap: sonic-buildcop

## Overview

Transform a single-purpose submodule-staleness repo into a monorepo with a shared core package. The journey: establish proper Python packaging with uv workspaces, build the core library (config, models, logging, API infrastructure), migrate the existing submodule-status tool to consume core, then add interface stubs for future Azure DevOps and AI provider deliverables.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Monorepo Scaffolding** - uv workspace with core and submodule-status packages
- [ ] **Phase 2: Core Foundations** - Config, data models, and structured logging in core package
- [ ] **Phase 3: Core API Infrastructure** - GitHub auth, retry, rate-limiting, and typed exceptions
- [ ] **Phase 4: Submodule-Status Migration** - Migrate existing tool to core, verify identical output
- [ ] **Phase 5: Future Client Stubs** - Azure DevOps and AI provider protocol interfaces

## Phase Details

### Phase 1: Monorepo Scaffolding
**Goal**: Project has a working uv workspace where core and deliverable packages can be developed and installed independently
**Depends on**: Nothing (first phase)
**Requirements**: PKG-01, PKG-02, PKG-03
**Success Criteria** (what must be TRUE):
  1. `uv sync` succeeds from the repo root, resolving all workspace member dependencies
  2. Core package is installable via `uv pip install -e ./core` and importable in Python
  3. Submodule-status package declares a dependency on core in its own `pyproject.toml`
  4. Directory structure follows monorepo layout: root workspace config, `core/` with src-layout, `submodule-status/` as deliverable
**Plans:** 1 plan

Plans:
- [x] 01-01-PLAN.md — Workspace infrastructure + atomic source/test migration to src-layout

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
**Plans**: TBD

Plans:
- [ ] 02-01: TBD

### Phase 3: Core API Infrastructure
**Goal**: Core package provides production-ready GitHub API session management with auth, retry, rate-limit handling, and typed exceptions
**Depends on**: Phase 2
**Requirements**: API-01, API-02, API-03, API-04
**Success Criteria** (what must be TRUE):
  1. GitHub session factory creates authenticated sessions and raises `AuthenticationError` on missing or invalid tokens
  2. API calls automatically retry with exponential backoff on transient failures (5xx, network errors)
  3. Rate-limited responses (403/429) are detected via `X-RateLimit-*` headers and handled with `RateLimitError`
  4. All API failures raise typed exceptions (`APIError`, `RateLimitError`, `AuthenticationError`) — no generic `Exception` or raw status codes
**Plans**: TBD

Plans:
- [ ] 03-01: TBD

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
**Plans**: TBD

Plans:
- [ ] 04-01: TBD

### Phase 5: Future Client Stubs
**Goal**: Core package defines extensible protocol interfaces for Azure DevOps and AI providers that future deliverables can implement
**Depends on**: Phase 2
**Requirements**: STB-01, STB-02
**Success Criteria** (what must be TRUE):
  1. An Azure DevOps client protocol/ABC exists in core with method signatures for pipeline interaction
  2. An AI provider client protocol/ABC exists in core with method signatures for provider integration
  3. Both stubs are importable and subclassable without requiring any external dependencies (azure-devops, etc.)
**Plans**: TBD

Plans:
- [ ] 05-01: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5
(Phase 5 depends only on Phase 2, but executes last since migration validation in Phase 4 is higher priority)

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Monorepo Scaffolding | 1/1 | Complete | 2026-03-25 |
| 2. Core Foundations | 0/? | Not started | - |
| 3. Core API Infrastructure | 0/? | Not started | - |
| 4. Submodule-Status Migration | 0/? | Not started | - |
| 5. Future Client Stubs | 0/? | Not started | - |
