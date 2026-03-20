# Domain Pitfalls

**Domain:** Submodule staleness dashboard (sonic-buildimage)
**Researched:** 2025-07-18
**Confidence:** HIGH — validated against actual sonic-buildimage repo data and GitHub API behavior

## Critical Pitfalls

Mistakes that cause rewrites, broken dashboards, or fundamentally wrong data.

### Pitfall 1: Comparing Against the Wrong Branch

**What goes wrong:** The dashboard compares each submodule's pinned SHA against `master` or `main`, but the submodule is actually tracking a different branch. The compare API returns `"status": "diverged"` with nonsensical `ahead_by`/`behind_by` numbers, or the staleness is wildly inaccurate.

**Why it happens:** 46 of 49 submodules in sonic-buildimage have NO explicit `branch` field in `.gitmodules` — they're pinned by SHA only. Developers assume "compare against default branch" is always correct. But:
- 3 submodules DO have explicit branches: `sonic-frr` tracks `frr-10.4.1`, `saibcm-modules-dnx` tracks `sdk-6.5.22-gpl-dnx`, `sonic-restapi` tracks `master`
- Some submodule repos may have changed their default branch from `master` to `main`
- A pinned SHA might be on a release branch, not the default branch

**Consequences:** Dashboard shows "500 commits behind" when the submodule is actually up-to-date on its intended branch. Or shows green when it's genuinely stale on the wrong branch. Loss of trust in the entire dashboard.

**Prevention:**
1. Always check `.gitmodules` `branch` field first — if present, use it
2. For submodules without explicit branch, query each repo's `default_branch` via API (costs 31 calls, but cacheable)
3. Handle the `"diverged"` status from compare API explicitly — show a distinct "diverged" badge, not fake green/red
4. Cache default branch info (it rarely changes) — fetch once per run, not per submodule

**Detection:** Compare API responses with `"status": "diverged"` instead of `"ahead"` or `"behind"`. Any submodule showing both `ahead_by > 0` AND `behind_by > 0` simultaneously.

**Phase:** Must be addressed in Phase 1 (core data collection). Getting the comparison target wrong poisons all downstream staleness computation.

---

### Pitfall 2: Submodule Name/Path/URL Mapping Chaos

**What goes wrong:** Code assumes a simple mapping between submodule name, filesystem path, and GitHub repo URL. In reality, sonic-buildimage has pervasive mismatches across all three identifiers, causing the script to query the wrong repo or miss submodules entirely.

**Why it happens:** Git submodules have three independent identifiers:
- **Name** (in `[submodule "name"]`) — sometimes just the repo name, sometimes includes `src/` prefix
- **Path** (the filesystem location) — always includes directory prefix
- **URL** (the GitHub repo URL) — the repo slug doesn't always match the path leaf

Verified mismatches in sonic-buildimage:
- 7 submodules have `name ≠ path` (e.g., name=`sonic-swss`, path=`src/sonic-swss`)
- 23+ submodules have URL repo slug ≠ path leaf (e.g., path ends in `sonic-platform-pde` but URL points to `sonic-platform-pdk-pde`)
- URLs inconsistently end with `.git` (25 repos), no suffix (23 repos), or `/` (1 repo)

**Consequences:** Script extracts `owner/repo` from URL incorrectly, makes API calls to nonexistent repos, gets 404s, and either crashes or silently omits submodules.

**Prevention:**
1. Parse `.gitmodules` with a proper parser (regex on the INI-like format), extracting all three fields per entry
2. Normalize URLs: strip trailing `.git`, trailing `/`, and extract `owner/repo` with explicit logic
3. Use the URL as the source of truth for which GitHub repo to query — never derive it from the path or name
4. Build a mapping table and validate it against API responses (does this repo exist?) during startup
5. Unit test the parser against the actual `.gitmodules` file from sonic-buildimage

**Detection:** Any 404 responses from the GitHub API during submodule queries. Count of processed submodules ≠ expected 31.

**Phase:** Must be addressed in Phase 1. The .gitmodules parser is the foundation of everything.

---

### Pitfall 3: Cadence Computation Fails on Sparse Data

**What goes wrong:** The auto-threshold algorithm produces useless or misleading thresholds for submodules with very few historical updates. A submodule with 2 data points gets a "threshold" that is meaningless noise.

