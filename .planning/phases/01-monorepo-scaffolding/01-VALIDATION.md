---
phase: 01
slug: monorepo-scaffolding
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest ≥8.0 |
| **Config file** | Root `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest apps/submodule-status/tests/ -x` |
| **Full suite command** | `uv run pytest -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest apps/submodule-status/tests/ -x`
- **After every plan wave:** Run `uv run pytest -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | PKG-01 | smoke | `uv sync && uv run python -c "import buildcop_common; import buildcop_github; import submodule_status"` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | PKG-02 | smoke | `uv run python -c "import buildcop_common; import buildcop_github"` | ❌ W0 | ⬜ pending |
| 01-01-03 | 01 | 1 | PKG-03 | unit | `uv run pytest apps/submodule-status/tests/ -x` | ✅ (migrated) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] Root `pyproject.toml` with pytest config — covers test discovery
- [ ] `uv sync` must succeed — proves workspace wiring (PKG-01, PKG-02)
- [ ] All 122 existing tests pass after migration (PKG-03)

*Existing infrastructure covers all phase requirements after migration.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| None | — | — | — |

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have automated verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
