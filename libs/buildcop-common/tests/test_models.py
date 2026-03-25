"""Tests for buildcop_common.models — TypedDict data models."""
from buildcop_common.models import (
    SubmoduleInfo, OpenBotPR, LastMergedBotPR,
    LatestRepoCommit, Cadence, Thresholds,
)


def test_typeddict_import():
    """All 6 TypedDicts importable."""
    assert SubmoduleInfo is not None
    assert OpenBotPR is not None
    assert LastMergedBotPR is not None
    assert LatestRepoCommit is not None
    assert Cadence is not None
    assert Thresholds is not None


def test_submoduleinfo_base_fields():
    """SubmoduleInfo requires base fields from parse_gitmodules."""
    info: SubmoduleInfo = {
        "name": "sonic-swss",
        "path": "src/sonic-swss",
        "url": "https://github.com/sonic-net/sonic-swss",
        "owner": "sonic-net",
        "repo": "sonic-swss",
        "branch": "master",
    }
    assert info["name"] == "sonic-swss"
    assert info["branch"] == "master"


def test_progressive_construction():
    """Pipeline-stage fields can be added progressively."""
    info: SubmoduleInfo = {
        "name": "sonic-swss",
        "path": "src/sonic-swss",
        "url": "https://github.com/sonic-net/sonic-swss",
        "owner": "sonic-net",
        "repo": "sonic-swss",
        "branch": "master",
    }
    # After collect_submodule
    info["status"] = "ok"
    info["pinned_sha"] = "abc123"
    info["commits_behind"] = 5
    info["days_behind"] = 14.2
    info["compare_url"] = "https://github.com/..."
    info["error"] = None
    assert info["status"] == "ok"
    assert info["commits_behind"] == 5


def test_nested_typedicts():
    """Nested TypedDicts for PR, commit, cadence, threshold data."""
    pr: OpenBotPR = {"url": "https://...", "age_days": 2.5, "ci_status": "success"}
    assert pr["age_days"] == 2.5

    merged: LastMergedBotPR = {"url": "https://...", "merged_at": "2024-01-15T10:00:00Z"}
    assert merged["merged_at"] is not None

    commit: LatestRepoCommit = {"url": "https://...", "date": "2024-01-15T10:00:00Z"}
    assert commit["date"] == "2024-01-15T10:00:00Z"

    cadence: Cadence = {"median_days": 7.0, "commit_count": 10, "is_fallback": False}
    assert cadence["median_days"] == 7.0

    thresh: Thresholds = {"yellow_days": 14.0, "red_days": 28.0, "is_fallback": False}
    assert thresh["red_days"] == 28.0


def test_submoduleinfo_with_nested():
    """SubmoduleInfo can hold nested TypedDicts."""
    info: SubmoduleInfo = {
        "name": "sonic-swss",
        "path": "src/sonic-swss",
        "url": "https://github.com/sonic-net/sonic-swss",
        "owner": "sonic-net",
        "repo": "sonic-swss",
        "branch": "master",
        "status": "ok",
        "open_bot_pr": {"url": "https://...", "age_days": 1.0, "ci_status": "success"},
        "thresholds": {"yellow_days": 14.0, "red_days": 28.0, "is_fallback": False},
    }
    assert info["open_bot_pr"]["ci_status"] == "success"
    assert info["thresholds"]["yellow_days"] == 14.0
