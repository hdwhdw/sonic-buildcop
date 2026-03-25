"""Tests for the submodule staleness data collector."""
from unittest.mock import patch, MagicMock
import requests

from sonic_submodule_status.collector import (
    parse_gitmodules,
    get_pinned_sha,
    get_default_branch,
    get_staleness,
    build_compare_url,
    collect_submodule,
)


# ---------------------------------------------------------------------------
# parse_gitmodules tests
# ---------------------------------------------------------------------------


def test_parse_gitmodules_returns_bot_maintained_only(sample_gitmodules):
    """parse_gitmodules should return only bot-maintained sonic-net submodules."""
    result = parse_gitmodules(sample_gitmodules)
    assert len(result) == 10


def test_parse_gitmodules_extracts_path(sample_gitmodules):
    """All parsed submodule entries should have a path starting with src/."""
    result = parse_gitmodules(sample_gitmodules)
    for entry in result:
        assert entry["path"].startswith("src/"), f"{entry['name']} path={entry['path']}"


def test_parse_gitmodules_normalizes_git_suffix(sample_gitmodules):
    """sonic-gnmi URL should have .git suffix stripped."""
    result = parse_gitmodules(sample_gitmodules)
    gnmi = [e for e in result if e["name"] == "sonic-gnmi"]
    assert len(gnmi) == 1
    assert gnmi[0]["url"] == "https://github.com/sonic-net/sonic-gnmi"


def test_parse_gitmodules_extracts_repo_slug(sample_gitmodules):
    """Each result should have a repo field matching the target name."""
    result = parse_gitmodules(sample_gitmodules)
    expected_repos = {
        "sonic-swss", "sonic-utilities", "sonic-platform-daemons",
        "sonic-sairedis", "sonic-gnmi", "sonic-swss-common",
        "sonic-platform-common", "sonic-host-services",
        "sonic-linux-kernel", "sonic-dash-ha",
    }
    actual_repos = {e["repo"] for e in result}
    assert actual_repos == expected_repos


def test_parse_gitmodules_extracts_branch_when_present():
    """Parser should extract an explicit branch field when present."""
    # sonic-frr isn't bot-maintained, so test with a synthetic entry
    # that IS in BOT_MAINTAINED and has a branch field
    import sonic_submodule_status.collector as collector
    content = """\
[submodule "sonic-swss"]
\tpath = src/sonic-swss
\turl = https://github.com/sonic-net/sonic-swss
\tbranch = custom-branch
"""
    result = parse_gitmodules(content)
    assert len(result) == 1
    assert result[0]["branch"] == "custom-branch"


def test_parse_gitmodules_branch_none_when_absent(sample_gitmodules):
    """Submodules without explicit branch should have branch=None."""
    result = parse_gitmodules(sample_gitmodules)
    for entry in result:
        assert entry["branch"] is None, f"{entry['name']} has branch={entry['branch']}"


def test_parse_gitmodules_excludes_non_sonic_net(sample_gitmodules):
    """parse_gitmodules should exclude non-sonic-net and non-bot-maintained submodules."""
    result = parse_gitmodules(sample_gitmodules)
    owners = {e["owner"] for e in result}
    assert owners == {"sonic-net"}, f"Non-sonic-net owners found: {owners}"
    names = {e["name"] for e in result}
    assert "p4rt-app" not in names
    assert "sonic-build-tools" not in names
    assert "sonic-frr" not in names
    assert "sonic-dbsyncd" not in names
# ---------------------------------------------------------------------------


def test_get_pinned_sha(mock_contents_response):
    """get_pinned_sha should return the sha from a Contents API response."""
    session = MagicMock(spec=requests.Session)
    resp = MagicMock()
    resp.json.return_value = mock_contents_response
    session.get.return_value = resp

    sha = get_pinned_sha(session, "src/sonic-swss")
    assert sha == "abc123def4567890abc123def4567890abc123de"
    session.get.assert_called_once()


# ---------------------------------------------------------------------------
# get_default_branch tests
# ---------------------------------------------------------------------------


def test_get_default_branch(mock_repo_response):
    """get_default_branch should return the default_branch from Repos API."""
    session = MagicMock(spec=requests.Session)
    resp = MagicMock()
    resp.json.return_value = mock_repo_response
    session.get.return_value = resp

    branch = get_default_branch(session, "sonic-net", "sonic-swss")
    assert branch == "master"


# ---------------------------------------------------------------------------
# get_staleness tests
# ---------------------------------------------------------------------------


def test_get_staleness_when_behind(mock_compare_response):
    """get_staleness should return commits_behind=5 and days_behind based on now - first_ahead_date."""
    session = MagicMock(spec=requests.Session)

    resp_compare = MagicMock()
    resp_compare.json.return_value = mock_compare_response

    session.get.side_effect = [resp_compare]

    result = get_staleness(session, "sonic-net", "sonic-swss", "abc123", "master")
    assert result["commits_behind"] == 5
    # days_behind = now - first_ahead_commit_date (2025-01-20)
    # Should be a large positive number (over a year from now)
    assert result["days_behind"] > 0


def test_get_staleness_when_identical(mock_compare_response_identical):
    """get_staleness should return 0/0 when compare status is identical."""
    session = MagicMock(spec=requests.Session)
    resp = MagicMock()
    resp.json.return_value = mock_compare_response_identical
    session.get.return_value = resp

    result = get_staleness(session, "sonic-net", "sonic-swss", "abc123", "master")
    assert result["commits_behind"] == 0
    assert result["days_behind"] == 0


