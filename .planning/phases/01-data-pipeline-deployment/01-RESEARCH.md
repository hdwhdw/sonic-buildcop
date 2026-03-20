# Phase 1: Data Pipeline & Deployment - Research

**Researched:** 2026-03-20
**Domain:** GitHub API data collection pipeline + GitHub Pages deployment (Python)
**Confidence:** HIGH — all API endpoints verified live against sonic-net repos, all library versions confirmed

## Summary

Phase 1 builds the end-to-end data pipeline: a Python script (`collector.py`) fetches submodule staleness data for 10 target sonic-net submodules from sonic-buildimage via the GitHub REST API, writes a JSON intermediate (`data.json`), then a second script (`renderer.py`) produces a minimal HTML table deployed to GitHub Pages. The entire pipeline runs in a GitHub Actions cron workflow.

The technical approach is straightforward: ~34 GitHub API calls per run (well within the 1,000/hr GITHUB_TOKEN limit), Python stdlib for parsing/dates, `requests` for HTTP, and `Jinja2` for HTML templating. The main complexity lies in correctly parsing `.gitmodules` (name≠path mismatches, `.git` URL suffixes), resolving the correct comparison branch per submodule, and computing days-behind using the right date comparison (`HEAD date - pinned date`, not `now() - pinned date`).

**Primary recommendation:** Build collector.py and renderer.py as independent modules communicating through data.json. Use `configparser` for `.gitmodules` parsing, the Contents API for pinned SHAs, the Compare API for commits-behind, and `actions/deploy-pages` for GitHub Pages deployment. Hardcode the 10 target submodule names as a filter list (not all 49).

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Language**: Python — pre-installed on ubuntu-latest, zero pip install for core deps. Use `requests` for HTTP, `Jinja2` for HTML templating
- **Project structure**: Separate modules — `collector.py` (data collection) and `renderer.py` (HTML generation)
- **JSON intermediate**: Collector writes `data.json`, renderer reads it to produce HTML
- **Bare-bones output**: Minimal HTML table — plain table with submodule name, commits behind, days behind, compare link. No styling beyond readable defaults
- **GitHub Pages deployment**: Deploy to `gh-pages` branch (keeps dashboard separate from source code). Use `actions/deploy-pages` or equivalent
- **API authentication**: GITHUB_TOKEN only — auto-provided in Actions, no PAT required
- **Error handling**: Retry failed API calls 2-3 times per submodule. If still failing, mark submodule as "data unavailable" and continue

### Claude's Discretion
- Exact .gitmodules parsing approach (configparser, regex, or git config)
- GitHub API endpoint choices (REST compare, commits, git ls-remote)
- Retry backoff strategy (linear, exponential)
- Exact GitHub Actions workflow structure (single job vs multiple)
- .nojekyll handling for Pages deployment

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DATA-01 | Dashboard lists the top 10 sonic-net submodules with path and pinned commit SHA | Contents API (`/repos/sonic-net/sonic-buildimage/contents/{path}`) returns `type: "submodule"` with `sha` field. All 10 targets verified. |
| DATA-02 | Dashboard shows commits-behind count for each submodule | Compare API (`/repos/sonic-net/{repo}/compare/{sha}...{branch}`) returns `ahead_by` — accurate even for 1000+ commits. Verified live. |
| DATA-03 | Dashboard shows days-behind for each submodule | Compute `date(HEAD on branch) - date(pinned commit)`. Both dates available from Compare API (`base_commit.commit.committer.date`) + Commits API for HEAD. |
| DATA-04 | Dashboard provides direct link to GitHub compare view | URL pattern: `https://github.com/sonic-net/{repo}/compare/{pinned_sha}...{branch}`. Construct from collected data. |
| DATA-05 | Data collection correctly resolves each submodule's upstream default branch | All 10 targets verified: all use `master` as default branch, none have explicit `branch` in `.gitmodules`. Code should still query `default_branch` dynamically. |
| DATA-06 | Data collection handles .gitmodules parsing edge cases | Verified: 44/49 name≠path mismatches, 25/49 `.git` suffixes, 3 explicit branches (none in our 10). `configparser` handles all cases. |
| CICD-01 | GitHub Actions cron workflow runs daily | Standard `schedule: cron: '0 6 * * *'` + `workflow_dispatch` for manual. Verified pattern from STACK.md. |
| CICD-02 | Workflow deploys updated dashboard to GitHub Pages automatically | `actions/deploy-pages@v4` with `actions/upload-pages-artifact@v4`. Verified — works with GITHUB_TOKEN, no PAT needed. |
| CICD-03 | Workflow stays within GitHub Actions free tier for public repos | ~34 API calls per run, <2 min runtime. Public repos get unlimited Actions minutes. |
| CICD-04 | Pipeline handles individual submodule failures gracefully | Per-submodule try/except with retry logic. Failed submodules marked "unavailable" in data.json, not omitted. |
| CICD-05 | Workflow supports manual trigger (workflow_dispatch) | Standard `on: workflow_dispatch:` in workflow YAML. |
| UI-06 | Dashboard is hosted as a static GitHub Pages site | `actions/deploy-pages` deploys to Pages. Requires `.nojekyll` file and Pages source set to "GitHub Actions" in repo settings. |

