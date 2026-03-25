"""Collect submodule staleness data from sonic-net/sonic-buildimage via GitHub API."""
import base64
import configparser
import json
import os
import time
from datetime import datetime, timezone

import requests

from sonic_submodule_status.staleness import enrich_with_staleness
from sonic_submodule_status.enrichment import enrich_with_details

REPO_OWNER = "sonic-net"
PARENT_REPO = "sonic-buildimage"
API_BASE = "https://api.github.com"

# Submodules actively maintained by the mssonicbld bot.
# Only these are tracked on the dashboard — unmaintained repos are noise.
BOT_MAINTAINED = {
    "sonic-swss",
    "sonic-sairedis",
    "sonic-platform-daemons",
    "sonic-utilities",
    "sonic-swss-common",
    "sonic-linux-kernel",
    "sonic-platform-common",
    "sonic-dash-ha",
    "dhcprelay",
    "sonic-gnmi",
    "sonic-ztp",
    "sonic-host-services",
    "sonic-dash-api",
    "sonic-mgmt-common",
    "sonic-bmp",
    "sonic-wpa-supplicant",
}


def parse_gitmodules(content: str) -> list[dict]:
    """Parse .gitmodules content and return target submodule info.

    Uses configparser to parse the INI-like format.  Normalises URLs by
    stripping trailing ``.git`` suffixes (via ``str.removesuffix`` — NOT
    ``rstrip`` which would mangle names like ``sonic-gnmi``).  Filters to
    only those repos owned by REPO_OWNER (sonic-net) and present in BOT_MAINTAINED.
    """
    parser = configparser.ConfigParser()
    parser.read_string(content)

    submodules = []
    for section in parser.sections():
        # Section format: 'submodule "name"'
        name = section.replace('submodule ', '').strip('"')
        url = parser.get(section, 'url', fallback='')
        path = parser.get(section, 'path', fallback='')
        branch = parser.get(section, 'branch', fallback=None)

        # CRITICAL: use .removesuffix() not .rstrip() — rstrip('.git') mangles
        # 'sonic-gnmi' to 'sonic-gnm'
        clean_url = url.removesuffix('.git').rstrip('/')

        # Extract owner/repo from URL
        parts = clean_url.split('/')
        if len(parts) >= 2:
            repo_slug = parts[-1]
            owner = parts[-2]
        else:
            continue

        # Filter to bot-maintained sonic-net submodules
        if owner == REPO_OWNER and repo_slug in BOT_MAINTAINED:
            submodules.append({
                "name": repo_slug,
                "path": path,
                "url": clean_url,
                "owner": owner,
                "repo": repo_slug,
                "branch": branch,
            })

    return submodules


def get_pinned_sha(session: requests.Session, submodule_path: str) -> str:
    """Get the pinned commit SHA for a submodule in sonic-buildimage."""
    url = f"{API_BASE}/repos/{REPO_OWNER}/{PARENT_REPO}/contents/{submodule_path}"
    resp = session.get(url)
    resp.raise_for_status()
    data = resp.json()

    if data.get("type") != "submodule":
        raise ValueError(
            f"Path {submodule_path} is not a submodule (type={data.get('type')})"
        )

    return data["sha"]


def get_default_branch(session: requests.Session, owner: str, repo: str) -> str:
    """Get the default branch name for a GitHub repo."""
    url = f"{API_BASE}/repos/{owner}/{repo}"
    resp = session.get(url)
    resp.raise_for_status()
    return resp.json()["default_branch"]


def get_staleness(
    session: requests.Session,
    owner: str,
    repo: str,
    pinned_sha: str,
    branch: str,
) -> dict:
    """Get commits-behind and days-behind for a submodule.

    Uses the Compare API's ``ahead_by`` field for commit count, and computes
    days as ``now - date(first commit after pinned)`` to measure real staleness
    time (how long the pointer has been behind).
    """
    compare_url = f"{API_BASE}/repos/{owner}/{repo}/compare/{pinned_sha}...{branch}"
    resp = session.get(compare_url)
    resp.raise_for_status()
    data = resp.json()

    commits_behind = data["ahead_by"]

    if commits_behind == 0:
        return {"commits_behind": 0, "days_behind": 0}

    # Find the oldest commit after pinned (first in the ahead list)
    commits_ahead = data.get("commits", [])
    if commits_ahead:
        first_ahead_date_str = commits_ahead[0]["commit"]["committer"]["date"]
        first_ahead_date = datetime.fromisoformat(
            first_ahead_date_str.replace("Z", "+00:00")
        )
    else:
        # Fallback: use HEAD commit date if commits list is empty
        head_url = f"{API_BASE}/repos/{owner}/{repo}/commits/{branch}"
        head_resp = session.get(head_url)
        head_resp.raise_for_status()
        first_ahead_date_str = head_resp.json()["commit"]["committer"]["date"]
        first_ahead_date = datetime.fromisoformat(
            first_ahead_date_str.replace("Z", "+00:00")
        )

    now = datetime.now(timezone.utc)
    days_behind = round((now - first_ahead_date).total_seconds() / 86400, 1)

    return {"commits_behind": commits_behind, "days_behind": max(0, days_behind)}


