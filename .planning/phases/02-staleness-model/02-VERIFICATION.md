---
phase: 02-staleness-model
verified: 2026-03-20T20:15:00Z
status: passed
score: 4/4 must-haves verified
re_verification: false
must_haves:
  truths:
    - "Each submodule's yellow/red thresholds reflect its historical update frequency — weekly triggers sooner than rarely-updated"
    - "Thresholds are computed from median inter-update interval (not mean), resisting outlier gaps"
    - "Submodules with fewer than 5 historical updates display sensible fallback thresholds"
    - "Each submodule displays a green, yellow, or red status badge based on its individually-computed thresholds"
  artifacts:
    - path: "scripts/staleness.py"
      provides: "Cadence computation, threshold derivation, classification"
    - path: "scripts/collector.py"
      provides: "Pipeline integration — imports and calls enrich_with_staleness"
    - path: "templates/dashboard.html"
      provides: "Badge column with green/yellow/red/unknown CSS classes"
    - path: "tests/test_staleness.py"
      provides: "20 unit tests covering all staleness functions"
    - path: "tests/conftest.py"
      provides: "4 new fixtures for staleness tests"
  key_links:
    - from: "staleness.py"
      to: "collector.py"
      via: "from staleness import enrich_with_staleness → enrich_with_staleness(session, results)"
    - from: "staleness.py"
      to: "dashboard.html"
      via: "staleness_status field rendered as badge-{{ sub.staleness_status }}"
    - from: "collector.py"
      to: "staleness.py"
      via: "enrich_with_staleness call in main() after collection loop"
---

# Phase 2: Staleness Model Verification Report

**Phase Goal:** Each submodule has cadence-aware staleness thresholds that distinguish urgently-stale from acceptably-behind
**Verified:** 2026-03-20T20:15:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Each submodule's yellow/red thresholds reflect its historical update frequency | ✓ VERIFIED | `compute_thresholds()` uses 2×/4× median multiplier; daily repo (median=1) → yellow=2d/red=4d vs weekly repo (median=8) → yellow=16d/red=32d. Tests `test_compute_thresholds_frequent_repo` and `test_compute_thresholds_slow_repo` confirm. |
| 2 | Thresholds computed from median (not mean), resisting outlier gaps | ✓ VERIFIED | `staleness.py:107` uses `statistics.median(intervals)`. Test `test_compute_cadence_median_resists_outliers`: 9×1-day + 1×30-day gap → median still 1.0. |
| 3 | Submodules with <5 historical updates use sensible fallback thresholds | ✓ VERIFIED | `MIN_COMMITS_FOR_CADENCE = 5` (line 22). `compute_cadence()` returns `is_fallback=True` for count<5. `FALLBACK_THRESHOLDS`: yellow=30d/10c, red=60d/20c. Tests `test_compute_cadence_fallback_few_commits`, `test_compute_cadence_fallback_zero_commits`, `test_compute_thresholds_fallback` confirm. |
| 4 | Each submodule displays green/yellow/red status badge | ✓ VERIFIED | `classify()` returns "green"/"yellow"/"red" via worst-of rule. `enrich_with_staleness()` sets `staleness_status` field. `collector.py:227` calls it. `dashboard.html:42-45` renders `<span class="badge badge-{{ sub.staleness_status }}">` with CSS at lines 16-19 for green/yellow/red/unknown. |

