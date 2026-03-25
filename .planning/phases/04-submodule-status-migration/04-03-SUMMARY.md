---
phase: 04-submodule-status-migration
plan: 03
subsystem: ci-workflow
tags: [github-actions, uv, migration-verification, ci]
dependency_graph:
  requires: [04-01, 04-02]
  provides: [mig-03-ci-updated, mig-04-dashboard-verified, pkg-04-verified]
  affects: [".github/workflows/update-dashboard.yml"]
tech_stack:
  added: [astral-sh/setup-uv@v5]
  patterns: [uv-sync-ci, entry-point-invocation]
key_files:
  created: []
  modified: [".github/workflows/update-dashboard.yml"]
decisions:
  - Replaced setup-python + pip with astral-sh/setup-uv + uv sync for CI
  - Entry points (collect-submodules, render-dashboard) replace direct python scripts/ invocation
  - Artifact path changed from submodule-status/site to site (monorepo root)
metrics:
  duration: 2min
  completed: "2026-03-25T18:49:00Z"
---

# Phase 04 Plan 03: GitHub Actions Workflow Update + Final Migration Verification Summary

Updated GitHub Actions CI workflow from pip/setup-python to uv/setup-uv with entry-point invocation, then verified all 5 migration requirements (MIG-01–04, PKG-04) pass with zero legacy patterns remaining.

## What Was Done

### Task 1: Update GitHub Actions workflow for uv-based monorepo
- **Commit:** `debd0c5`
- Replaced `actions/setup-python@v5` with `astral-sh/setup-uv@v5`
- Replaced `pip install -r requirements.txt` with `uv sync`
- Replaced `python scripts/collector.py` with `uv run collect-submodules` (entry point)
- Replaced `python scripts/renderer.py` with `uv run render-dashboard` (entry point)
- Removed `defaults.run.working-directory: submodule-status`
- Updated artifact upload path from `submodule-status/site` to `site`

### Task 2: Final migration verification sweep (verification-only, no commit)
- **MIG-01**: All 4 production modules (collector, staleness, enrichment, renderer) import from `buildcop_common` ✅
- **MIG-02**: 122 submodule-status tests pass; 171 total tests pass ✅
- **MIG-03**: CI workflow uses `uv sync` (1), `uv run` (2), `astral-sh/setup-uv` (1) ✅
- **MIG-04**: Dashboard `sort_submodules` and `compute_summary` produce correct output ✅
- **PKG-04**: Zero `sys.path.insert` calls in apps/ and libs/ ✅
- **No legacy patterns**: 0 `raise_for_status`, 0 `os.environ.get`, 0 bare `print()` ✅

## Deviations from Plan

None — plan executed exactly as written.

## Verification Results

All acceptance criteria met:
- YAML valid
- No pip/setup-python/python-scripts/working-directory references remain
- uv sync, uv run entry points, astral-sh/setup-uv all present
- Full test suite green (171 passed)
- All 5 migration requirements confirmed

## Decisions Made

1. **astral-sh/setup-uv@v5 with `version: "latest"`** — matches workspace-level uv toolchain; avoids pinning a specific uv version in CI
2. **Entry points over direct script invocation** — `uv run collect-submodules` uses pyproject.toml `[project.scripts]` entries, eliminating path dependencies
3. **Artifact path `site` at root** — since `working-directory` was removed, the output directory is now relative to repo root
