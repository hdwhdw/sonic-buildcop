---
phase: 05-visual-overhaul
plan: 01
title: "Linkification + Structural Changes"
one_liner: "Linkify names/SHAs to GitHub, remove Path column, add header/footer"
completed: "2026-03-21T06:26:00Z"
duration: "~2min"
tasks_completed: 2
tasks_total: 2
dependency_graph:
  requires: []
  provides: ["linked-names", "linked-shas", "header-section", "footer-section", "8-column-table"]
  affects: ["templates/dashboard.html", "tests/test_renderer.py"]
tech_stack:
  added: []
  patterns: ["Jinja2 URL construction for commit links"]
key_files:
  created: []
  modified:
    - templates/dashboard.html
    - tests/test_renderer.py
key_decisions:
  - "Commit URLs built in template via owner/repo/sha fields rather than a pre-built URL"
  - "Path column fully removed (was always src/<name>, redundant with linked name)"
metrics:
  duration: "2min"
  completed_date: "2026-03-21"
  tasks: 2
  files: 2
---

# Phase 05 Plan 01: Linkification + Structural Changes Summary

Linkify names/SHAs to GitHub, remove Path column, add header/footer with description and source link.

## What Was Done

### Task 1: Template Changes
- Wrapped h1, timestamp, and summary in `<header>` element
- Added `.description` paragraph linking to sonic-net/sonic-buildimage
- Removed `<th>Path</th>` and `<td>{{ sub.path }}</td>` — table now 8 columns
- Wrapped submodule name in `<a href="{{ sub.url }}">`
- Wrapped pinned SHA `<code>` in `<a href="https://github.com/{{ sub.owner }}/{{ sub.repo }}/commit/{{ sub.pinned_sha }}">`
- Added `<footer>` with "Powered by sonic-buildcop" link
- Added `.description` and `footer` CSS rules

### Task 2: Test Updates
- Added `owner` and `repo` fields to `_make_data()` defaults (both submodules)
- Added `owner` and `repo` fields to `_make_sub()` helper
- Added `owner` and `repo` fields to custom dicts in `test_html_contains_pinned_sha_short` and `test_render_html_sorted_worst_first`
- Updated `test_html_contains_table_headers` to 8 columns (removed Path assertion)
- Updated `test_render_html_preserves_all_columns` to 8 columns (removed Path)
- Added 6 new tests: name links, SHA links, header, footer, path removed, unavailable SHA not linked

## Commits

| Hash | Message | Files |
|------|---------|-------|
| df9f3ed | feat(05-01): linkify dashboard entities and add header/footer | templates/dashboard.html, tests/test_renderer.py |

## Test Results

75 passed, 0 failed (including 6 new linkification/structure tests)

## Deviations from Plan

None — plan executed exactly as written.

## Requirements Coverage

| Req | Description | Status |
|-----|-------------|--------|
| LINK-01 | Submodule names link to GitHub repos | ✅ Done |
| LINK-02 | Pinned SHAs link to exact commits | ✅ Done |
| LINK-03 | Path column removed | ✅ Done |
| LINK-04 | Footer with source repo link | ✅ Done |
| VIS-04 | Header with project description | ✅ Done |
