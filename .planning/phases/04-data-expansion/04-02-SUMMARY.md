---
phase: 04-data-expansion
plan: 02
subsystem: ui
tags: [jinja2, datetime, html-template, dashboard]

# Dependency graph
requires:
  - phase: 02-staleness-model
    provides: staleness fields (median_days, thresholds, staleness_status)
provides:
  - format_relative_time() utility for human-friendly timestamps
  - Median Cadence column in dashboard table
  - Thresholds column in dashboard table
  - <time> element with ISO datetime attribute
affects: [05-polish]

# Tech tracking
tech-stack:
  added: []
  patterns: [relative-time-formatting, semantic-html-time-element]

key-files:
  created: []
  modified:
    - scripts/renderer.py
    - templates/dashboard.html
    - tests/test_renderer.py

key-decisions:
  - "Use integer division for relative time buckets (just now / minutes / hours / days)"
  - "Threshold display as 'Xd / Xd' for yellow/red, 'fallback' for fallback thresholds"
  - "Median cadence formatted as '~X.X days' with one decimal place"

patterns-established:
  - "Relative time: format_relative_time() accepts optional now param for testability"
  - "Column additions: headers and cells added between existing columns, not appended"

requirements-completed: [DATA-07, DATA-08, DATA-10]

# Metrics
duration: 4min
completed: 2026-03-21
---

# Phase 4 Plan 2: Add Cadence Columns and Relative Timestamps Summary

**Median cadence + thresholds columns and human-friendly relative timestamps via format_relative_time() with `<time>` semantic HTML**

## What Was Done

### Task 1: Add format_relative_time and update renderer.py + template

- Added `format_relative_time(iso_timestamp, now=None)` to `scripts/renderer.py` — converts ISO 8601 to "just now", "N minutes ago", "N hours ago", "N days ago"
- Updated `render_dashboard()` to compute `generated_at_relative` and pass to template
- Replaced plain-text timestamp with `<time datetime="...">relative</time>` in template
- Added `<th>Median Cadence</th>` and `<th>Thresholds</th>` headers between Days Behind and Compare
- Added two new `<td>` cells: median cadence shows `~X.X days` or `—`; thresholds shows `Xd / Xd`, `fallback`, or `—`

### Task 2: Update test_renderer.py

- Added staleness fields to both default submodule dicts in `_make_data()` (sonic-swss: green/1.5d/20 commits; sonic-dash-ha: all None)
- Fixed `test_html_contains_pinned_sha_short` custom dict to include staleness fields
- Updated `_make_sub()` to accept optional `median_days` and `thresholds` params
- Added 8 `test_format_relative_time_*` unit tests covering all branches (just_now, minutes, singular_minute, hours, singular_hour, days, singular_day, z_suffix)
- Updated `test_html_contains_table_headers` and `test_render_html_preserves_all_columns` to check 9 columns
- Updated `test_html_contains_generated_at` to verify `<time>` element with `datetime` attribute
- Added `test_render_html_shows_median_cadence`, `test_render_html_shows_thresholds`, `test_render_html_unavailable_shows_dashes_in_cadence_columns`

## Deviations from Plan

None — plan executed exactly as written.

## Test Results

- **34 renderer tests passed** (23 existing + 11 new)
- **69 total tests passed** across full suite (collector + renderer + staleness)

## Commits

| Hash | Message |
|------|---------|
| 1eba415 | Add cadence columns and relative timestamps to dashboard |

## Self-Check: PASSED
