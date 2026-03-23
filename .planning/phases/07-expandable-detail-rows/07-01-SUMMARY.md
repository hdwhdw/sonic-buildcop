---
phase: 07-expandable-detail-rows
plan: 01
subsystem: dashboard-ui
tags: [expandable-rows, toggle, detail-panel, dark-mode, javascript]
dependency_graph:
  requires: [06-02]
  provides: [expandable-detail-rows, toggle-mechanism, enrichment-display]
  affects: [dashboard.html, test_renderer.py]
tech_stack:
  added: []
  patterns: [vanilla-js-toggle, inline-detail-panel, css-dark-mode-extension]
key_files:
  created: []
  modified:
    - submodule-status/templates/dashboard.html
    - submodule-status/tests/test_renderer.py
decisions:
  - Vanilla JS toggle (~15 lines) instead of <details> element or framework
  - colspan="9" for detail row (8 existing + 1 toggle column)
  - Muted italic placeholder text for null enrichment fields
metrics:
  duration: 187s
  completed: "2026-03-23T18:51:49Z"
  tasks_completed: 2
  tasks_total: 2
  test_count: 60
  test_pass: 60
---

# Phase 07 Plan 01: Expandable Detail Rows Summary

Expandable detail rows with ▶/▼ toggle icons, inline enrichment panels (bot PR, pointer update, repo commit, avg delay), Expand All/Collapse All button, and full dark mode support.

## Tasks Completed

| # | Task | Commit | Key Changes |
|---|------|--------|-------------|
| 1 | Add toggle column, detail rows, CSS, and JS | `940544f` | dashboard.html: toggle column, detail rows, light/dark CSS, vanilla JS |
| 2 | Add tests for expandable detail rows | `6fb7461` | test_renderer.py: _make_sub enrichment params, 14 new tests |

## Changes Made

### Task 1: Template Enhancement
- Added dedicated toggle column (`<th class="toggle-header">`) as first column
- Added ▶ toggle icon in each data row with `onclick="toggleDetail(this)"`
- Added hidden detail row (`display:none`) with `colspan="9"` after each data row
- Detail panel shows: Open Bot PR (link + age + CI status), Last Pointer Update (linked date), Latest Repo Commit (linked date), Avg Update Delay (formatted float)
- All null states use muted italic placeholders: "No open PR", "No merged PR found", "No commit data", "Not enough data"
- CI status rendered with colored indicators: ✓ Pass (green), ✗ Fail (red), ⏳ Pending (yellow)
- Added 38 lines of new CSS for light mode + 14 dark mode rules
- Added `toggleDetail()` and `toggleAll()` vanilla JS functions
- Added Expand All / Collapse All button in header

### Task 2: Test Coverage
- Updated `_make_sub()` helper with 4 optional enrichment params (open_bot_pr, last_merged_bot_pr, latest_repo_commit, avg_delay_days)
- Updated `_make_data()` default dicts with enrichment None fields
- Patched 2 inline dicts in existing tests for compatibility
- Added 14 new tests covering all 5 EXPAND requirements plus structural/dark mode checks

## Deviations from Plan

None — plan executed exactly as written.

## Test Results

```
60 passed in 0.59s (test_renderer.py)
115 passed in 0.70s (full suite)
```

All 46 existing tests pass (no regressions). All 14 new tests pass.

## Requirements Covered

- **EXPAND-01**: Toggle icon, detail rows, expand all button, JS functions
- **EXPAND-02**: Open bot PR link/age/CI status + null state + fail/pending variants
- **EXPAND-03**: Last merged PR link with date
- **EXPAND-04**: Latest repo commit link with date
- **EXPAND-05**: Average delay metric + null state placeholder

## Self-Check: PASSED

All files exist, all commits verified.