</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.12+ | Script language | Pre-installed on `ubuntu-latest` runners. All 10 target submodule repos are SONiC (Python ecosystem). |
| `requests` | 2.32.5 (latest) | HTTP client for GitHub API | Pre-installed on `ubuntu-latest`. Clean auth headers, JSON response handling across ~34 API calls per run. |
| `Jinja2` | 3.1.6 (latest) | HTML templating | Only pip dependency needed. Cleaner than f-strings for HTML generation, scales for Phase 3 polish. |
| `configparser` | stdlib | Parse `.gitmodules` | Built-in INI parser. Handles the `.gitmodules` format (which IS INI-like with `[submodule "name"]` sections). Verified working. |
| `json` | stdlib | Read/write `data.json` | Serialize collected data as intermediate JSON between collector and renderer. |
| `datetime` | stdlib | Date math for days-behind | Compute `HEAD date - pinned date` for days-behind metric. |

### GitHub Actions

| Action | Version | Purpose | Why |
|--------|---------|---------|-----|
| `actions/checkout` | v4 | Checkout sonic-buildcop repo | Get scripts and templates. Do NOT use `submodules: true`. |
| `actions/setup-python` | v5 | Python 3.12 environment | Pin Python version for reproducibility. |
| `actions/configure-pages` | v5 | Configure Pages | Required by the official Pages deploy workflow. |
| `actions/upload-pages-artifact` | v4 | Upload site artifact | Packages `site/` directory as a Pages deployment artifact. |
| `actions/deploy-pages` | v4 | Deploy to Pages | Official action. Works with `GITHUB_TOKEN`, no PAT or deploy key needed. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `configparser` | Regex parsing | Regex is fragile; configparser handles the INI format natively. Configparser is standard library. |
| `configparser` | `git config --file` | Requires git CLI, subprocess calls, slightly more complex. Configparser is pure Python. |
| `actions/deploy-pages` | `peaceiris/actions-gh-pages` | 3rd party, pushes to branch, requires branch management. Official action is simpler. |
| `actions/deploy-pages` | Manual `git push` to gh-pages | More YAML, token permissions complexity, branch management headaches. |
| Sequential API calls | `asyncio` + `aiohttp` | Overkill for 34 calls. Sequential with small delay is simpler, avoids secondary rate limits. |

**Installation:**
```bash
pip install jinja2  # Only additional dependency
# requests is pre-installed on ubuntu-latest runners
```

## Architecture Patterns

### Recommended Project Structure
```
sonic-buildcop/
├── .github/
│   └── workflows/
│       └── update-dashboard.yml    # Cron + manual dispatch workflow
├── scripts/
│   ├── collector.py                # Stage 1: Fetch data from GitHub API → data.json
│   └── renderer.py                 # Stage 2: Read data.json → site/index.html
├── templates/
│   └── dashboard.html              # Jinja2 template for the HTML table
├── site/                           # Generated output directory (gitignored)
│   ├── index.html                  # Generated dashboard
│   └── .nojekyll                   # Prevent Jekyll processing on Pages
├── requirements.txt                # jinja2 (only pip dependency)
└── README.md
```

**Key structural decisions:**
- `scripts/` contains the two pipeline stages (locked decision: separate collector.py + renderer.py)
- `templates/` holds the Jinja2 template (separate from scripts for readability)
- `site/` is the deployment output directory (uploaded as Pages artifact, NOT committed)
- `data.json` is written to the workspace root by collector, read by renderer (intermediate artifact)
- No `docs/` folder, no `gh-pages` branch management needed — `actions/deploy-pages` handles deployment via the Pages API

### Pattern 1: Two-Stage ETL Pipeline with JSON Intermediate

