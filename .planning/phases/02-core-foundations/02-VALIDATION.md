---
phase: 02
slug: core-foundations
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest ≥8.0 (installed) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` at repo root |
| **Quick run command** | `uv run pytest libs/buildcop-common/tests/ -x -q` |
| **Full suite command** | `uv run pytest -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest libs/buildcop-common/tests/ -x -q`
- **After every plan wave:** Run `uv run pytest -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | CFG-01 | unit | `uv run pytest libs/buildcop-common/tests/test_config.py::test_constants_accessible -x` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | CFG-01 | unit | `uv run pytest libs/buildcop-common/tests/test_config.py::test_constants_values -x` | ❌ W0 | ⬜ pending |
| 02-01-03 | 01 | 1 | CFG-02 | unit | `uv run pytest libs/buildcop-common/tests/test_config.py::test_get_with_default -x` | ❌ W0 | ⬜ pending |
| 02-01-04 | 01 | 1 | CFG-02 | unit | `uv run pytest libs/buildcop-common/tests/test_config.py::test_get_missing_required -x` | ❌ W0 | ⬜ pending |
| 02-01-05 | 01 | 1 | CFG-02 | unit | `uv run pytest libs/buildcop-common/tests/test_config.py::test_get_type_coercion -x` | ❌ W0 | ⬜ pending |
| 02-01-06 | 01 | 1 | CFG-03 | unit | `uv run pytest libs/buildcop-common/tests/test_http.py::test_session_timeout -x` | ❌ W0 | ⬜ pending |
| 02-01-07 | 01 | 1 | CFG-03 | unit | `uv run pytest libs/buildcop-common/tests/test_http.py::test_timeout_override -x` | ❌ W0 | ⬜ pending |
| 02-01-08 | 01 | 1 | LOG-01 | unit | `uv run pytest libs/buildcop-common/tests/test_log.py::test_setup_logging -x` | ❌ W0 | ⬜ pending |
| 02-01-09 | 01 | 1 | LOG-01 | unit | `uv run pytest libs/buildcop-common/tests/test_log.py::test_log_format -x` | ❌ W0 | ⬜ pending |
| 02-01-10 | 01 | 1 | LOG-02 | unit | `uv run pytest libs/buildcop-common/tests/test_log.py::test_module_logger -x` | ❌ W0 | ⬜ pending |
| 02-01-11 | 01 | 1 | MDL-01 | unit | `uv run pytest libs/buildcop-common/tests/test_models.py::test_typeddict_import -x` | ❌ W0 | ⬜ pending |
| 02-01-12 | 01 | 1 | MDL-01 | unit | `uv run pytest libs/buildcop-common/tests/test_models.py::test_progressive_construction -x` | ❌ W0 | ⬜ pending |
| 02-01-13 | 01 | 1 | MDL-01 | unit | `uv run pytest libs/buildcop-common/tests/test_models.py::test_nested_typedicts -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `libs/buildcop-common/tests/` — test directory creation
- [ ] `libs/buildcop-common/tests/__init__.py` — package marker
- [ ] `libs/buildcop-common/tests/test_config.py` — stubs for CFG-01, CFG-02
- [ ] `libs/buildcop-common/tests/test_http.py` — stubs for CFG-03
- [ ] `libs/buildcop-common/tests/test_log.py` — stubs for LOG-01, LOG-02
- [ ] `libs/buildcop-common/tests/test_models.py` — stubs for MDL-01
- [ ] `requests` dependency addition to `libs/buildcop-common/pyproject.toml`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Existing 122 tests unchanged | Regression | Phase 2 only adds modules | Run `uv run pytest apps/ -q` and verify same count |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
