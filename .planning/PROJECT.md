# sonic-buildcop

## What This Is

A monorepo for SONiC build infrastructure tools — dashboards, bots, and monitors that interact with GitHub, Azure Pipelines, and AI providers. Shared core package provides API clients and common patterns; separate deliverable directories contain tool-specific logic.

## Core Value

An extensible repo structure where adding a new tool/dashboard requires only writing deliverable-specific logic, not re-implementing API plumbing.

## Requirements

### Validated

- ✓ Submodule staleness monitoring with adaptive thresholds — existing
- ✓ Bot PR tracking and CI status aggregation — existing
- ✓ Static HTML dashboard rendering via Jinja2 — existing
- ✓ GitHub Actions scheduled pipeline with GitHub Pages deployment — existing
- ✓ Retry with backoff and graceful degradation on API errors — existing

### Active

- [ ] Shared core Python package with GitHub client (PyGithub), Azure DevOps client (azure-devops-python-api), and AI provider client stubs
- [ ] Proper Python packaging with pyproject.toml — core as installable package, deliverables depend on it
- [ ] Monorepo directory structure: core/ package + deliverable dirs (submodule-status/, future tools)
- [ ] Migrate existing submodule-status from raw requests to shared core GitHub client
- [ ] Shared reusable patterns extracted from current code (auth, rate limiting, config, logging)
- [ ] Existing tests pass after migration — submodule-status produces same output

### Out of Scope

- Building new deliverables (flake dashboard, test cop) — structure only, those come later
- Rewriting the submodule-status business logic — only the API/infra layer changes
- Deploying to anything other than GitHub Pages — keep current deployment model
- Adding async/concurrent API calls — address later per deliverable need

## Context

**Current state:** Single-purpose repo with a submodule-staleness pipeline under `submodule-status/`. All GitHub API interaction is via raw `requests.Session` with inline auth headers. No Python packaging — scripts use `sys.path` hacks for imports. Constants duplicated across 3 modules. No logging framework.

**Tech debt addressed by this refactoring:**
- Duplicated constants (API_BASE, PARENT_OWNER/REPO_OWNER across 3 files)
- No proper Python packaging (no `__init__.py`, no `pyproject.toml`)
- `sys.path.insert` hacks in tests
- Unversioned dependencies in requirements.txt
- No structured logging
- No shared auth/rate-limit handling

**Target libraries:**
- `PyGithub` — typed GitHub API client replacing raw requests
- `azure-devops-python-api` — Azure Pipelines interaction for future deliverables
- AI provider clients — TBD, stub interface for now

## Constraints

- **Backward compatibility**: submodule-status must produce identical dashboard output after migration
- **Python 3.12+**: already the target runtime
- **GitHub Actions**: must continue working as CI/CD — workflow may need path updates
- **Existing tests**: all current tests must pass (adapted for new imports, same assertions)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Monorepo with shared core package | Multiple deliverables need same API clients; avoids duplication | — Pending |
| PyGithub over raw requests | Typed, maintained, handles pagination/rate-limits natively | — Pending |
| azure-devops-python-api for Azure | Official Microsoft client, matches PyGithub pattern | — Pending |
| pyproject.toml packaging | Modern Python standard, fixes sys.path hacks, enables editable installs | — Pending |

---
*Last updated: 2026-03-25 after initialization*
