---
phase: 03-dashboard-ui
plan: 01
subsystem: renderer
tags: [sort, summary, tdd, dashboard]
dependency_graph:
  requires: [renderer.py, data.json schema with staleness_status/days_behind]
  provides: [sort_submodules, compute_summary, sorted render pipeline]
  affects: [render_dashboard, dashboard.html output order]
tech_stack:
  added: []
  patterns: [tiered sort with _TIER_ORDER constant, emoji-count summary string]
key_files:
  created: []
  modified:
    - scripts/renderer.py
    - tests/test_renderer.py
decisions:
  - "_TIER_ORDER dict maps red=0, yellow=1, green=2 for sort priority"
  - "Unavailable/None staleness_status sorts last (tier=3)"
  - "summary_text passed to template.render even before template uses it (Jinja2 ignores extras)"
metrics:
  duration: 2min
  completed: "2026-03-20T20:44:00Z"
  tasks_completed: 2
  tasks_total: 2
  test_count_before: 43
  test_count_after: 52
---

# Phase 03 Plan 01: Sort + Summary Python Logic Summary

**One-liner:** Worst-first sort (red→yellow→green→unknown) and emoji summary (🟢 N · 🟡 N · 🔴 N) wired into render_dashboard pipeline via TDD

## What Was Done

### Task 1: Add sort_submodules and compute_summary with TDD tests

**TDD RED → GREEN cycle:**

- **RED:** Added 8 failing tests to `tests/test_renderer.py` — 5 for sort_submodules (tier ordering, days_behind descending, unavailable last, empty list, no mutation) and 3 for compute_summary (mixed format, excludes unavailable, all green). Confirmed ImportError on import.
- **GREEN:** Implemented `sort_submodules()` and `compute_summary()` in `scripts/renderer.py`. Added `_TIER_ORDER` constant. Wired both into `render_dashboard()` — sorted_subs replaces unsorted submodules, summary_text passed as extra template variable.

**Commits:**
- `2324b51` — test(03-01): add failing tests for sort_submodules and compute_summary
- `7f34023` — feat(03-01): implement sort_submodules and compute_summary in renderer

### Task 2: Integration test — sorted order in rendered HTML

Added `test_render_html_sorted_worst_first` that renders a full dashboard with red, yellow, green, and unavailable submodules, then verifies their positions in the HTML output follow worst-first order.

**Commit:**
- `e4f0cfe` — test(03-01): add integration test for sorted HTML output

## Test Results

- **Before:** 43 tests (14 collector + 9 renderer + 20 staleness)
- **After:** 52 tests (14 collector + 18 renderer + 20 staleness)
- **New tests:** 9 (5 sort + 3 summary + 1 integration)
- **Regressions:** 0

## Deviations from Plan

None — plan executed exactly as written.

## Key Implementation Details

### sort_submodules
- `_TIER_ORDER = {"red": 0, "yellow": 1, "green": 2}` — unknown/None maps to 3
- Sort key: `(tier, -days_behind)` — tier ascending, days descending within tier
- Returns new list via `sorted()` — input never mutated

### compute_summary
- Counts green/yellow/red from `staleness_status` field
- Ignores None (unavailable submodules)
- Returns emoji format: `🟢 N · 🟡 N · 🔴 N`

### render_dashboard wiring
- `sorted_subs = sort_submodules(data["submodules"])` before template.render
- `summary_text = compute_summary(data["submodules"])` passed to template
- Jinja2 silently ignores summary_text until template uses it (Plan 03-02)

## Commits

| # | Hash | Message |
|---|------|---------|
| 1 | 2324b51 | test(03-01): add failing tests for sort_submodules and compute_summary |
| 2 | 7f34023 | feat(03-01): implement sort_submodules and compute_summary in renderer |
| 3 | e4f0cfe | test(03-01): add integration test for sorted HTML output |

## Self-Check: PASSED

All files exist, all commits verified, all key functions present.
