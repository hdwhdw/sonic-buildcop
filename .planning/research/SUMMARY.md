# Research Summary: sonic-buildcop Monorepo Refactoring

**Domain:** Python monorepo with shared API client packages
**Researched:** 2026-03-25
**Overall confidence:** HIGH

## Executive Summary

The sonic-buildcop monorepo refactoring has a clear, well-supported technology path. PyGithub 2.9.0 is the dominant Python GitHub client (7.7k stars, released 4 days ago) and provides built-in solutions for every concern in the current codebase: typed return objects replace untyped dicts, `GithubRetry` replaces manual retry loops, automatic rate limiting replaces scattered `time.sleep()` calls, and `PaginatedList` handles pagination the code currently doesn't do. Every raw `requests` call in the existing code maps 1:1 to a PyGithub method — verified by inspecting both the current codebase and the PyGithub 2.9.0 API surface.

For project management, uv (0.11.1) has emerged as the clear 2025/2026 standard for Python packaging. Its native workspace support with `[tool.uv.workspace]` directly solves the monorepo packaging problem — each package gets its own `pyproject.toml`, dependencies resolve across the workspace, and `uv.lock` provides the deterministic lockfile currently missing. The combination of uv (project manager) + hatchling (build backend) is the recommended modern Python stack.

The azure-devops client (7.1.0b4) is the notable risk area: still in beta, depends on deprecated msrest, and hasn't had a release since November 2023. However, it's the only official Microsoft client and covers the future Azure Pipelines interaction needs. The mitigation is to wrap it behind a protocol/interface in the core package so it can be swapped later.

The logging gap (`print()` everywhere, silent exception swallowing) is addressed by structlog, which provides structured key-value logging with stdlib integration and CI-friendly console output. Ruff (0.15.7) replaces the missing linter/formatter configuration in a single tool.

## Key Findings

**Stack:** PyGithub 2.9 + azure-devops 7.1 + uv workspaces + hatchling build + structlog logging + ruff linting
**Architecture:** uv workspace with `packages/core/` shared library + `deliverables/*/` for each tool
**Critical pitfall:** azure-devops depends on deprecated msrest — wrap behind interface for future swapability

## Implications for Roadmap

Based on research, suggested phase structure:

1. **Monorepo scaffolding** — Set up uv workspace, pyproject.toml files, directory structure
   - Addresses: No proper Python packaging, sys.path hacks, unversioned dependencies
   - Avoids: Trying to migrate code AND packaging simultaneously

2. **Core package: GitHub client** — Implement shared PyGithub wrapper with auth, retry, rate-limit
   - Addresses: Duplicated constants, manual auth/retry code, no rate-limit handling
   - Avoids: Premature abstraction — build the GitHub client first since it's used NOW

3. **Migrate submodule-status** — Port existing raw requests code to use core GitHub client
   - Addresses: All current tech debt in one deliverable
   - Avoids: Breaking backward compatibility by running both old and new in parallel during migration

4. **Core package: Azure DevOps stub + logging + tooling** — Add azure-devops wrapper interface, structlog, ruff/mypy configs
   - Addresses: Missing logging, Azure Pipelines future needs
   - Avoids: Blocking the GitHub migration on Azure work

**Phase ordering rationale:**
- Phase 1 must come first — can't migrate code without the packaging foundation
- Phase 2 before 3 — core package must exist before deliverables can depend on it
- Phase 3 before 4 — prove the pattern works with the existing deliverable before adding more infrastructure
- Azure DevOps is deferred because it's future-use only; GitHub is the immediate need

**Research flags for phases:**
- Phase 1: Standard patterns, unlikely to need additional research
- Phase 2: PyGithub migration is well-understood (1:1 mapping verified)
- Phase 3: May need phase-specific research for test migration patterns (responses library mocking)
- Phase 4: azure-devops wrapper design may need research if MS updates the client

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All versions verified via PyPI live queries and installed package inspection |
| Features | HIGH | Feature landscape is well-understood from codebase analysis |
| Architecture | HIGH | uv workspace pattern is well-documented and actively maintained |
| Pitfalls | MEDIUM | azure-devops deprecation risk is real but timeline uncertain |

## Gaps to Address

- Azure DevOps client future: Will Microsoft release a non-msrest version? Monitor `azure-devops` PyPI for releases.
- PyGithub mocking strategy: Need to decide between mocking at the PyGithub object level vs the HTTP level during test migration.
- GitHub Actions `setup-uv` action: Verify `astral-sh/setup-uv@v5` exists and works with uv 0.11.

---

*Research summary: 2026-03-25*
