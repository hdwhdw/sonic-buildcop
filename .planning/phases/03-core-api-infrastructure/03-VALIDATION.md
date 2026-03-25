---
phase: 03
slug: core-api-infrastructure
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 03 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest libs/buildcop-common/tests/ -x -q` |
| **Full suite command** | `uv run pytest -x -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest libs/buildcop-common/tests/ -x -q`
- **After every plan wave:** Run `uv run pytest -x -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | API-04 | unit | `uv run pytest libs/buildcop-common/tests/test_exceptions.py -x` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 1 | API-04 | unit | `uv run pytest libs/buildcop-common/tests/test_exceptions.py::test_rate_limit_error_attributes -x` | ❌ W0 | ⬜ pending |
| 03-01-03 | 01 | 1 | API-04 | unit | `uv run pytest libs/buildcop-common/tests/test_exceptions.py::test_api_error_attributes -x` | ❌ W0 | ⬜ pending |
| 03-01-04 | 01 | 1 | API-01 | unit | `uv run pytest libs/buildcop-common/tests/test_github.py::test_create_github_session_explicit_token -x` | ❌ W0 | ⬜ pending |
| 03-01-05 | 01 | 1 | API-01 | unit | `uv run pytest libs/buildcop-common/tests/test_github.py::test_create_github_session_missing_token -x` | ❌ W0 | ⬜ pending |
| 03-01-06 | 01 | 1 | API-02 | unit | `uv run pytest libs/buildcop-common/tests/test_github.py::test_retry_on_transient_error -x` | ❌ W0 | ⬜ pending |
| 03-01-07 | 01 | 1 | API-02 | unit | `uv run pytest libs/buildcop-common/tests/test_github.py::test_retry_exhaustion -x` | ❌ W0 | ⬜ pending |
| 03-01-08 | 01 | 1 | API-03 | unit | `uv run pytest libs/buildcop-common/tests/test_github.py::test_check_response_429_rate_limit -x` | ❌ W0 | ⬜ pending |
| 03-01-09 | 01 | 1 | API-03 | unit | `uv run pytest libs/buildcop-common/tests/test_github.py::test_check_response_403_rate_limit -x` | ❌ W0 | ⬜ pending |
| 03-01-10 | 01 | 1 | API-03 | unit | `uv run pytest libs/buildcop-common/tests/test_github.py::test_check_response_403_not_rate_limit -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `libs/buildcop-common/tests/test_exceptions.py` — stubs for API-04
- [ ] `libs/buildcop-common/tests/test_github.py` — stubs for API-01, API-02, API-03

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Existing 145 tests unchanged | Regression | Phase 3 only adds modules | Run `uv run pytest -x -q` and verify same count + new |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
