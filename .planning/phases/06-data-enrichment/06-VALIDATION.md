---
phase: 6
slug: data-enrichment
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-21
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | none |
| **Quick run command** | `python -m pytest submodule-status/tests/ -q --tb=short` |
| **Full suite command** | `python -m pytest submodule-status/tests/ -v --tb=short` |
| **Estimated runtime** | ~1 second |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest submodule-status/tests/ -q --tb=short`
- **After every plan completion:** Run full suite with `-v`

## Validation Architecture

Extracted from 06-RESEARCH.md:

### ENRICH-01: Open Bot PR
- Unit test: mock GitHub Search API response, verify open PR fields (url, title, age_days, ci_status) populated
- Unit test: verify null fields when no open PR exists
- Integration: verify JSON schema includes bot_pr_open key

### ENRICH-02: Last Merged Bot PR  
- Unit test: mock merged PR search, verify last_merged_pr fields (url, merged_at) populated
- Unit test: verify null when no merged PR found
- Integration: verify JSON schema includes last_merged_pr key

### ENRICH-03: Latest Repo Commit
- Unit test: mock repo commits API, verify latest_repo_commit fields (url, date) populated
- Integration: verify JSON schema includes latest_repo_commit key

### ENRICH-04: Average Delay
- Unit test: mock pointer bump history, verify average_delay_days computed correctly
- Unit test: verify edge case with zero bumps returns null
- Integration: verify JSON schema includes average_delay_days key
