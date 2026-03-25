---
phase: 04
slug: submodule-status-migration
status: draft
nyquist_compliant: false
wave_0_complete: true
created: 2026-03-25
---

# Phase 04 — Validation Strategy

> Migration phase — existing 122 tests serve as the primary validation. All must pass with identical assertions after migration.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` at repo root |
| **Quick run command** | `uv run pytest apps/submodule-status/tests/ -x -q` |
| **Full suite command** | `uv run pytest -x -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest apps/submodule-status/tests/ -x -q`
- **After every plan wave:** Run `uv run pytest -x -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | MIG-01 | regression | `uv run pytest apps/submodule-status/tests/ -x -q` | ✅ existing | ⬜ pending |
| 04-01-02 | 01 | 1 | MIG-02 | regression | `uv run pytest apps/submodule-status/tests/ -x -q` | ✅ existing | ⬜ pending |
| 04-01-03 | 01 | 1 | MIG-03 | grep | `grep -r "sys.path.insert" apps/ libs/` | N/A | ⬜ pending |
| 04-01-04 | 01 | 1 | MIG-04 | diff | Manual: compare dashboard HTML output | N/A | ⬜ pending |
| 04-01-05 | 01 | 1 | PKG-04 | grep | `grep -r "sys.path.insert" . --include="*.py"` | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements — 122 tests already exist.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Dashboard HTML identical | MIG-04 | Requires running with real/fixture data | Generate with fixtures, diff against pre-migration snapshot |
| GitHub Actions workflow | MIG-03 | CI environment required | Push branch, verify workflow passes |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
