# Phase 1: Data Pipeline & Deployment - Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Collect correct submodule staleness data (commits behind, days behind, compare links) for 10 specific sonic-net submodules from sonic-net/sonic-buildimage via the GitHub API, and deploy a minimal HTML table to GitHub Pages on a daily cron. This phase establishes the end-to-end pipeline; cadence-aware thresholds (Phase 2) and polished UI (Phase 3) build on top.

</domain>

<decisions>
## Implementation Decisions

### Script language
- Python — pre-installed on ubuntu-latest, zero pip install for core deps
- SONiC ecosystem is Python-heavy, consistent with contributor expectations
- Use `requests` for HTTP (pre-installed on Actions runners)
- Use `Jinja2` for HTML templating (only additional pip dependency)

### Project structure
- Separate modules: `collector.py` (data collection) and `renderer.py` (HTML generation)
- JSON intermediate file: collector writes `data.json`, renderer reads it to produce HTML
- This enables debugging (inspect data.json) and future consumers (v2 JSON endpoint)

### Bare-bones output
- Minimal HTML table — plain table with submodule name, commits behind, days behind, compare link
- No styling beyond readable defaults — Phase 3 handles the polish
- Jinja2 template for HTML generation (cleaner than f-strings, scales for Phase 3)

### GitHub Pages deployment
- Deploy to `gh-pages` branch (keeps dashboard separate from source code)
- Use `actions/deploy-pages` or equivalent for automated deployment

### API authentication
- GITHUB_TOKEN only — auto-provided in Actions, 1,000 req/hour, no secrets needed
- ~64-99 API calls per run, well within limits
- No PAT required for v1

### Error handling
- Retry failed API calls 2-3 times per submodule
- If still failing, mark submodule as "data unavailable" and continue
- Never let one submodule failure break the whole pipeline

### Claude's Discretion
- Exact .gitmodules parsing approach (configparser, regex, or git config)
- GitHub API endpoint choices (REST compare, commits, git ls-remote)
- Retry backoff strategy (linear, exponential)
- Exact GitHub Actions workflow structure (single job vs multiple)
- .nojekyll handling for Pages deployment

</decisions>

<canonical_refs>
## Canonical References

No external specs — requirements fully captured in decisions above and in:

### Project requirements
- `.planning/REQUIREMENTS.md` — DATA-01 through DATA-06, CICD-01 through CICD-05, UI-06
- `.planning/PROJECT.md` — Core value, constraints, key decisions

### Research findings
- `.planning/research/STACK.md` — Technology recommendations, API endpoint details, verified gotchas
- `.planning/research/PITFALLS.md` — 14 domain-specific pitfalls (wrong branch comparison, URL parsing, 60-day workflow disable)
- `.planning/research/ARCHITECTURE.md` — ETL pipeline pattern, component boundaries, data flow

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — this is a greenfield project (hdwhdw/sonic-buildcop)

### Established Patterns
- sonic-buildimage `.gitmodules` has 49 entries; 7 name≠path mismatches, inconsistent `.git` URL suffixes
- 46/49 submodules have no explicit branch in `.gitmodules` — must query each repo's default_branch
- 3 submodules track non-default branches — compare against correct branch to avoid false alerts

### Integration Points
- Data source: sonic-net/sonic-buildimage (public repo, read-only access via GitHub API)
- Target submodules: sonic-swss, sonic-utilities, sonic-platform-daemons, sonic-sairedis, sonic-gnmi, sonic-swss-common, sonic-platform-common, sonic-host-services, sonic-linux-kernel, sonic-dash-ha

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches for the pipeline implementation.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-data-pipeline-deployment*
*Context gathered: 2026-03-20*
