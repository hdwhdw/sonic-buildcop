# Requirements: sonic-buildcop

**Defined:** 2026-03-25
**Core Value:** An extensible repo structure where adding a new tool/dashboard requires only writing deliverable-specific logic, not re-implementing API plumbing.

## v1 Requirements

Requirements for the monorepo refactoring. Each maps to roadmap phases.

### Packaging

- [x] **PKG-01**: Monorepo uses uv workspaces with root `pyproject.toml` and per-package `pyproject.toml` files
- [x] **PKG-02**: Core package (`sonic-buildcop-core`) installable with `uv pip install -e ./core`
- [x] **PKG-03**: Submodule-status package depends on core, uses src-layout
- [ ] **PKG-04**: All `sys.path.insert` hacks removed — proper package imports throughout

### Configuration

- [x] **CFG-01**: Centralized constants module (`API_BASE`, `PARENT_OWNER`, `PARENT_REPO`) — single source of truth
- [x] **CFG-02**: Env-var-based config helper with typed defaults (`core.config.get()`)
- [x] **CFG-03**: Request timeout defaults on all HTTP sessions (30s connect, 60s read)

### Logging

- [x] **LOG-01**: Structured logging via Python `logging` stdlib replacing all bare `print()` statements
- [x] **LOG-02**: Caught exceptions logged at WARNING level (no more silent `None` returns)

### API Infrastructure

- [x] **API-01**: GitHub auth & session factory with token validation and proper error on missing token
- [x] **API-02**: Reusable retry decorator with exponential backoff (extracted from `collect_submodule`)
- [x] **API-03**: Rate-limit-aware request handling — read `X-RateLimit-*` headers, handle 403/429 specifically
- [x] **API-04**: Custom exception types: `APIError`, `RateLimitError`, `AuthenticationError`

### Data Models

- [x] **MDL-01**: Typed dataclasses for cross-module types (`SubmoduleInfo`, `StalenessResult`, `PRInfo`)

### Migration

- [x] **MIG-01**: Submodule-status collector, staleness, and enrichment modules import from core
- [x] **MIG-02**: All existing tests pass with adapted imports (same assertions, new import paths)
- [ ] **MIG-03**: GitHub Actions workflow updated for new directory structure (uv-based)
- [ ] **MIG-04**: Dashboard output identical to pre-migration

### Future Client Stubs

- [ ] **STB-01**: Azure DevOps client stub interface in core (protocol/ABC, no implementation)
- [ ] **STB-02**: AI provider client stub interface in core (protocol/ABC, no implementation)

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### GitHub Client Upgrade

- **GH-01**: Replace raw `requests` with PyGithub typed client in core
- **GH-02**: Core GitHub client wrapper that configures PyGithub with auth, retry, logging

### Performance

- **PERF-01**: Response caching layer for slow-changing data (`.gitmodules`, bump history)
- **PERF-02**: Adaptive rate-limit delays using header-based throttling

### Developer Experience

- **DX-01**: Shared test utilities extracted to core (`mock_github_response`, `create_test_session`)
- **DX-02**: Health check / diagnostic mode for API connectivity validation
- **DX-03**: CLI argument parsing helpers in core config

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Abstract API client base class | GitHub, Azure, AI APIs have different shapes — generic interface loses type info |
| Async/concurrent API calls in core | Out of scope per PROJECT.md; current workload doesn't justify complexity |
| Database / persistent state | Stateless pipeline model is fine for 4-hour cron cadence |
| Plugin/extension system | 2-3 planned deliverables doesn't justify registry/discovery overhead |
| Webhook / real-time event handling | Batch pipeline architecture, not a real-time service |
| ORM-like query builder for GitHub | PyGithub already provides Pythonic access; custom builder adds no value |
| Global config file (YAML/TOML) | Env vars are CI-native; config file adds deployment artifact to manage |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| PKG-01 | Phase 1: Monorepo Scaffolding | Complete |
| PKG-02 | Phase 1: Monorepo Scaffolding | Complete |
| PKG-03 | Phase 1: Monorepo Scaffolding | Complete |
| PKG-04 | Phase 4: Submodule-Status Migration | Pending |
| CFG-01 | Phase 2: Core Foundations | Complete |
| CFG-02 | Phase 2: Core Foundations | Complete |
| CFG-03 | Phase 2: Core Foundations | Complete |
| LOG-01 | Phase 2: Core Foundations | Complete |
| LOG-02 | Phase 2: Core Foundations | Complete |
| API-01 | Phase 3: Core API Infrastructure | Complete |
| API-02 | Phase 3: Core API Infrastructure | Complete |
| API-03 | Phase 3: Core API Infrastructure | Complete |
| API-04 | Phase 3: Core API Infrastructure | Complete |
| MDL-01 | Phase 2: Core Foundations | Complete |
| MIG-01 | Phase 4: Submodule-Status Migration | Complete |
| MIG-02 | Phase 4: Submodule-Status Migration | Complete |
| MIG-03 | Phase 4: Submodule-Status Migration | Pending |
| MIG-04 | Phase 4: Submodule-Status Migration | Pending |
| STB-01 | Phase 5: Future Client Stubs | Pending |
| STB-02 | Phase 5: Future Client Stubs | Pending |

**Coverage:**
- v1 requirements: 20 total
- Mapped to phases: 20 ✓
- Unmapped: 0

---
*Requirements defined: 2026-03-25*
*Last updated: 2026-03-25 after roadmap creation*
