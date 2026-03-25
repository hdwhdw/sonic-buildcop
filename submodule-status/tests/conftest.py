"""Shared test fixtures for collector tests."""

import pytest


@pytest.fixture
def sample_gitmodules():
    """Multi-line .gitmodules INI string with 14 entries (12 sonic-net + 2 non-sonic-net)."""
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

[submodule "p4rt-app"]
\tpath = src/p4rt-app
\turl = https://github.com/p4lang/p4rt-app

[submodule "sonic-build-tools"]
\tpath = src/sonic-build-tools
\turl = https://github.com/Azure/sonic-build-tools
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
        "commits": [
            {
                "commit": {
                    "committer": {
                        "date": "2025-01-20T10:00:00Z"
                    }
                }
            },
        ],
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
def mock_bump_response():
    """Mock sonic-buildimage commits API response — 5 pointer bump commits."""
    return [
        {"commit": {"committer": {"date": "2025-08-05T10:00:00Z"}}},
        {"commit": {"committer": {"date": "2025-08-01T10:00:00Z"}}},
        {"commit": {"committer": {"date": "2025-08-03T10:00:00Z"}}},
        {"commit": {"committer": {"date": "2025-08-02T10:00:00Z"}}},
        {"commit": {"committer": {"date": "2025-08-04T10:00:00Z"}}},
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


# ---------------------------------------------------------------------------
# Phase 6: Enrichment module fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_submodule_list():
    """Two ok submodules + one unavailable for enrichment testing."""
    return [
        {
            "name": "sonic-swss",
            "path": "src/sonic-swss",
            "url": "https://github.com/sonic-net/sonic-swss",
            "owner": "sonic-net",
            "repo": "sonic-swss",
            "branch": "master",
            "status": "ok",
            "error": None,
        },
        {
            "name": "sonic-swss-common",
            "path": "src/sonic-swss-common",
            "url": "https://github.com/sonic-net/sonic-swss-common",
            "owner": "sonic-net",
            "repo": "sonic-swss-common",
            "branch": "master",
            "status": "ok",
            "error": None,
        },
        {
            "name": "sonic-sairedis",
            "path": "src/sonic-sairedis",
            "url": "https://github.com/sonic-net/sonic-sairedis",
            "owner": "sonic-net",
            "repo": "sonic-sairedis",
            "branch": "master",
            "status": "unavailable",
            "error": "API down",
        },
    ]


@pytest.fixture
def mock_search_open_prs():
    """Mock GitHub Search Issues API response — 2 open bot PRs."""
    return {
        "total_count": 2,
        "items": [
            {
                "number": 101,
                "title": "[submodule] Update submodule src/sonic-swss to latest",
                "html_url": "https://github.com/sonic-net/sonic-buildimage/pull/101",
                "created_at": "2025-02-15T10:00:00Z",
                "pull_request": {"merged_at": None},
            },
            {
                "number": 102,
                "title": "[submodule] Update submodule src/sonic-swss-common to latest",
                "html_url": "https://github.com/sonic-net/sonic-buildimage/pull/102",
                "created_at": "2025-02-18T10:00:00Z",
                "pull_request": {"merged_at": None},
            },
        ],
    }


@pytest.fixture
def mock_search_merged_prs():
    """Mock GitHub Search Issues API response — 1 merged bot PR."""
    return {
        "total_count": 1,
        "items": [
            {
                "number": 99,
                "title": "[submodule] Update submodule src/sonic-swss to latest",
                "html_url": "https://github.com/sonic-net/sonic-buildimage/pull/99",
                "created_at": "2025-01-10T10:00:00Z",
                "pull_request": {"merged_at": "2025-01-12T15:30:00Z"},
            },
        ],
    }


@pytest.fixture
def mock_check_runs_all_pass():
    """Mock Check Runs API — all checks passed."""
    return {
        "total_count": 3,
        "check_runs": [
            {"name": "build", "status": "completed", "conclusion": "success"},
            {"name": "lint", "status": "completed", "conclusion": "success"},
            {"name": "test", "status": "completed", "conclusion": "neutral"},
        ],
    }


@pytest.fixture
def mock_check_runs_one_fail():
    """Mock Check Runs API — one check failed."""
    return {
        "total_count": 3,
        "check_runs": [
            {"name": "build", "status": "completed", "conclusion": "success"},
            {"name": "lint", "status": "completed", "conclusion": "failure"},
            {"name": "test", "status": "completed", "conclusion": "success"},
        ],
    }


@pytest.fixture
def mock_check_runs_pending():
    """Mock Check Runs API — one check still running."""
    return {
        "total_count": 2,
        "check_runs": [
            {"name": "build", "status": "completed", "conclusion": "success"},
            {"name": "test", "status": "in_progress", "conclusion": None},
        ],
    }


@pytest.fixture
def mock_check_runs_empty():
    """Mock Check Runs API — no checks configured."""
    return {"total_count": 0, "check_runs": []}


@pytest.fixture
def mock_latest_commit_response():
    """Mock GitHub Commits API response for HEAD commit with html_url."""
    return {
        "sha": "def456abc789",
        "html_url": "https://github.com/sonic-net/sonic-swss/commit/def456abc789",
        "commit": {
            "committer": {
                "date": "2025-02-19T08:00:00Z"
            }
        },
    }


@pytest.fixture
def mock_pr_detail_response():
    """Mock GitHub Pull Request API response with head SHA."""
    return {
        "number": 101,
        "head": {"sha": "abc123headsha"},
    }


# ---------------------------------------------------------------------------
# Phase 6 Plan 02: Average delay fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_bump_commits():
    """Mock pointer bump commits in sonic-buildimage for a submodule path."""
    return [
        {
            "sha": "bump_sha_1",
            "commit": {"committer": {"date": "2025-02-10T12:00:00Z"}},
        },
        {
            "sha": "bump_sha_2",
            "commit": {"committer": {"date": "2025-02-05T12:00:00Z"}},
        },
        {
            "sha": "bump_sha_3",
            "commit": {"committer": {"date": "2025-01-30T12:00:00Z"}},
        },
    ]


@pytest.fixture
def mock_contents_at_bump():
    """Mock Contents API response showing submodule SHA at a bump ref."""
    return {
        "type": "submodule",
        "sha": "sub_commit_sha_abc",
    }


@pytest.fixture
def mock_sub_commit_dates():
    """Three submodule commit date responses — delays of 2, 3, and 4 days."""
    return [
        {"commit": {"committer": {"date": "2025-02-08T12:00:00Z"}}},  # 2 days before bump_sha_1
        {"commit": {"committer": {"date": "2025-02-02T12:00:00Z"}}},  # 3 days before bump_sha_2
        {"commit": {"committer": {"date": "2025-01-26T12:00:00Z"}}},  # 4 days before bump_sha_3
    ]