def build_compare_url(owner: str, repo: str, pinned_sha: str, branch: str) -> str:
    """Build a GitHub compare URL for visual diff."""
    return f"https://github.com/{owner}/{repo}/compare/{pinned_sha}...{branch}"


def collect_submodule(
    session: requests.Session,
    submodule: dict,
    retries: int = 3,
) -> dict:
    """Collect staleness data for a single submodule with retry logic.

    Retries up to ``retries`` times with exponential backoff.  On exhaustion,
    returns a dict with ``status='unavailable'`` and an error message.
    """
    last_error = None
    for attempt in range(retries):
        try:
            sha = get_pinned_sha(session, submodule["path"])

            # Resolve branch: use explicit branch from .gitmodules, or query
            # the repo's default branch via API.
            branch = submodule.get("branch") or get_default_branch(
                session, submodule["owner"], submodule["repo"]
            )

            staleness = get_staleness(
                session, submodule["owner"], submodule["repo"], sha, branch
            )

            compare_url = build_compare_url(
                submodule["owner"], submodule["repo"], sha, branch
            )

            return {
                "name": submodule["name"],
                "path": submodule["path"],
                "url": submodule["url"],
                "owner": submodule["owner"],
                "repo": submodule["repo"],
                "pinned_sha": sha,
                "branch": branch,
                "commits_behind": staleness["commits_behind"],
                "days_behind": staleness["days_behind"],
                "compare_url": compare_url,
                "status": "ok",
                "error": None,
            }

        except (requests.RequestException, ValueError, KeyError) as exc:
            last_error = exc
            if attempt < retries - 1:
                time.sleep(2 ** attempt)

    # All retries exhausted
    return {
        "name": submodule["name"],
        "path": submodule["path"],
        "url": submodule["url"],
        "owner": submodule["owner"],
        "repo": submodule["repo"],
        "pinned_sha": None,
        "branch": None,
        "commits_behind": None,
        "days_behind": None,
        "compare_url": None,
        "status": "unavailable",
        "error": str(last_error),
    }


def main():
    """Entry point: fetch .gitmodules, parse, collect staleness, write data.json."""
    token = os.environ.get("GITHUB_TOKEN", "")

    session = requests.Session()
    session.headers.update({
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    })

    # Fetch .gitmodules from sonic-buildimage
    gitmodules_url = (
        f"{API_BASE}/repos/{REPO_OWNER}/{PARENT_REPO}/contents/.gitmodules"
    )
    resp = session.get(gitmodules_url)
    resp.raise_for_status()
    content = base64.b64decode(resp.json()["content"]).decode("utf-8")

    # Parse and filter to target submodules
    submodule_defs = parse_gitmodules(content)

    # Collect staleness data for each target submodule
    results = []
    for submodule_def in submodule_defs:
        result = collect_submodule(session, submodule_def)
        results.append(result)
        time.sleep(0.5)  # Rate-limit courtesy delay

    # Enrich with cadence-aware staleness classification
    enrich_with_staleness(session, results)

    # Enrich with detail data (bot PRs, latest commits, avg delay)
    enrich_with_details(session, results)

    # Write output
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "submodules": results,
    }
    with open("data.json", "w") as f:
        json.dump(output, f, indent=2)

    # Summary
    ok_count = sum(1 for r in results if r["status"] == "ok")
    fail_count = sum(1 for r in results if r["status"] == "unavailable")
    print(f"Collected {len(results)} submodules: {ok_count} ok, {fail_count} unavailable")


if __name__ == "__main__":
    main()