**Score:** 4/4 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `scripts/staleness.py` | Cadence computation, threshold derivation, classification | ✓ VERIFIED | 203 lines, 5 exported functions (get_commit_dates, compute_cadence, compute_thresholds, classify, enrich_with_staleness). Uses statistics.median, 1.0-day minimum floor, 2×/4× multipliers, worst-of classification. |
| `scripts/collector.py` | Pipeline integration via staleness import | ✓ VERIFIED | Line 11: `from staleness import enrich_with_staleness`. Line 227: `enrich_with_staleness(session, results)` called after collection loop, before JSON write. |
| `templates/dashboard.html` | Badge column with CSS styling | ✓ VERIFIED | CSS classes `.badge-green`, `.badge-yellow`, `.badge-red`, `.badge-unknown` (lines 16-19). Status column as 2nd `<th>` (line 29). Conditional badge rendering (lines 42-45). |
| `tests/test_staleness.py` | Comprehensive staleness tests | ✓ VERIFIED | 20 test functions covering: 6 cadence tests (regular, weekly, outlier, fallback×2, floor), 4 threshold tests (normal, fast, slow, fallback), 6 classify tests (green, yellow×2, red×2, worst-of), 2 API tests (single page, pagination), 2 enrich tests (ok, unavailable). |
| `tests/conftest.py` | Extended fixtures for staleness | ✓ VERIFIED | 4 new fixtures added (lines 136-193): `mock_commits_page_1`, `mock_commits_page_2`, `sample_submodule_ok`, `sample_submodule_unavailable`. Existing 7 fixtures untouched. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `staleness.py` | `collector.py` | `from staleness import enrich_with_staleness` | ✓ WIRED | Imported at module level (line 11) and called in `main()` (line 227) |
| `collector.py` | `staleness.py` | `enrich_with_staleness(session, results)` | ✓ WIRED | Passes live session and results list; staleness module enriches dicts in-place before JSON write |
| `staleness.py` → data | `dashboard.html` | `sub.staleness_status` field via Jinja2 | ✓ WIRED | `enrich_with_staleness` sets `staleness_status` → renderer passes data → template renders `badge-{{ sub.staleness_status }}` |
| `test_staleness.py` | `staleness.py` | `from staleness import (5 functions)` | ✓ WIRED | All 5 public functions imported and tested (20 tests) |
| `conftest.py` | `test_staleness.py` | pytest fixture injection | ✓ WIRED | 4 fixtures used across 4 test functions |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-----------|-------------|--------|----------|
| STALE-01 | 02-01 | Auto-computed thresholds from historical update cadence | ✓ SATISFIED | `get_commit_dates()` fetches 6-month history → `compute_cadence()` calculates median interval → `compute_thresholds()` derives 2×/4× multiplied yellow/red thresholds |
| STALE-02 | 02-01 | Frequently-updated submodules trigger sooner than rare ones | ✓ SATISFIED | Thresholds proportional to median: daily repo (1d median) → yellow at 2d; weekly repo (8d median) → yellow at 16d. Tests `test_compute_thresholds_frequent_repo` vs `test_compute_thresholds_slow_repo` prove differentiation. |
| STALE-03 | 02-01 | Median not mean, resists outliers | ✓ SATISFIED | `statistics.median(intervals)` at line 107. Test `test_compute_cadence_median_resists_outliers` confirms: single 30-day gap among 1-day intervals doesn't affect median. |
| STALE-04 | 02-01 | Fallback thresholds for <5 commits | ✓ SATISFIED | `MIN_COMMITS_FOR_CADENCE = 5`. Fallback returns yellow=30d/10c, red=60d/20c. Tests confirm for 0 and 3 commit cases. |
| STALE-05 | 02-02 | Green/yellow/red badge per submodule | ✓ SATISFIED | `classify()` returns color via worst-of rule → `staleness_status` field set by `enrich_with_staleness()` → dashboard.html renders CSS-styled badge spans with green/yellow/red/unknown classes. |

**Orphaned requirements:** None — all 5 STALE requirements accounted for.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | None found | — | — |

No TODO/FIXME/HACK comments, no placeholder implementations, no empty handlers, no console-only stubs found in any phase-modified file.

### Test Results

All **43 tests pass** (14 collector + 9 renderer + 20 staleness) with 0 failures, 0 errors, in 0.17s. No regressions in pre-existing tests.

### Commit Verification

| Commit | Message | Status |
|--------|---------|--------|
| `f2fafb8` | test(02-01): add failing staleness tests — RED | ✓ EXISTS |
| `6ee3272` | feat(02-01): implement staleness module — GREEN | ✓ EXISTS |
| `44ada8e` | feat(02-02): wire staleness enrichment into collector pipeline | ✓ EXISTS |
| `196f429` | feat(02-02): add status badge column to dashboard template | ✓ EXISTS |

### Human Verification Required

### 1. Badge Visual Appearance

**Test:** Open the generated dashboard HTML in a browser after running the full pipeline
**Expected:** Each submodule row shows a colored badge: green (#28a745), yellow (#ffc107), or red (#dc3545) with readable text
**Why human:** CSS rendering and color contrast can't be verified programmatically

### 2. End-to-End Pipeline with Live API

**Test:** Run `GITHUB_TOKEN=<token> python scripts/collector.py` and inspect data.json
**Expected:** Each submodule in data.json has `staleness_status` (green/yellow/red), `median_days`, `commit_count_6m`, and `thresholds` fields populated
**Why human:** Requires live GitHub API access; unit tests mock the API layer

### Gaps Summary

No gaps found. All 4 observable truths are verified, all 5 artifacts pass all three levels (exists, substantive, wired), all 3 key links are confirmed wired, and all 5 requirements (STALE-01 through STALE-05) are satisfied. Zero anti-patterns detected. All 43 tests pass with no regressions.

---

_Verified: 2026-03-20T20:15:00Z_
_Verifier: Claude (gsd-verifier)_