@patch("sonic_submodule_status.collector.datetime")
def test_get_staleness_uses_now_minus_first_ahead(mock_dt):
    """days_behind should be now - first_ahead_commit_date, not head - pinned."""
    from datetime import datetime, timezone

    fake_now = datetime(2025, 1, 25, 10, 0, 0, tzinfo=timezone.utc)
    mock_dt.now.return_value = fake_now
    mock_dt.fromisoformat = datetime.fromisoformat

    session = MagicMock(spec=requests.Session)
    resp = MagicMock()
    resp.json.return_value = {
        "ahead_by": 1,
        "commits": [
            {"commit": {"committer": {"date": "2025-01-24T10:00:00Z"}}},
        ],
    }
    session.get.return_value = resp

    result = get_staleness(session, "sonic-net", "sonic-swss", "abc123", "master")
    assert result["commits_behind"] == 1
    assert result["days_behind"] == 1.0  # 1 day since first ahead commit


# ---------------------------------------------------------------------------
# build_compare_url tests
# ---------------------------------------------------------------------------


def test_build_compare_url():
    """build_compare_url should return the correct GitHub compare URL."""
    url = build_compare_url("sonic-net", "sonic-swss", "abc123", "master")
    assert url == "https://github.com/sonic-net/sonic-swss/compare/abc123...master"


# ---------------------------------------------------------------------------
# collect_submodule tests
# ---------------------------------------------------------------------------


@patch("sonic_submodule_status.collector.time.sleep")
def test_collect_submodule_success(mock_sleep):
    """collect_submodule should return status=ok with all fields on success."""
    session = MagicMock(spec=requests.Session)

    # pinned sha response
    resp_sha = MagicMock()
    resp_sha.json.return_value = {
        "type": "submodule",
        "sha": "abc123def4567890abc123def4567890abc123de",
    }

    # default branch response
    resp_branch = MagicMock()
    resp_branch.json.return_value = {"default_branch": "master"}

    # compare response
    resp_compare = MagicMock()
    resp_compare.json.return_value = {
        "status": "ahead",
        "ahead_by": 5,
        "behind_by": 0,
        "base_commit": {
            "commit": {"committer": {"date": "2025-01-15T10:00:00Z"}}
        },
        "commits": [
            {"commit": {"committer": {"date": "2025-01-20T10:00:00Z"}}},
        ],
    }

    session.get.side_effect = [resp_sha, resp_branch, resp_compare]

    submodule = {
        "name": "sonic-swss",
        "path": "src/sonic-swss",
        "url": "https://github.com/sonic-net/sonic-swss",
        "owner": "sonic-net",
        "repo": "sonic-swss",
        "branch": None,
    }

    result = collect_submodule(session, submodule)
    assert result["status"] == "ok"
    assert result["pinned_sha"] == "abc123def4567890abc123def4567890abc123de"
    assert result["branch"] == "master"
    assert result["commits_behind"] == 5
    assert result["days_behind"] > 0  # now - 2025-01-20
    assert result["compare_url"] == "https://github.com/sonic-net/sonic-swss/compare/abc123def4567890abc123def4567890abc123de...master"
    assert result["error"] is None


@patch("sonic_submodule_status.collector.time.sleep")
def test_collect_submodule_retries_on_failure(mock_sleep):
    """collect_submodule should retry on failure and succeed on the 3rd try."""
    session = MagicMock(spec=requests.Session)

    # First two calls raise, then succeed for all four API calls
    resp_sha = MagicMock()
    resp_sha.json.return_value = {
        "type": "submodule",
        "sha": "abc123def4567890abc123def4567890abc123de",
    }
    resp_branch = MagicMock()
    resp_branch.json.return_value = {"default_branch": "master"}
    resp_compare = MagicMock()
    resp_compare.json.return_value = {
        "status": "identical",
        "ahead_by": 0,
        "behind_by": 0,
        "base_commit": {
            "commit": {"committer": {"date": "2025-01-15T10:00:00Z"}}
        },
    }

    session.get.side_effect = [
        requests.RequestException("timeout"),
        requests.RequestException("timeout"),
        resp_sha,
        resp_branch,
        resp_compare,
    ]

    submodule = {
        "name": "sonic-swss",
        "path": "src/sonic-swss",
        "url": "https://github.com/sonic-net/sonic-swss",
        "owner": "sonic-net",
        "repo": "sonic-swss",
        "branch": None,
    }

    result = collect_submodule(session, submodule)
    assert result["status"] == "ok"
    assert session.get.call_count >= 3


@patch("sonic_submodule_status.collector.time.sleep")
def test_collect_submodule_unavailable_after_retries(mock_sleep):
    """collect_submodule should return status=unavailable after exhausting retries."""
    session = MagicMock(spec=requests.Session)
    session.get.side_effect = requests.RequestException("API down")

    submodule = {
        "name": "sonic-swss",
        "path": "src/sonic-swss",
        "url": "https://github.com/sonic-net/sonic-swss",
        "owner": "sonic-net",
        "repo": "sonic-swss",
        "branch": None,
    }

    result = collect_submodule(session, submodule)
    assert result["status"] == "unavailable"
    assert result["error"] is not None
    assert isinstance(result["error"], str)
    assert result["pinned_sha"] is None
    assert result["commits_behind"] is None
    assert result["days_behind"] is None