**What:** collector.py fetches all data and writes `data.json`. renderer.py reads `data.json` and produces `site/index.html`. The workflow orchestrates both stages sequentially.

**When to use:** Always — this is the locked project structure decision.

**Data flow:**
```
GitHub API → collector.py → data.json → renderer.py → site/index.html → GitHub Pages
```

**data.json schema:**
```json
{
  "generated_at": "2026-03-20T06:00:00Z",
  "submodules": [
    {
      "name": "sonic-swss",
      "path": "src/sonic-swss",
      "url": "https://github.com/sonic-net/sonic-swss",
      "pinned_sha": "c20ded7bcef07eb68995aa2347f39c4bc22c9191",
      "branch": "master",
      "commits_behind": 0,
      "days_behind": 0,
      "compare_url": "https://github.com/sonic-net/sonic-swss/compare/c20ded7...master",
      "status": "ok",
      "error": null
    },
    {
      "name": "sonic-platform-common",
      "path": "src/sonic-platform-common",
      "url": "https://github.com/sonic-net/sonic-platform-common",
      "pinned_sha": "972ff46bd50b43108c1f630308e9138d8b886529",
      "branch": "master",
      "commits_behind": 1,
      "days_behind": 3,
      "compare_url": "https://github.com/sonic-net/sonic-platform-common/compare/972ff46...master",
      "status": "ok",
      "error": null
    },
    {
      "name": "sonic-dash-ha",
      "status": "unavailable",
      "error": "API returned 403 after 3 retries",
      "pinned_sha": null,
      "commits_behind": null,
      "days_behind": null,
      "compare_url": null
    }
  ]
}
```

### Pattern 2: Defensive Per-Submodule Error Handling

**What:** Wrap each submodule's data collection in try/except. If one fails after retries, mark it as `"status": "unavailable"` with an error message. Never let one failure break the whole pipeline.

**When to use:** Always — required by CICD-04.

**Example:**
```python
def collect_submodule(session, submodule, retries=3):
    """Collect data for one submodule with retry logic."""
    for attempt in range(retries):
        try:
            pinned_sha = get_pinned_sha(session, submodule["path"])
            compare = get_compare_data(session, submodule["repo"], pinned_sha, submodule["branch"])
            return {
                "name": submodule["name"],
                "path": submodule["path"],
                "pinned_sha": pinned_sha,
                "commits_behind": compare["ahead_by"],
                "days_behind": compute_days_behind(compare),
                "compare_url": build_compare_url(submodule["repo"], pinned_sha, submodule["branch"]),
                "status": "ok",
                "error": None,
            }
        except requests.RequestException as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                continue
            return {
                "name": submodule["name"],
                "path": submodule["path"],
                "status": "unavailable",
                "error": str(e),
                "pinned_sha": None,
                "commits_behind": None,
                "days_behind": None,
                "compare_url": None,
            }
```

### Pattern 3: GitHub Pages Artifact-Based Deployment

**What:** Use `actions/upload-pages-artifact` + `actions/deploy-pages` instead of pushing to a branch.

**When to use:** Always — this is the modern, official approach.

**Why not gh-pages branch:** The user's intent is "keep dashboard separate from source code." `actions/deploy-pages` achieves this better: no branch management, no force-push complexity, no git history pollution with daily data. The Pages API deploys artifacts directly — the separation is cleaner than a branch.

```yaml
permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install jinja2
      - name: Collect data
        run: python scripts/collector.py
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      - name: Render dashboard
        run: python scripts/renderer.py
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v4
        with:
          path: ./site
      - id: deployment
        uses: actions/deploy-pages@v4
```

### Anti-Patterns to Avoid

- **NEVER clone sonic-buildimage:** It's >2GB. The GitHub API returns everything we need in milliseconds.
- **NEVER use `submodules: true` in `actions/checkout`:** This would clone all 49 submodule repos. Only checkout hdwhdw/sonic-buildcop.
- **NEVER use `str.rstrip('.git')` to strip URL suffixes:** It treats `.git` as a character set and mangles names like `sonic-gnmi` → `sonic-gnm`. Use `str.removesuffix('.git')`.
- **NEVER compute days-behind as `now() - pinned_date`:** Use `HEAD_date - pinned_date` instead. A submodule whose upstream is dormant is NOT stale.
- **NEVER make all API calls concurrently:** Sequential with small delays avoids GitHub's secondary rate limits (abuse detection).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| INI-style `.gitmodules` parsing | Custom regex parser | `configparser` (stdlib) | Handles quoted section names, whitespace, multi-line values. Verified working on actual sonic-buildimage `.gitmodules`. |
| HTML generation | f-string concatenation | `Jinja2` templating | Escaping, loops, conditionals, template inheritance. Locked decision. |
| HTTP with auth headers | `urllib.request` boilerplate | `requests` library | Session objects, automatic JSON, clean error handling. Locked decision. |
| Retry with backoff | Manual loop | `time.sleep(2 ** attempt)` in a for-loop | Simple enough to inline — no library needed for 2-3 retries. |
| GitHub Pages deployment | `git push origin gh-pages` | `actions/deploy-pages` | Official action handles permissions, artifacts, environment URLs automatically. |