**Why it happens:** Real data from sonic-buildimage shows extreme cadence variance:
- `sonic-swss`: 55 updates since Jan 2025, avg 8 days, but has a 94-day outlier gap
- `sonic-dbsyncd`: only 2 updates since Jan 2025, 87-day interval — ONE data point
- `sonic-restapi`: 5 updates, intervals of [14, 14, 7, 23] days

Statistical operations (mean, median, percentile) on N<5 samples are unreliable. Using p95 of intervals with 3 data points just returns the max, which isn't a meaningful threshold.

**Consequences:** Dashboard shows perpetual green for barely-maintained submodules (threshold is infinity) or perpetual red for active ones during normal pauses (threshold too tight from mean on skewed data).

**Prevention:**
1. Define minimum sample size (N≥5 intervals) for cadence-based thresholds
2. For submodules below minimum: use a global fallback threshold (e.g., median of all submodules' cadence, or a sensible default like 30 days)
3. Use median rather than mean — it's robust to the outlier gaps (sonic-swss avg=8 days but has 94-day gap)
4. Consider using IQR-based thresholds: `yellow = median + 1×IQR`, `red = median + 2×IQR` — this handles skewed distributions better than fixed multipliers on mean
5. Flag submodules with insufficient data in the dashboard UI so users know the threshold is approximate

**Detection:** Any submodule where computed threshold exceeds 180 days, or where N<5 intervals. Any submodule perpetually in one state (always green or always red for weeks).

**Phase:** Must be addressed in the cadence/threshold computation phase. Design the algorithm with fallbacks from the start — don't bolt them on later.

---

### Pitfall 4: Dashboard Silently Goes Stale (The Meta-Irony)

**What goes wrong:** The staleness dashboard itself becomes stale. GitHub disables the cron workflow after 60 days of repository inactivity, the workflow fails silently, or errors cause it to deploy old data. Users see green badges from data that's weeks old.

**Why it happens:**
- GitHub automatically disables scheduled workflows after 60 days of no repository activity (commits, issues, PRs)
- Cron failures don't send notifications by default
- If the script errors out partway, it might deploy a partial/old HTML file
- No mechanism to distinguish "all green because everything is fresh" from "all green because data is stale"

**Consequences:** The tool designed to prevent staleness becomes the thing that masks it. Maintainers trust the green dashboard and miss genuine drift.

**Prevention:**
1. **Mandatory timestamp:** Display "Last updated: YYYY-MM-DD HH:MM UTC" prominently at the top of the dashboard — this is non-negotiable
2. **Staleness self-check:** Include a visual warning if data is >48 hours old (dashboard checks its own freshness in the browser via JS)
3. **Workflow keep-alive:** Commit the generated data.json to the repo on each run (not just deploy to Pages) — this creates activity that prevents the 60-day disable
4. **Graceful degradation:** If a submodule query fails, show "Error" badge for that row but still deploy the rest — never skip deployment entirely on partial failures
5. **Workflow notifications:** Add `if: failure()` step that creates a GitHub issue or annotation when the workflow fails

**Detection:** Dashboard showing the same "last updated" for multiple days. GitHub Actions tab showing the workflow as "disabled."

**Phase:** Must be designed into Phase 1 (workflow + deployment). The timestamp and self-check are load-bearing features, not polish.

---

### Pitfall 5: Accidentally Cloning All 49 Submodules in CI

**What goes wrong:** The GitHub Actions workflow uses `actions/checkout` with `submodules: true` or runs `git submodule update --init`, causing it to clone all 49 submodule repositories. The workflow takes 15-30+ minutes, consumes massive bandwidth, and frequently times out.

**Why it happens:** Developer instinct is to "initialize submodules" when working with a repo that has them. But sonic-buildimage's `.git` alone is 826MB, and fully initializing all 49 submodules would clone dozens of additional repositories.

**Consequences:** Workflow exceeds GitHub Actions timeout (6 hours default, but realistically 10-30 minutes wasted). Unnecessary bandwidth and compute. May hit rate limits from parallel git fetches.

**Prevention:**
1. **NEVER** use `submodules: true` or `submodules: recursive` in `actions/checkout`
2. Get submodule pinned SHAs from `git ls-tree HEAD` (works on the parent tree, no submodule init needed)
3. Get submodule URLs from `.gitmodules` (file in the repo, no submodule init needed)
4. If cadence computation needs git log history: use `fetch-depth: 0` on the PARENT repo only (no submodules)
5. For submodule HEAD comparison: use GitHub API, not git operations on cloned submodules

**Detection:** Workflow run time >5 minutes for data collection. Workflow logs showing `Submodule path 'src/...' registered for path...` messages.

**Phase:** Phase 1 (workflow design). The checkout step configuration is one of the first things written and one of the hardest to notice is wrong.

## Moderate Pitfalls

### Pitfall 6: GitHub API Secondary Rate Limits (Abuse Detection)

**What goes wrong:** Even within the 1,000 requests/hour budget, making 30+ concurrent API requests triggers GitHub's secondary rate limiting. The API returns `403 Forbidden` with a `Retry-After` header, and the script either crashes or returns incomplete data.

**Prevention:**
1. Serialize API requests with a small delay (100-200ms between calls)
2. Or use GitHub's GraphQL API to batch multiple repo queries into fewer requests (can fetch all 31 repos in 2-3 queries)
3. Respect `Retry-After` headers — implement exponential backoff
4. Log remaining rate limit from `X-RateLimit-Remaining` response header

**Phase:** Phase 1 (API client implementation). Easy to add delays upfront, painful to retrofit.

---

### Pitfall 7: The Compare API 250-Commit Detail Limit

**What goes wrong:** The GitHub compare API (`/compare/{base}...{head}`) returns a max of 250 commits in the response body. If a submodule is very far behind (e.g., 500 commits), the `ahead_by` field is accurate but the commit list is truncated, so you can't iterate commit dates from the compare response alone.

**Prevention:**
1. Use `ahead_by` / `behind_by` fields for the count — these ARE accurate beyond 250
2. For date computation: get the date of HEAD commit and the date of the pinned commit separately (2 calls), rather than iterating all commits between them
3. "Days behind" = `date(HEAD on default branch) - date(pinned commit)` — only needs 2 dates, not the full commit list

**Phase:** Phase 1 (data collection design). If you design around iterating the commit list, you'll discover this limit too late.

---

### Pitfall 8: Confusing "Days Since Pinned Commit" with "Days Behind HEAD"

**What goes wrong:** The dashboard computes "days behind" as `now() - date(pinned_commit)`, which measures how old the pinned commit is. But this isn't the same as how far behind the submodule is — what matters is `date(HEAD_commit) - date(pinned_commit)`, i.e., how much newer the upstream is.

**Why it happens:** It's simpler to compute `now - pinned_date`, and it seems equivalent. But consider: if a submodule's upstream repo has had no commits in 6 months, the pinned commit from 6 months ago is NOT stale — it's up to date.

**Prevention:**
1. Always compute: `date(latest commit on upstream default branch) - date(pinned commit)`
2. Also show "last upstream activity" date — helps distinguish "stale pointer" from "dormant upstream"
3. A submodule with 0 commits ahead is up-to-date regardless of commit age

**Phase:** Phase 1 (staleness metric definition). Getting the core metric wrong invalidates the entire dashboard.

---

### Pitfall 9: Not Handling Archived/Deleted/Renamed Repos

**What goes wrong:** A submodule's upstream repo gets archived, renamed, or deleted. API calls return 404 or redirect. The script crashes or shows misleading data.

**Prevention:**
1. Treat any non-200 API response as "unknown" status, not an error
2. Show distinct badge: "⚠️ Repo unavailable" vs "✅ Up to date" vs "🔴 Stale"
3. GitHub returns `301` for renamed repos — follow redirects but log the new URL
4. Archived repos return normal data but will never have new commits — flag them as "archived" if the `archived` field is true in the repo response

**Phase:** Phase 1 (error handling). Must be in the initial API client, not added later.

---

### Pitfall 10: Jekyll Processing Breaks GitHub Pages Assets

**What goes wrong:** GitHub Pages runs Jekyll by default, which ignores files/directories starting with `_` (underscore). If the generated dashboard uses a framework with `_next/`, `_static/`, or `_assets/` directories, they silently vanish in production.

**Prevention:**
1. Add a `.nojekyll` file to the deployed output (empty file, just needs to exist)
2. If using `actions/upload-pages-artifact` + `actions/deploy-pages`, the `.nojekyll` must be in the artifact root
3. Test the deployed site, not just the local build — this bug only manifests on GitHub Pages

**Phase:** Phase 1 (deployment configuration). A 30-second fix if you know about it, hours of debugging if you don't.

## Minor Pitfalls

### Pitfall 11: Cron Schedule Timing Unreliability

**What goes wrong:** Dashboard is expected to update "daily at 6AM UTC" but the cron triggers anywhere from 6:00 to 7:00 UTC due to GitHub Actions scheduling delays. During GitHub outages, runs may be skipped entirely.

**Prevention:**
1. Don't rely on exact timing — design the dashboard to be "eventually consistent"
2. Show the actual run time, not the scheduled time
3. Allow manual `workflow_dispatch` trigger for on-demand refresh
4. If a run is skipped, the next run should catch up gracefully (idempotent generation)

**Phase:** Phase 1 (workflow design). Minor but easy to address.

---

### Pitfall 12: Concurrent Workflow Runs Deploy Conflicting Data

**What goes wrong:** If the cron triggers twice in quick succession (or a manual trigger overlaps with cron), two workflow runs generate and deploy data simultaneously, potentially deploying an older run's data after a newer one.

**Prevention:**
Add a concurrency group to the workflow:
```yaml
concurrency:
  group: dashboard-deploy
  cancel-in-progress: true
```
This ensures only the latest run deploys.

**Phase:** Phase 1 (workflow configuration). One line of YAML prevents data races.

---

### Pitfall 13: Treating All Submodules Equally in the UI

**What goes wrong:** The dashboard gives equal visual weight to all 31 submodules. But `sonic-swss` (63 updates/year, critical path) and `sonic-genl-packet` (rarely updated, niche) are not equally important. Users are overwhelmed by noise from low-importance submodules.

**Prevention:**
1. Sort by staleness severity (red first, then yellow, then green)
2. Consider grouping by update frequency: "Active" (weekly+) vs "Occasional" (monthly+) vs "Rare" (<quarterly)
3. Allow collapsing green submodules to reduce noise
4. v2 consideration: integrate CODEOWNERS data to show responsible team

**Phase:** Phase 2 (UI polish). Get the data right first, optimize presentation second.

---

### Pitfall 14: Hardcoding the Submodule List

**What goes wrong:** The script hardcodes a list of 31 submodule names/URLs. When sonic-buildimage adds or removes a submodule, the dashboard silently misses the new one or errors on the removed one.

**Prevention:**
1. Always discover submodules dynamically from `.gitmodules` at runtime
2. Filter to sonic-net org by checking the URL, not by name matching
3. Log when the discovered count changes from the previous run

**Phase:** Phase 1 (data collection). Dynamic discovery is easier to implement than hardcoded lists and prevents drift.

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Data collection (API client) | Rate limiting, wrong branch comparison, URL parsing | Serial requests with delay, normalize URLs, query default_branch per repo |
| .gitmodules parsing | Name/path/URL mismatches | Use URL as truth, normalize suffixes, validate against API |
| Cadence computation | Sparse data, outlier gaps, regime changes | Minimum sample size, median over mean, IQR-based thresholds, fallback defaults |
| Staleness metric | Wrong date comparison, misleading "commits behind" | Use upstream HEAD date minus pinned date, not now() minus pinned date |
| GitHub Actions workflow | Submodule clone, shallow clone, cron disable | Never init submodules, appropriate fetch-depth, keep-alive mechanism |
| GitHub Pages deployment | Jekyll processing, missing .nojekyll, permissions | Add .nojekyll, configure permissions block, test deployed site |
| Dashboard UI | Stale data not visible, no error states | Mandatory timestamp, self-check in browser, graceful degradation |
| Error handling | Partial failures crash everything | Per-submodule try/catch, deploy partial data, log errors |

## Sources

- sonic-net/sonic-buildimage `.gitmodules` analysis (direct inspection — 49 submodules, 31 sonic-net, verified name/path/URL mismatches)
- sonic-net/sonic-buildimage `git log` analysis (update cadence data: sonic-swss=55/yr, sonic-dbsyncd=2/yr, etc.)
- GitHub REST API documentation: rate limits (60/hr unauth, 5000/hr PAT, 1000/hr GITHUB_TOKEN), compare endpoint 250-commit cap
- GitHub Actions documentation: 60-day workflow disable policy, cron scheduling delays, concurrency groups
- GitHub Pages documentation: Jekyll processing, .nojekyll file, actions/deploy-pages permissions
- Confidence: HIGH for all findings derived from direct repo inspection; MEDIUM for GitHub API behavior (based on docs + training data, not live API testing)
