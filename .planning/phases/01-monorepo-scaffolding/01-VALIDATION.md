---
phase: 1
slug: monorepo-scaffolding
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest ≥8.0 |
| **Config file** | None currently — will add `[tool.pytest.ini_options]` in root `pyproject.toml` |
| **Quick run command** | `uv run pytest submodule-status/tests/ -x` |
| **Full suite command** | `uv run pytest submodule-status/tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest submodule-status/tests/ -x`
- **After every plan wave:** Run `uv run pytest submodule-status/tests/ -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | PKG-01 | smoke | `cd . && uv sync && echo "PASS"` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | PKG-02 | smoke | `uv run python -c "from sonic_buildcop_core import __version__; print(__version__)"` | ❌ W0 | ⬜ pending |
| 01-01-03 | 01 | 1 | PKG-03 | smoke | `uv run python -c "import sonic_submodule_status"` | ❌ W0 | ⬜ pending |
| 01-01-04 | 01 | 1 | PKG-03 | smoke | `uv run python -c "from sonic_submodule_status.collector import main"` | ❌ W0 | ⬜ pending |
| 01-01-05 | 01 | 1 | (implicit) | regression | `uv run pytest submodule-status/tests/ -v` | ✅ existing | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] Root `pyproject.toml` — workspace configuration
- [ ] `core/pyproject.toml` — core package build configuration
- [ ] `submodule-status/pyproject.toml` — deliverable build configuration
- [ ] `uv sync` — creates virtual env and installs all packages

---
*Created: 2026-03-25*
