# Phase 3: Dashboard UI - Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Polish the existing HTML dashboard into something maintainers can assess project-wide submodule health from in under 10 seconds. This means: pre-sorted table (worst-first), aggregate summary at top, clean visual styling, and responsive layout. No new data collection or staleness logic — purely presentation layer on top of Phase 1+2's data.json.

</domain>

<decisions>
## Implementation Decisions

### Sort order (UI-02)
- Pre-sort in Python (renderer.py) before generating HTML — no JavaScript needed
- Primary key: color tier (red first, then yellow, then green)
- Secondary key: days-behind descending within each tier
- Unavailable/unknown submodules sort last

### Aggregate summary (UI-03)
- Text line with colored counts at the top of the page, below the heading
- Format: "🟢 7 green · 🟡 2 yellow · 🔴 1 red"
- Computed in renderer.py, passed as template variables
- Gives instant project-wide health assessment

### Visual polish (UI-05)
- Clean minimal CSS: system fonts, subtle table borders, good spacing
- No external CSS frameworks or dependencies
- All styling inline in the template `<style>` block
- Professional but simple — this is a developer tool, not a marketing page

### Responsive layout (UI-05)
- Horizontal scroll on narrow screens — table stays readable
- `overflow-x: auto` wrapper around the table
- Don't worry about mobile card layouts — developer tool used on laptops
- Max-width container for readability on wide monitors

### Timestamp (UI-04)
- Already exists from Phase 1 ({{ generated_at }}) — just ensure it's styled consistently
- Format is ISO 8601, acceptable as-is for developer audience

### Claude's Discretion
- Exact CSS values (colors, paddings, font sizes, border styles)
- Whether to add subtle alternating row colors
- Exact container max-width value
- Whether to add a footer or keep it minimal
- How to handle the sort in renderer.py (key function, where to place it)

</decisions>

<canonical_refs>
## Canonical References

### Phase 1+2 outputs (integration points)
- `scripts/renderer.py` — Current renderer; needs sort logic and summary computation
- `templates/dashboard.html` — Current template; needs CSS polish, summary section, responsive wrapper
- `data.json` schema: submodules now include `staleness_status`, `median_days`, `thresholds`, `commit_count_6m`

### Requirements
- `.planning/REQUIREMENTS.md` — UI-01 through UI-05

</canonical_refs>

<code_context>
## Existing Code Insights

### What already works (from Phase 1+2)
- Table with 7 columns: Submodule, Status, Path, Pinned SHA, Commits Behind, Days Behind, Compare
- Badge CSS for green/yellow/red/unknown status
- "Last updated" timestamp
- Jinja2 template rendering via renderer.py
- .nojekyll for GitHub Pages

### What needs changing
- `renderer.py`: add sort logic before passing to template, compute summary counts
- `dashboard.html`: add summary section, responsive CSS, visual polish
- No new files needed — all changes are to existing files

### Integration Points
- renderer.py reads data.json (unchanged) and renders template (existing flow)
- No changes to collector.py, staleness.py, or the GitHub Actions workflow

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

*Phase: 03-dashboard-ui*
*Context gathered: 2026-03-20*
