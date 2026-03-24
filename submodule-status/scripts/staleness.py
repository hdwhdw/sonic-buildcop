"""Staleness computation module for submodule cadence analysis.

Computes per-submodule staleness thresholds from pointer bump history
in sonic-buildimage and classifies each submodule as green/yellow/red
based on how far behind its pinned SHA is relative to its bump cadence.

Exports:
    get_bump_dates    — fetch pointer bump dates from sonic-buildimage
    compute_cadence   — compute median inter-bump interval
    compute_thresholds — derive yellow/red thresholds from cadence
    classify          — classify days/commits behind as green/yellow/red
    enrich_with_staleness — enrich submodule dicts with staleness fields
"""
import statistics
import time
from datetime import datetime, timezone, timedelta

import requests

# --- Constants ---

MIN_BUMPS_FOR_CADENCE = 5
MIN_MEDIAN_DAYS = 1.0
MAX_YELLOW_DAYS = 30
MAX_RED_DAYS = 60

FALLBACK_THRESHOLDS = {
    "yellow_days": 30,
    "red_days": 60,
    "is_fallback": True,
}

API_BASE = "https://api.github.com"
PARENT_OWNER = "sonic-net"
PARENT_REPO = "sonic-buildimage"
NUM_BUMPS = 30


# --- Functions ---


def get_bump_dates(
    session: requests.Session,
    submodule_path: str,
    num_bumps: int = NUM_BUMPS,
) -> list[datetime]:
    """Fetch pointer bump dates from sonic-buildimage commit log.

    Queries commits in sonic-buildimage that touched ``submodule_path``
    (i.e., pointer bump commits). Returns a sorted (ascending) list of
    datetime objects for the last ``num_bumps`` bumps.

    Returns an empty list on API error or unexpected response format.
    """
    url = f"{API_BASE}/repos/{PARENT_OWNER}/{PARENT_REPO}/commits"
    params = {"path": submodule_path, "per_page": num_bumps}

    try:
        resp = session.get(url, params=params)
        resp.raise_for_status()
        commits = resp.json()
    except (requests.RequestException, KeyError, ValueError):
        return []

    if not isinstance(commits, list):
        return []

    dates: list[datetime] = []
    for commit in commits:
        try:
            date_str = commit["commit"]["committer"]["date"]
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            dates.append(dt)
        except (KeyError, ValueError):
            continue

    dates.sort()
    return dates


def compute_cadence(bump_dates: list[datetime]) -> dict:
    """Compute median inter-bump interval from sorted bump dates.

    Returns a dict with:
        median_days  — median interval in days (or None if fallback)
        commit_count — total number of bumps
        is_fallback  — True if too few bumps for reliable cadence

    If fewer than MIN_BUMPS_FOR_CADENCE bumps, returns fallback mode.
    Zero or near-zero medians are floored to MIN_MEDIAN_DAYS.
    """
    count = len(bump_dates)
    if count < MIN_BUMPS_FOR_CADENCE:
        return {
            "median_days": None,
            "commit_count": count,
            "is_fallback": True,
        }

    # Compute intervals between consecutive bumps (in days)
    intervals = [
        (bump_dates[i + 1] - bump_dates[i]).total_seconds() / 86400
        for i in range(count - 1)
    ]

    median = max(statistics.median(intervals), MIN_MEDIAN_DAYS)

    return {
        "median_days": median,
        "commit_count": count,
        "is_fallback": False,
    }


def compute_thresholds(cadence: dict) -> dict:
    """Derive yellow/red day thresholds from cadence data.

    For normal repos: 2× median = yellow, 4× median = red (days), capped at MAX_YELLOW_DAYS/MAX_RED_DAYS.
    For fallback repos (<5 commits): use FALLBACK_THRESHOLDS.
    """
    if cadence["is_fallback"]:
        return dict(FALLBACK_THRESHOLDS)

    m = cadence["median_days"]
    return {
        "yellow_days": min(round(2 * m, 1), MAX_YELLOW_DAYS),
        "red_days": min(round(4 * m, 1), MAX_RED_DAYS),
        "is_fallback": False,
    }


def classify(days_behind: float, thresholds: dict) -> str:
    """Classify staleness as green/yellow/red based on days behind only.

    Commits behind is shown for reference but does not affect classification.
    """
    if days_behind > thresholds["red_days"]:
        return "red"
    if days_behind > thresholds["yellow_days"]:
        return "yellow"
    return "green"


def enrich_with_staleness(
    session: requests.Session,
    submodules: list[dict],
) -> None:
    """Enrich submodule dicts in-place with staleness classification.

    For each submodule with status='ok':
        - Fetches pointer bump history from sonic-buildimage
        - Computes cadence and thresholds
        - Classifies as green/yellow/red

    For unavailable submodules, sets all staleness fields to None.

    Adds fields: staleness_status, median_days, commit_count_6m, thresholds
    """
    for sub in submodules:
        if sub["status"] != "ok":
            sub["staleness_status"] = None
            sub["median_days"] = None
            sub["commit_count_6m"] = None
            sub["thresholds"] = None
            continue

        try:
            dates = get_bump_dates(session, sub["path"])
            cadence = compute_cadence(dates)
            thresholds = compute_thresholds(cadence)
            status = classify(sub["days_behind"], thresholds)

            sub["staleness_status"] = status
            sub["median_days"] = cadence["median_days"]
            sub["commit_count_6m"] = cadence["commit_count"]
            sub["thresholds"] = thresholds

        except (requests.RequestException, KeyError, ValueError):
            sub["staleness_status"] = None
            sub["median_days"] = None
            sub["commit_count_6m"] = None
            sub["thresholds"] = None

        time.sleep(0.5)  # Rate-limit courtesy delay between submodules
