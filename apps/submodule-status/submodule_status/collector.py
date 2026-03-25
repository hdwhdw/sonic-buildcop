"""Collect submodule staleness data from sonic-net/sonic-buildimage via GitHub API."""
import base64
import configparser
import json
import logging
import time
from datetime import datetime, timezone

import requests

from buildcop_common.config import API_BASE, BOT_MAINTAINED, PARENT_OWNER, PARENT_REPO
from buildcop_common.exceptions import APIError
from buildcop_common.github import check_response, create_github_session, retry
from buildcop_common.log import setup_logging
from submodule_status.staleness import enrich_with_staleness
from submodule_status.enrichment import enrich_with_details

logger = logging.getLogger(__name__)


def parse_gitmodules(content: str) -> list[dict]:
    """Parse .gitmodules content and return target submodule info.

    Uses configparser to parse the INI-like format.  Normalises URLs by
    stripping trailing ``.git`` suffixes (via ``str.removesuffix`` — NOT
    ``rstrip`` which would mangle names like ``sonic-gnmi``).  Filters to
    only those repos owned by PARENT_OWNER (sonic-net) and present in BOT_MAINTAINED.
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
        if owner == PARENT_OWNER and repo_slug in BOT_MAINTAINED:
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
    url = f"{API_BASE}/repos/{PARENT_OWNER}/{PARENT_REPO}/contents/{submodule_path}"
    resp = session.get(url)
    check_response(resp)
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
    check_response(resp)
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
    check_response(resp)
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
        check_response(head_resp)
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


@retry(max_retries=2, base_delay=1.0, backoff_factor=2.0)
def _collect_submodule_data(
    session: requests.Session,
    submodule: dict,
) -> dict:
    """Inner collection logic — decorated with @retry for transient failures.

    @retry(max_retries=2) gives 3 total attempts (initial + 2 retries),
    matching the original manual retry loop. Backoff: sleep(1), sleep(2).
    """
    sha = get_pinned_sha(session, submodule["path"])

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


def collect_submodule(
    session: requests.Session,
    submodule: dict,
) -> dict:
    """Collect staleness data for a single submodule with retry logic.

    Delegates to _collect_submodule_data (decorated with @retry).
    On exhaustion, returns a dict with status='unavailable' and error message.
    """
    try:
        return _collect_submodule_data(session, submodule)
    except (APIError, requests.ConnectionError, requests.Timeout, ValueError, KeyError) as exc:
        logger.warning(
            "collect_submodule failed for %s: %s",
            submodule["name"], exc, exc_info=True,
        )
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
            "error": str(exc),
        }


def main():
    """Entry point: fetch .gitmodules, parse, collect staleness, write data.json."""
    setup_logging()
    session = create_github_session()

    # Fetch .gitmodules from sonic-buildimage
    gitmodules_url = (
        f"{API_BASE}/repos/{PARENT_OWNER}/{PARENT_REPO}/contents/.gitmodules"
    )
    resp = session.get(gitmodules_url)
    check_response(resp)
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
    logger.info("Collected %d submodules: %d ok, %d unavailable", len(results), ok_count, fail_count)


if __name__ == "__main__":
    main()