**Key insight:** The entire pipeline uses Python stdlib + 2 libraries (requests, jinja2). No build tools, no package managers for frontend, no complex infrastructure. Keep it simple.

## Common Pitfalls

### Pitfall 1: URL `.git` Suffix Mangling
**What goes wrong:** Using `rstrip('.git')` instead of `removesuffix('.git')` to strip `.git` from submodule URLs. `rstrip` treats the argument as a character set, so `sonic-gnmi.git` becomes `sonic-gnm` (strips trailing `i` too).
**Why it happens:** `rstrip` is the first thing developers reach for.
**How to avoid:** Always use `url.removesuffix('.git')`. Verified: sonic-gnmi is the only target submodule with `.git` suffix, but 25/49 total submodules have it.
**Warning signs:** 404 errors from GitHub API for repos with names ending in common `.git` characters.

### Pitfall 2: Comparing Against Wrong Branch
**What goes wrong:** Hardcoding `master` or using `default_branch` when a submodule tracks a specific branch.
**Why it happens:** 46/49 submodules have no explicit `branch` in `.gitmodules`, so "default branch" works for almost everything — making the bug invisible.
**How to avoid:** Check `.gitmodules` `branch` field first. If absent, query the repo's `default_branch` via API. For Phase 1's 10 targets: all use `master` and none have explicit branch fields. But code should still handle the general case for robustness.
**Warning signs:** Compare API returning `"status": "diverged"` instead of `"ahead"`.

