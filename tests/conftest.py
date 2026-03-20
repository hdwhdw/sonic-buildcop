"""Shared test fixtures for collector tests."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

import pytest


@pytest.fixture
def sample_gitmodules():
    """Multi-line .gitmodules INI string with 12 entries (10 targets + 2 non-targets)."""
    return """\
[submodule "sonic-swss"]
\tpath = src/sonic-swss
\turl = https://github.com/sonic-net/sonic-swss

[submodule "src/sonic-utilities"]
\tpath = src/sonic-utilities
\turl = https://github.com/sonic-net/sonic-utilities

[submodule "src/sonic-platform-daemons"]
\tpath = src/sonic-platform-daemons
\turl = https://github.com/sonic-net/sonic-platform-daemons

[submodule "sonic-sairedis"]
\tpath = src/sonic-sairedis
\turl = https://github.com/sonic-net/sonic-sairedis

[submodule "src/sonic-gnmi"]
\tpath = src/sonic-gnmi
\turl = https://github.com/sonic-net/sonic-gnmi.git

[submodule "sonic-swss-common"]
\tpath = src/sonic-swss-common
\turl = https://github.com/sonic-net/sonic-swss-common

[submodule "src/sonic-platform-common"]
\tpath = src/sonic-platform-common
\turl = https://github.com/sonic-net/sonic-platform-common

[submodule "src/sonic-host-services"]
\tpath = src/sonic-host-services
\turl = https://github.com/sonic-net/sonic-host-services

[submodule "sonic-linux-kernel"]
\tpath = src/sonic-linux-kernel
\turl = https://github.com/sonic-net/sonic-linux-kernel

[submodule "src/sonic-dash-ha"]
\tpath = src/sonic-dash-ha
\turl = https://github.com/sonic-net/sonic-dash-ha

[submodule "sonic-frr"]
\tpath = src/sonic-frr
\turl = https://github.com/sonic-net/sonic-frr
\tbranch = frr-10.4.1

[submodule "sonic-dbsyncd"]
\tpath = src/sonic-dbsyncd
\turl = https://github.com/sonic-net/sonic-dbsyncd
"""


@pytest.fixture
def mock_contents_response():
    """Mock GitHub Contents API response for a submodule entry."""
    return {
        "type": "submodule",
        "sha": "abc123def4567890abc123def4567890abc123de",
        "name": "src/sonic-swss",
        "path": "src/sonic-swss",
    }


@pytest.fixture
def mock_compare_response():
    """Mock GitHub Compare API response when submodule is behind."""
    return {
        "status": "ahead",
        "ahead_by": 5,
        "behind_by": 0,
        "base_commit": {
            "commit": {
                "committer": {
                    "date": "2025-01-15T10:00:00Z"
                }
            }
        },
    }


@pytest.fixture
def mock_compare_response_identical():
    """Mock GitHub Compare API response when submodule is identical."""
    return {
        "status": "identical",
        "ahead_by": 0,
        "behind_by": 0,
        "base_commit": {
            "commit": {
                "committer": {
                    "date": "2025-01-15T10:00:00Z"
                }
            }
        },
    }


@pytest.fixture
def mock_head_commit_response():
    """Mock GitHub Commits API response for HEAD commit."""
    return {
        "commit": {
            "committer": {
                "date": "2025-02-20T10:00:00Z"
            }
        }
    }


@pytest.fixture
def mock_repo_response():
    """Mock GitHub Repos API response."""
    return {
        "default_branch": "master",
        "archived": False,
    }


# ---------------------------------------------------------------------------
# Phase 2: Staleness module fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_commits_page_1():
    """Page 1 of GitHub Commits API response — 5 commits, 1-day intervals."""
    return [
        {"commit": {"committer": {"date": "2025-08-01T10:00:00Z"}}},
        {"commit": {"committer": {"date": "2025-08-02T10:00:00Z"}}},
        {"commit": {"committer": {"date": "2025-08-03T10:00:00Z"}}},
        {"commit": {"committer": {"date": "2025-08-04T10:00:00Z"}}},
        {"commit": {"committer": {"date": "2025-08-05T10:00:00Z"}}},
    ]


@pytest.fixture
def mock_commits_page_2():
    """Page 2 of GitHub Commits API response — 3 more commits."""
    return [
        {"commit": {"committer": {"date": "2025-08-06T10:00:00Z"}}},
        {"commit": {"committer": {"date": "2025-08-07T10:00:00Z"}}},
        {"commit": {"committer": {"date": "2025-08-08T10:00:00Z"}}},
    ]


@pytest.fixture
def sample_submodule_ok():
    """A single submodule dict with status='ok' — input to enrich_with_staleness."""
    return {
        "name": "sonic-swss",
        "path": "src/sonic-swss",
        "url": "https://github.com/sonic-net/sonic-swss",
        "owner": "sonic-net",
        "repo": "sonic-swss",
        "pinned_sha": "abc123def4567890abc123def4567890abc123de",
        "branch": "master",
        "commits_behind": 42,
        "days_behind": 15,
        "compare_url": "https://github.com/sonic-net/sonic-swss/compare/abc123...master",
        "status": "ok",
        "error": None,
    }


@pytest.fixture
def sample_submodule_unavailable():
    """A single submodule dict with status='unavailable'."""
    return {
        "name": "sonic-swss",
        "path": "src/sonic-swss",
        "url": "https://github.com/sonic-net/sonic-swss",
        "owner": "sonic-net",
        "repo": "sonic-swss",
        "pinned_sha": None,
        "branch": None,
        "commits_behind": None,
        "days_behind": None,
        "compare_url": None,
        "status": "unavailable",
        "error": "API down",
    }
