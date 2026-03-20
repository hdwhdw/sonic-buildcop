# Phase 2: Staleness Model - Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Compute cadence-aware per-submodule staleness thresholds and classify each submodule as green/yellow/red. This builds on Phase 1's data pipeline (collector.py → data.json → renderer.py) by adding threshold computation from historical commit activity and a classification step that feeds status badges into the existing dashboard.

</domain>

<decisions>
## Implementation Decisions

### Cadence history source
- Query each submodule repo's **own commit history** on its default branch (development activity)
- NOT sonic-buildimage's pointer update history — we're measuring whether the pointer keeps up with development velocity
- Use GitHub Commits API with `since` parameter for 6-month lookback window
- Include all commits (not just merges) — sonic-net repos use squash-merge so each commit is meaningful

### Cadence computation
- List commit dates over last 6 months per submodule
- Compute intervals between consecutive commits
- Take **median interval** (STALE-03) — resists holiday gaps and burst periods
- Result: "median_days" per submodule (e.g., sonic-swss = 1.2 days, sonic-linux-kernel = 8 days)

### Classification signal
- **Both** days-behind and commits-behind are evaluated — worst of the two determines color
- Days-behind compared against time-based thresholds (median_days × multiplier)
- Commits-behind compared against commit-based thresholds (derived from same cadence)

### Threshold multipliers
- Fixed at **2× median = yellow**, **4× median = red** for both signals
- Days: yellow if days_behind > 2 × median_days, red if > 4 × median_days
- Commits: yellow if commits_behind > 2 × expected_commits_in_median_window, red if > 4×
- Green if below both yellow thresholds

### Fallback thresholds (STALE-04)
- For submodules with <5 commits in the 6-month window
- Default yellow: 30 days / 10 commits behind
- Default red: 60 days / 20 commits behind (2× yellow)

### Integration with Phase 1
- Staleness model runs as a separate module between collector and renderer
- collector.py → data.json → staleness module enriches data.json with thresholds and status → renderer.py reads enriched data
- Or: staleness module is called by collector.py to add fields before writing data.json
- Claude's discretion on exact integration point

### Claude's Discretion
- Whether staleness is a separate `staleness.py` module or integrated into collector
- Exact API pagination strategy for commit history (per_page, max pages)
- How to derive "expected commits in median window" for commit-based thresholds
- Whether to cache cadence data or recompute daily
- Template changes for rendering status badges (color mapping)

</decisions>

<canonical_refs>
## Canonical References

### Phase 1 outputs (integration points)
- `scripts/collector.py` — Current data pipeline; data.json schema includes commits_behind, days_behind per submodule
- `scripts/renderer.py` — Reads data.json, renders HTML; needs to consume new status/threshold fields
- `templates/dashboard.html` — Jinja2 template; needs status badge column
- `data.json` schema: `{generated_at, submodules: [{name, path, pinned_sha, branch, commits_behind, days_behind, compare_url, status, error}]}`

### Requirements
- `.planning/REQUIREMENTS.md` — STALE-01 through STALE-05

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `collector.py` already has GitHub API session setup, retry logic, and rate-limit courtesy delays
- `get_staleness()` computes commits_behind and days_behind — staleness model consumes these
- `conftest.py` has mock API fixtures that can be extended for commit history mocks

### Integration Points
- data.json is the interchange format — staleness fields get added here
- renderer.py + dashboard.html need to display the new status badge column
- GitHub Actions workflow already runs collector → renderer; may need a step between or collector change

### API Budget Impact
- Current: ~34 API calls per run
- Phase 2 adds: 10 submodules × ~2-3 pages of commits each = ~20-30 extra calls
- Total: ~54-64 calls, still well within 1,000/hr GITHUB_TOKEN limit

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond the decisions above.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-staleness-model*
*Context gathered: 2026-03-20*
