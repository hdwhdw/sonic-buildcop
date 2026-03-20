---
phase: 1
slug: data-pipeline-deployment
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-20
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | none — Wave 0 installs |
| **Quick run command** | `python -m pytest tests/ -x -q` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | DATA-01 | unit | `pytest tests/test_collector.py -k submodule_list` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | DATA-05 | unit | `pytest tests/test_collector.py -k default_branch` | ❌ W0 | ⬜ pending |
| 01-01-03 | 01 | 1 | DATA-06 | unit | `pytest tests/test_collector.py -k gitmodules_parse` | ❌ W0 | ⬜ pending |
| 01-01-04 | 01 | 1 | DATA-02 | unit | `pytest tests/test_collector.py -k commits_behind` | ❌ W0 | ⬜ pending |
| 01-01-05 | 01 | 1 | DATA-03 | unit | `pytest tests/test_collector.py -k days_behind` | ❌ W0 | ⬜ pending |
| 01-01-06 | 01 | 1 | DATA-04 | unit | `pytest tests/test_collector.py -k compare_link` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 1 | UI-06 | integration | `pytest tests/test_renderer.py -k html_output` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 2 | CICD-01 | manual | Verify cron schedule in workflow YAML | N/A | ⬜ pending |
| 01-03-02 | 03 | 2 | CICD-04 | unit | `pytest tests/test_collector.py -k error_handling` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_collector.py` — stubs for DATA-01 through DATA-06, CICD-04
- [ ] `tests/test_renderer.py` — stubs for UI-06
- [ ] `tests/conftest.py` — shared fixtures (mock API responses)
- [ ] `pip install pytest` — test framework setup

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Daily cron runs | CICD-01 | Requires waiting for scheduled trigger | Check Actions tab after 24h |
| Manual dispatch works | CICD-05 | Requires clicking "Run workflow" button | Trigger via Actions UI, verify run starts |
| Pages deployment | CICD-02 | Requires GitHub Pages configuration | Visit deployed URL after workflow completes |
| Free tier compliance | CICD-03 | Observational — no automated check | Verify ~64 API calls per run in workflow logs |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