### Pitfall 3: Wrong Days-Behind Computation
**What goes wrong:** Computing `now() - pinned_commit_date` instead of `HEAD_commit_date - pinned_commit_date`.
**Why it happens:** `now() - date` is simpler and seems equivalent.
**How to avoid:** For submodules with `commits_behind > 0`: fetch HEAD commit date on the branch, then compute `HEAD_date - pinned_date`. For submodules with `commits_behind == 0`: days_behind is 0 (they're identical).
**Warning signs:** A dormant upstream repo showing increasing "days behind" every day even though it's up to date.

### Pitfall 4: Name ≠ Path Mismatch in .gitmodules
**What goes wrong:** Using the submodule name (from `[submodule "name"]`) as the filesystem path for the Contents API call.
**Why it happens:** In 5/10 target submodules, the name IS the path leaf (e.g., `sonic-swss` → `src/sonic-swss`). But in 5/10, the name includes the `src/` prefix (e.g., name=`src/sonic-gnmi`, path=`src/sonic-gnmi`). The `path` field is the actual filesystem path needed for the API.
**How to avoid:** Always use the `path` field from `.gitmodules` for API calls. Use the `url` field to derive the GitHub repo slug.
**Warning signs:** 404 errors from Contents API.

### Pitfall 5: Jekyll Breaks GitHub Pages
**What goes wrong:** GitHub Pages runs Jekyll by default, which ignores files starting with `_`.
**Why it happens:** Not knowing about this behavior.
**How to avoid:** Include a `.nojekyll` file (empty) in the `site/` output directory.
**Warning signs:** Missing CSS/JS files on the deployed page, or entirely blank page.

### Pitfall 6: 60-Day Workflow Auto-Disable
**What goes wrong:** GitHub disables scheduled workflows after 60 days of no repository activity.
**Why it happens:** GitHub's policy to save resources. A dashboard-only repo may have no commits for months.
**How to avoid:** Either (a) commit `data.json` to the repo on each run (creates activity), or (b) add a README note about re-enabling. For Phase 1, option (a) is recommended since it also provides a history of dashboard states.
**Warning signs:** GitHub Actions tab showing the workflow as "disabled."

### Pitfall 7: Secondary Rate Limiting
**What goes wrong:** Making 30+ API requests rapidly triggers GitHub's abuse detection, returning 403 even within the rate limit.
**Why it happens:** GitHub has secondary limits on request velocity, not just total count.
**How to avoid:** Add a small delay between API calls (`time.sleep(0.5)` between submodule processing). 34 calls with 0.5s delay = 17 seconds total — acceptable.
**Warning signs:** Sporadic 403 responses with `Retry-After` header.

## Code Examples

### Example 1: Parse .gitmodules and Filter to Target Submodules

```python
# Source: Verified against actual sonic-buildimage .gitmodules
import configparser

TARGET_SUBMODULES = [
    "sonic-swss", "sonic-utilities", "sonic-platform-daemons",
    "sonic-sairedis", "sonic-gnmi", "sonic-swss-common",
    "sonic-platform-common", "sonic-host-services",
    "sonic-linux-kernel", "sonic-dash-ha",
]

def parse_gitmodules(content: str) -> list[dict]:
    """Parse .gitmodules content and return target submodule info."""
    parser = configparser.ConfigParser()
    parser.read_string(content)
    
    submodules = []
    for section in parser.sections():
        # Section format: 'submodule "name"'
        name = section.replace('submodule ', '').strip('"')
        url = parser.get(section, 'url', fallback='')
        path = parser.get(section, 'path', fallback='')
        branch = parser.get(section, 'branch', fallback=None)
        
        # Normalize URL: strip .git suffix and trailing slash
        clean_url = url.removesuffix('.git').rstrip('/')
        
        # Extract owner/repo from URL
        # e.g., "https://github.com/sonic-net/sonic-gnmi" → "sonic-net/sonic-gnmi"
        parts = clean_url.split('/')
        if len(parts) >= 2:
            repo_slug = parts[-1]  # e.g., "sonic-gnmi"
            owner = parts[-2]       # e.g., "sonic-net"
        else:
            continue
        
        # Filter to target submodules by repo slug
        if repo_slug in TARGET_SUBMODULES:
            submodules.append({
                "name": repo_slug,
                "path": path,
                "url": clean_url,
                "owner": owner,
                "repo": repo_slug,
                "branch": branch,  # None for most; used for branch-specific comparison
            })
    
    return submodules
```

### Example 2: Fetch Pinned SHA via Contents API

```python
# Source: Verified live — GET /repos/sonic-net/sonic-buildimage/contents/src/sonic-swss returns type="submodule"
def get_pinned_sha(session: requests.Session, submodule_path: str) -> str:
    """Get the pinned commit SHA for a submodule in sonic-buildimage."""
    url = f"https://api.github.com/repos/sonic-net/sonic-buildimage/contents/{submodule_path}"
    resp = session.get(url)
    resp.raise_for_status()
    data = resp.json()
    
    if data.get("type") != "submodule":
        raise ValueError(f"Path {submodule_path} is not a submodule (type={data.get('type')})")
    
    return data["sha"]
```

### Example 3: Compare Pinned vs Upstream HEAD

```python
# Source: Verified live — Compare API returns ahead_by, base_commit date, status
from datetime import datetime, timezone

def get_staleness(session: requests.Session, owner: str, repo: str, 
                  pinned_sha: str, branch: str) -> dict:
    """Get commits-behind and days-behind for a submodule."""
    url = f"https://api.github.com/repos/{owner}/{repo}/compare/{pinned_sha}...{branch}"
    resp = session.get(url)
    resp.raise_for_status()
    data = resp.json()
    
    commits_behind = data["ahead_by"]  # ahead_by = how many commits upstream has that pinned doesn't
    
    if commits_behind == 0:
        return {"commits_behind": 0, "days_behind": 0}
    
    # Get pinned commit date from base_commit
    pinned_date_str = data["base_commit"]["commit"]["committer"]["date"]
    pinned_date = datetime.fromisoformat(pinned_date_str.replace("Z", "+00:00"))
    
    # Get HEAD commit date on the branch
    head_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{branch}"
    head_resp = session.get(head_url)
    head_resp.raise_for_status()
    head_date_str = head_resp.json()["commit"]["committer"]["date"]
    head_date = datetime.fromisoformat(head_date_str.replace("Z", "+00:00"))
    
    days_behind = (head_date - pinned_date).days
    
    return {"commits_behind": commits_behind, "days_behind": max(0, days_behind)}
```

### Example 4: Jinja2 Template for Minimal HTML Table

```html
{# templates/dashboard.html #}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SONiC Submodule Status</title>
</head>
<body>
    <h1>SONiC Submodule Status</h1>
    <p>Last updated: {{ generated_at }}</p>
    <table>
        <thead>
            <tr>
                <th>Submodule</th>
                <th>Path</th>
                <th>Pinned SHA</th>
                <th>Commits Behind</th>
                <th>Days Behind</th>
                <th>Compare</th>
            </tr>
        </thead>
        <tbody>
            {% for sub in submodules %}
            <tr>
                <td>{{ sub.name }}</td>
                <td>{{ sub.path }}</td>
                <td>
                    {% if sub.status == "ok" %}
                        <code>{{ sub.pinned_sha[:7] }}</code>
                    {% else %}
                        <em>unavailable</em>
                    {% endif %}
                </td>
                <td>
                    {% if sub.status == "ok" %}
                        {{ sub.commits_behind }}
                    {% else %}
                        <em>{{ sub.error }}</em>
                    {% endif %}
                </td>
                <td>{{ sub.days_behind if sub.status == "ok" else "—" }}</td>
                <td>
                    {% if sub.compare_url %}
                        <a href="{{ sub.compare_url }}">View</a>
                    {% else %}
                        —
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
```

### Example 5: Workflow YAML

```yaml
# .github/workflows/update-dashboard.yml
name: Update Dashboard

on:
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM UTC
  workflow_dispatch:       # Manual trigger

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: dashboard-deploy
  cancel-in-progress: true

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install jinja2

      - name: Collect submodule data
        run: python scripts/collector.py
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Render dashboard
        run: python scripts/renderer.py

      - uses: actions/configure-pages@v5

      - uses: actions/upload-pages-artifact@v4
        with:
          path: ./site

      - id: deployment
        uses: actions/deploy-pages@v4
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `gh-pages` branch + `peaceiris/actions-gh-pages` | `actions/deploy-pages` (artifact-based) | 2023 | No branch management, no force-push, works with GITHUB_TOKEN. |
| `str.rstrip('.git')` | `str.removesuffix('.git')` | Python 3.9+ | Safe suffix removal without character-set mangling. |
| `datetime.strptime` for ISO dates | `datetime.fromisoformat` | Python 3.7+ (improved in 3.11) | Handles `Z` suffix in Python 3.11+. For 3.12 runners, this works natively. |
| Manual JSON handling | `requests.Response.json()` | Always available | No need for `json.loads(resp.text)`. |

## Verified Data: The 10 Target Submodules

Live-verified on 2026-03-20 against the actual sonic-buildimage `.gitmodules` and GitHub API:

| Target | .gitmodules Name | Path | URL Has .git? | Explicit Branch | Default Branch |
|--------|-----------------|------|---------------|-----------------|----------------|
| sonic-swss | `sonic-swss` | `src/sonic-swss` | No | No | master |
| sonic-utilities | `src/sonic-utilities` | `src/sonic-utilities` | No | No | master |
| sonic-platform-daemons | `src/sonic-platform-daemons` | `src/sonic-platform-daemons` | No | No | master |
| sonic-sairedis | `sonic-sairedis` | `src/sonic-sairedis` | No | No | master |
| sonic-gnmi | `src/sonic-gnmi` | `src/sonic-gnmi` | **Yes** | No | master |
| sonic-swss-common | `sonic-swss-common` | `src/sonic-swss-common` | No | No | master |
| sonic-platform-common | `src/sonic-platform-common` | `src/sonic-platform-common` | No | No | master |
| sonic-host-services | `src/sonic-host-services` | `src/sonic-host-services` | No | No | master |
| sonic-linux-kernel | `sonic-linux-kernel` | `src/sonic-linux-kernel` | No | No | master |
| sonic-dash-ha | `src/sonic-dash-ha` | `src/sonic-dash-ha` | No | No | master |

**Key observations:**
- All 10 targets have `master` as default branch — but code should NOT hardcode this
- Only sonic-gnmi has the `.git` URL suffix among our targets
- 5/10 have name = path leaf (e.g., `sonic-swss` → `src/sonic-swss`), 5/10 have name = full path (e.g., `src/sonic-gnmi` → `src/sonic-gnmi`)
- None of the 10 targets have an explicit `branch` field — all compare against default branch

### API Call Budget for 10 Submodules

| Operation | Calls | Notes |
|-----------|-------|-------|
| GET `.gitmodules` raw content | 1 | Parse to get path/URL/branch mapping |
| GET `/contents/{path}` per submodule | 10 | Get pinned SHA (type=submodule) |
| GET `/repos/{repo}` per submodule | 10 | Get default_branch (cacheable if all same org) |
| GET `/compare/{sha}...{branch}` per submodule | 10 | Get commits_behind (ahead_by) |
| GET `/commits/{branch}` per submodule (only if behind) | ~3 | Get HEAD date for days_behind calculation |
| **Total** | **~34** | **3.4% of 1,000/hour GITHUB_TOKEN limit** |

## Discretion Recommendations

### .gitmodules Parsing: Use `configparser`
**Recommendation:** `configparser` from stdlib.
**Reasoning:** Verified working on the actual 49-entry `.gitmodules` file. Handles quoted section names, tab-indented values, and all edge cases. No external dependency. Regex would be fragile and unnecessary.

### API Endpoint Choices: REST Contents + Compare
**Recommendation:** Contents API for pinned SHAs, Compare API for commits-behind, Commits endpoint for HEAD date.
**Reasoning:** All three endpoints verified live. The Contents API returns `type: "submodule"` with the pinned SHA directly — simpler than parsing the Git Trees API. The Compare API gives `ahead_by` accurately. Total: ~34 calls.
**Alternative considered:** Git Trees API (`/git/trees/master?recursive=true`) gets ALL submodule SHAs in one call (mode=160000), saving 9 calls. But it requires more complex filtering and the savings are negligible at 10 submodules.

### Retry Strategy: Exponential Backoff
**Recommendation:** 3 retries with exponential backoff: `sleep(2^attempt)` → 1s, 2s, 4s delays.
**Reasoning:** Simple, effective, respects GitHub's `Retry-After` guidance. Linear backoff would also work but exponential is the standard pattern.

### Workflow Structure: Single Job
**Recommendation:** Single job with sequential steps (collect → render → deploy).
**Reasoning:** Total runtime <30 seconds for data collection + rendering. Multi-job adds runner spin-up overhead and artifact-passing complexity for no benefit.

### .nojekyll Handling
**Recommendation:** Create an empty `.nojekyll` file in the `site/` directory during the render step.
**Reasoning:** Required to prevent GitHub Pages from running Jekyll processing. Without it, any directories starting with `_` would be silently dropped.

### Deployment Approach: `actions/deploy-pages` (NOT gh-pages branch)
**Recommendation:** Use `actions/deploy-pages` with artifact upload.
**Reasoning:** The user's stated intent is "keep dashboard separate from source code." `actions/deploy-pages` achieves this better than a `gh-pages` branch: no branch management, no force-push, no git history pollution with daily HTML commits, simpler permissions model. Pages source in repo settings must be set to "GitHub Actions" (not "Deploy from a branch").

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (latest) |
| Config file | None — see Wave 0 |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DATA-01 | Collector outputs 10 submodules with path and SHA | unit | `pytest tests/test_collector.py::test_outputs_10_submodules -x` | ❌ Wave 0 |
| DATA-02 | Commits-behind count matches compare API | unit | `pytest tests/test_collector.py::test_commits_behind -x` | ❌ Wave 0 |
| DATA-03 | Days-behind computed as HEAD_date - pinned_date | unit | `pytest tests/test_collector.py::test_days_behind_computation -x` | ❌ Wave 0 |
| DATA-04 | Compare URL has correct format | unit | `pytest tests/test_collector.py::test_compare_url_format -x` | ❌ Wave 0 |
| DATA-05 | Default branch resolved dynamically | unit | `pytest tests/test_collector.py::test_default_branch_resolution -x` | ❌ Wave 0 |
| DATA-06 | .gitmodules parsing handles edge cases | unit | `pytest tests/test_collector.py::test_gitmodules_parsing -x` | ❌ Wave 0 |
| CICD-01 | Workflow has cron schedule | manual-only | Verify YAML has `schedule.cron` field | N/A |
| CICD-02 | Workflow deploys to Pages | manual-only | Trigger workflow, check Pages URL | N/A |
| CICD-03 | <34 API calls per run | unit | `pytest tests/test_collector.py::test_api_call_count -x` | ❌ Wave 0 |
| CICD-04 | One submodule failure doesn't break pipeline | unit | `pytest tests/test_collector.py::test_graceful_failure -x` | ❌ Wave 0 |
| CICD-05 | Workflow has workflow_dispatch trigger | manual-only | Verify YAML has `workflow_dispatch` | N/A |
| UI-06 | Rendered HTML is valid page with table | unit | `pytest tests/test_renderer.py::test_html_output -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/ -x -q`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_collector.py` — covers DATA-01 through DATA-06, CICD-03, CICD-04
- [ ] `tests/test_renderer.py` — covers UI-06
- [ ] `tests/conftest.py` — shared fixtures (mock API responses, sample .gitmodules)
- [ ] `pytest.ini` or `pyproject.toml` — pytest configuration
- [ ] `requirements.txt` — include `jinja2` and `pytest` for dev/CI

## Open Questions

1. **How should sonic-buildimage's default ref be resolved?**
   - What we know: The `.gitmodules` content needs a `ref` parameter when fetched via API. Using `master` works today.
   - What's unclear: Whether sonic-buildimage might change its default branch from `master` to `main` in the future.
   - Recommendation: First query the repo's `default_branch`, then use that ref for `.gitmodules` fetch. Costs 1 extra API call but future-proofs the pipeline.

2. **Should we commit data.json for 60-day keepalive?**
   - What we know: GitHub disables scheduled workflows after 60 days of no repo activity.
   - What's unclear: Whether the `actions/deploy-pages` deployment counts as "activity."
   - Recommendation: For Phase 1, rely on manual re-enablement or periodic manual dispatches. Committing data.json would require `contents: write` permission and complicates the workflow. Defer this to a later concern.

3. **Should the 10 target submodules be hardcoded or config-file-driven?**
   - What we know: The user specified exactly 10 targets. Dynamic discovery from `.gitmodules` would find all 49.
   - What's unclear: Whether the list might change soon.
   - Recommendation: Hardcode the 10 names as a constant in `collector.py`. Parse all `.gitmodules` entries but filter to the target list. This is explicit and easy to modify.

## Sources

### Primary (HIGH confidence)
- **GitHub REST API — Contents endpoint**: Verified live. `GET /repos/sonic-net/sonic-buildimage/contents/src/sonic-swss` returns `type: "submodule"`, `sha: "c20ded7..."`. [Tested 2026-03-20]
- **GitHub REST API — Compare endpoint**: Verified live. `ahead_by` is accurate. `base_commit.commit.committer.date` provides pinned commit date. [Tested 2026-03-20]
- **GitHub REST API — Repos endpoint**: Verified live. All 10 targets return `default_branch: "master"`, `archived: false`. [Tested 2026-03-20]
- **sonic-buildimage .gitmodules**: Parsed locally. 49 submodules total, 10 targets verified with exact name/path/URL/branch fields. [Inspected 2026-03-20]
- **Python `configparser`**: Verified working on actual `.gitmodules` content. Handles quoted section names correctly. [Tested 2026-03-20]
- **URL suffix bug**: Verified: `"sonic-gnmi.git".rstrip(".git")` → `"sonic-gnm"` (WRONG). `"sonic-gnmi.git".removesuffix(".git")` → `"sonic-gnmi"` (correct). [Tested 2026-03-20]
- **Jinja2 3.1.6**: Latest version confirmed via `pip3 index versions jinja2`. [Checked 2026-03-20]
- **requests 2.32.5**: Latest version confirmed via `pip3 index versions requests`. [Checked 2026-03-20]

### Secondary (MEDIUM confidence)
- **STACK.md**: GitHub Actions versions (`actions/checkout@v4`, `actions/deploy-pages@v4`, etc.) verified against GitHub Releases API on 2025-07-18. May have newer versions now.
- **PITFALLS.md**: 14 pitfalls documented from repo analysis and GitHub docs. Most verified empirically.
- **ARCHITECTURE.md**: ETL pipeline pattern and project structure verified against actual constraints.

### Tertiary (LOW confidence)
- **60-day workflow disable**: Documented in GitHub Actions docs but exact "activity" definition is unclear (does Pages deployment count?). [Needs validation]
- **Secondary rate limiting thresholds**: GitHub doesn't publish exact velocity limits. 0.5s delay between calls is a conservative estimate. [Based on community experience]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified with current versions, API endpoints tested live
- Architecture: HIGH — two-stage pipeline with JSON intermediate is simple and proven
- Pitfalls: HIGH — all major pitfalls verified against actual data (URL mangling, name/path mismatch, wrong date computation)
- Validation: MEDIUM — test structure is standard pytest but no existing test infrastructure to build on

**Research date:** 2026-03-20
**Valid until:** 2026-04-20 (stable domain, no fast-moving dependencies)
