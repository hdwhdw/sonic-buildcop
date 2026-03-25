"""Tests for the HTML dashboard renderer."""

import json
import os

from sonic_submodule_status.renderer import render_dashboard, sort_submodules, compute_summary
from datetime import datetime, timezone
from sonic_submodule_status.renderer import format_relative_time


def _make_data(submodules=None, generated_at="2026-03-20T06:00:00Z"):
    """Helper: create a data dict matching the data.json schema."""
    if submodules is None:
        submodules = [
            {
                "name": "sonic-swss",
                "path": "src/sonic-swss",
                "url": "https://github.com/sonic-net/sonic-swss",
                "owner": "sonic-net",
                "repo": "sonic-swss",
                "pinned_sha": "c20ded7bcef07eb68995aa2347f39c4bc22c9191",
                "branch": "master",
                "commits_behind": 5,
                "days_behind": 12,
                "compare_url": "https://github.com/sonic-net/sonic-swss/compare/c20ded7...master",
                "status": "ok",
                "error": None,
                "staleness_status": "green",
                "median_days": 1.5,
                "commit_count_6m": 20,
                "thresholds": {"yellow_days": 3.0, "red_days": 6.0, "is_fallback": False},
                "open_bot_pr": None,
                "last_merged_bot_pr": None,
                "latest_repo_commit": None,
                "avg_delay_days": None,
            },
            {
                "name": "sonic-dash-ha",
                "path": "src/sonic-dash-ha",
                "url": "https://github.com/sonic-net/sonic-dash-ha",
                "owner": "sonic-net",
                "repo": "sonic-dash-ha",
                "pinned_sha": None,
                "branch": None,
                "commits_behind": None,
                "days_behind": None,
                "compare_url": None,
                "status": "unavailable",
                "error": "API returned 403 after 3 retries",
                "staleness_status": None,
                "median_days": None,
                "commit_count_6m": None,
                "thresholds": None,
                "open_bot_pr": None,
                "last_merged_bot_pr": None,
                "latest_repo_commit": None,
                "avg_delay_days": None,
            },
        ]
    return {"generated_at": generated_at, "submodules": submodules}


def _write_data(tmp_path, data=None):
    """Helper: write data.json to tmp_path, return path."""
    if data is None:
        data = _make_data()
    data_path = tmp_path / "data.json"
    data_path.write_text(json.dumps(data))
    return str(data_path)


def _render(tmp_path, data=None):
    """Helper: write data and render, return HTML string."""
    data_path = _write_data(tmp_path, data)
    site_dir = str(tmp_path / "site")
    render_dashboard(data_path, site_dir)
    return (tmp_path / "site" / "index.html").read_text()


def test_render_produces_html_file(tmp_path):
    """render_dashboard creates site/index.html."""
    data_path = _write_data(tmp_path)
    site_dir = str(tmp_path / "site")
    render_dashboard(data_path, site_dir)
    assert (tmp_path / "site" / "index.html").exists()


def test_render_creates_nojekyll(tmp_path):
    """render_dashboard creates site/.nojekyll."""
    data_path = _write_data(tmp_path)
    site_dir = str(tmp_path / "site")
    render_dashboard(data_path, site_dir)
    assert (tmp_path / "site" / ".nojekyll").exists()


def test_html_contains_table_headers(tmp_path):
    """HTML output contains all 8 table column headers."""
    html = _render(tmp_path)
    assert "<th>Submodule</th>" in html
    assert "<th>Status</th>" in html
    assert "<th>Pinned SHA</th>" in html
    assert "<th>Commits Behind</th>" in html
    assert "<th>Days Behind</th>" in html
    assert "<th>Median Cadence</th>" in html
    assert "<th>Thresholds</th>" in html
    assert "<th>Compare</th>" in html


def test_html_contains_submodule_name(tmp_path):
    """HTML output contains the submodule name."""
    html = _render(tmp_path)
    assert "sonic-swss" in html


def test_html_contains_pinned_sha_short(tmp_path):
    """HTML output shows first 7 chars of pinned SHA."""
    data = _make_data(submodules=[
        {
            "name": "test-sub",
            "path": "src/test-sub",
            "url": "https://github.com/test/test-sub",
            "owner": "test",
            "repo": "test-sub",
            "pinned_sha": "abc123def4567890",
            "branch": "master",
            "commits_behind": 0,
            "days_behind": 0,
            "compare_url": "https://github.com/test/test-sub/compare/abc123d...master",
            "status": "ok",
            "error": None,
            "staleness_status": "green",
            "median_days": 1.5,
            "commit_count_6m": 20,
            "thresholds": {"yellow_days": 3.0, "red_days": 6.0, "is_fallback": False},
            "open_bot_pr": None,
            "last_merged_bot_pr": None,
            "latest_repo_commit": None,
            "avg_delay_days": None,
        }
    ])
    html = _render(tmp_path, data)
    assert "abc123d" in html


def test_html_contains_compare_link(tmp_path):
    """HTML output contains clickable compare link."""
    html = _render(tmp_path)
    assert 'href="https://github.com/sonic-net/sonic-swss/compare/c20ded7...master"' in html


def test_html_shows_unavailable_submodule(tmp_path):
    """HTML output shows 'unavailable' for submodules with errors."""
    html = _render(tmp_path)
    assert "unavailable" in html


def test_html_contains_generated_at(tmp_path):
    """HTML output contains the generated_at timestamp in a <time> element."""
    html = _render(tmp_path)
    assert "<time" in html
    assert 'datetime="2026-03-20T06:00:00Z"' in html


def test_render_creates_site_directory(tmp_path):
    """render_dashboard creates the site directory if it doesn't exist."""
    data_path = _write_data(tmp_path)
    site_dir = str(tmp_path / "nonexistent" / "site")
    render_dashboard(data_path, site_dir)
    assert os.path.isdir(site_dir)
    assert os.path.isfile(os.path.join(site_dir, "index.html"))


# --- Helpers for sort/summary tests ---


def _make_sub(name, staleness_status, days_behind, status="ok", median_days=None, thresholds=None,
              open_bot_pr=None, last_merged_bot_pr=None, latest_repo_commit=None, avg_delay_days=None):
    """Minimal submodule dict for sort/summary testing."""
    return {
        "name": name,
        "path": f"src/{name}",
        "url": f"https://github.com/sonic-net/{name}",
        "owner": "sonic-net",
        "repo": name,
        "pinned_sha": "abc123def4567890" if status == "ok" else None,
        "branch": "master" if status == "ok" else None,
        "commits_behind": 5 if status == "ok" else None,
        "days_behind": days_behind,
        "compare_url": f"https://github.com/sonic-net/{name}/compare/abc123...master" if status == "ok" else None,
        "status": status,
        "error": None if status == "ok" else "API error",
        "staleness_status": staleness_status,
        "median_days": median_days,
        "commit_count_6m": None,
        "thresholds": thresholds,
        "open_bot_pr": open_bot_pr,
        "last_merged_bot_pr": last_merged_bot_pr,
        "latest_repo_commit": latest_repo_commit,
        "avg_delay_days": avg_delay_days,
    }


# --- sort_submodules tests ---


def test_sort_red_before_yellow_before_green():
    """sort_submodules orders red → yellow → green."""
    subs = [
        _make_sub("g", "green", 5),
        _make_sub("r", "red", 50),
        _make_sub("y", "yellow", 20),
    ]
    result = sort_submodules(subs)
    assert [s["name"] for s in result] == ["r", "y", "g"]


def test_sort_days_behind_descending_within_tier():
    """Within the same tier, more days-behind appears first."""
    subs = [
        _make_sub("b", "yellow", 10),
        _make_sub("a", "yellow", 30),
    ]
    result = sort_submodules(subs)
    assert [s["name"] for s in result] == ["a", "b"]


def test_sort_unavailable_last():
    """Submodules with staleness_status=None sort after green."""
    subs = [
        _make_sub("unavail", None, None, status="unavailable"),
        _make_sub("ok-green", "green", 1),
    ]
    result = sort_submodules(subs)
    assert [s["name"] for s in result] == ["ok-green", "unavail"]


def test_sort_empty_list():
    """Empty input returns empty list."""
    assert sort_submodules([]) == []


def test_sort_does_not_mutate_input():
    """sort_submodules returns a new list; original is unchanged."""
    subs = [
        _make_sub("g", "green", 5),
        _make_sub("r", "red", 50),
    ]
    original = list(subs)
    sort_submodules(subs)
    assert subs == original


# --- compute_summary tests ---


def test_summary_format_mixed():
    """Mixed statuses produce correct emoji-count string."""
    subs = [
        _make_sub("a", "green", 1),
        _make_sub("b", "green", 2),
        _make_sub("c", "yellow", 15),
        _make_sub("d", "red", 60),
    ]
    assert compute_summary(subs) == "🟢 2 · 🟡 1 · 🔴 1"


def test_summary_excludes_unavailable():
    """Unavailable submodules (staleness_status=None) are not counted."""
    subs = [
        _make_sub("ok", "green", 1),
        _make_sub("bad", None, None, status="unavailable"),
    ]
    assert compute_summary(subs) == "🟢 1 · 🟡 0 · 🔴 0"


def test_summary_all_green():
    """All-green input returns correct counts."""
    subs = [
        _make_sub("a", "green", 1),
        _make_sub("b", "green", 2),
        _make_sub("c", "green", 3),
    ]
    assert compute_summary(subs) == "🟢 3 · 🟡 0 · 🔴 0"


# --- Integration test: sort order in rendered HTML ---


def test_render_html_contains_summary_text(tmp_path):
    """Rendered HTML displays the aggregate summary with emoji counts."""
    subs = [
        _make_sub("a", "green", 3),
        _make_sub("b", "yellow", 20),
        _make_sub("c", "red", 60),
    ]
    data = _make_data(submodules=subs)
    html = _render(tmp_path, data)
    assert "\U0001f7e2 1" in html   # 🟢 1
    assert "\U0001f7e1 1" in html   # 🟡 1
    assert "\U0001f534 1" in html   # 🔴 1


def test_render_html_has_responsive_wrapper(tmp_path):
    """Rendered HTML wraps table in overflow-x: auto container."""
    html = _render(tmp_path)
    assert "table-wrapper" in html
    assert "overflow-x" in html


def test_render_html_has_container(tmp_path):
    """Rendered HTML has max-width container for readability."""
    html = _render(tmp_path)
    assert "container" in html
    assert "max-width" in html


def test_render_html_has_timestamp_class(tmp_path):
    """Rendered HTML styles the timestamp with .timestamp class."""
    html = _render(tmp_path)
    assert 'class="timestamp"' in html
    assert "2026-03-20T06:00:00Z" in html


def test_render_html_preserves_all_columns(tmp_path):
    """All 8 table columns are present."""
    html = _render(tmp_path)
    for col in ["Submodule", "Status", "Pinned SHA", "Commits Behind", "Days Behind", "Median Cadence", "Thresholds", "Compare"]:
        assert f"<th>{col}</th>" in html


def test_render_html_sorted_worst_first(tmp_path):
    """Rendered HTML table has submodules sorted: red → yellow → green → unavailable."""
    subs = [
        _make_sub("sub-green", "green", 3),
        _make_sub("sub-red", "red", 60),
        _make_sub("sub-yellow", "yellow", 20),
        {
            "name": "sub-unavail",
            "path": "src/sub-unavail",
            "url": "https://github.com/sonic-net/sub-unavail",
            "owner": "sonic-net",
            "repo": "sub-unavail",
            "pinned_sha": None,
            "branch": None,
            "commits_behind": None,
            "days_behind": None,
            "compare_url": None,
            "status": "unavailable",
            "error": "API error",
            "staleness_status": None,
            "median_days": None,
            "commit_count_6m": None,
            "thresholds": None,
            "open_bot_pr": None,
            "last_merged_bot_pr": None,
            "latest_repo_commit": None,
            "avg_delay_days": None,
        },
    ]
    data = _make_data(submodules=subs)
    html = _render(tmp_path, data)
    red_pos = html.index("sub-red")
    yellow_pos = html.index("sub-yellow")
    green_pos = html.index("sub-green")
    unavail_pos = html.index("sub-unavail")
    assert red_pos < yellow_pos < green_pos < unavail_pos


# --- format_relative_time tests ---


def test_format_relative_time_just_now():
    """Timestamps less than 60 seconds ago return 'just now'."""
    now = datetime(2026, 3, 20, 12, 0, 0, tzinfo=timezone.utc)
    assert format_relative_time("2026-03-20T11:59:30Z", now=now) == "just now"


def test_format_relative_time_minutes():
    """Timestamps a few minutes ago return 'N minutes ago'."""
    now = datetime(2026, 3, 20, 12, 0, 0, tzinfo=timezone.utc)
    assert format_relative_time("2026-03-20T11:55:00Z", now=now) == "5 minutes ago"


def test_format_relative_time_singular_minute():
    """Exactly 1 minute ago returns '1 minute ago' (singular)."""
    now = datetime(2026, 3, 20, 12, 0, 0, tzinfo=timezone.utc)
    assert format_relative_time("2026-03-20T11:59:00Z", now=now) == "1 minute ago"


def test_format_relative_time_hours():
    """Timestamps a few hours ago return 'N hours ago'."""
    now = datetime(2026, 3, 20, 12, 0, 0, tzinfo=timezone.utc)
    assert format_relative_time("2026-03-20T09:00:00Z", now=now) == "3 hours ago"


def test_format_relative_time_singular_hour():
    """Exactly 1 hour ago returns '1 hour ago' (singular)."""
    now = datetime(2026, 3, 20, 12, 0, 0, tzinfo=timezone.utc)
    assert format_relative_time("2026-03-20T11:00:00Z", now=now) == "1 hour ago"


def test_format_relative_time_days():
    """Timestamps days ago return 'N days ago'."""
    now = datetime(2026, 3, 20, 12, 0, 0, tzinfo=timezone.utc)
    assert format_relative_time("2026-03-17T12:00:00Z", now=now) == "3 days ago"


def test_format_relative_time_singular_day():
    """Exactly 1 day ago returns '1 day ago' (singular)."""
    now = datetime(2026, 3, 20, 12, 0, 0, tzinfo=timezone.utc)
    assert format_relative_time("2026-03-19T12:00:00Z", now=now) == "1 day ago"


def test_format_relative_time_z_suffix():
    """Timestamps with 'Z' suffix are handled correctly."""
    now = datetime(2026, 3, 20, 12, 0, 0, tzinfo=timezone.utc)
    result = format_relative_time("2026-03-20T10:00:00Z", now=now)
    assert result == "2 hours ago"


# --- New column rendering tests ---


def test_render_html_shows_median_cadence(tmp_path):
    """HTML shows formatted median cadence for submodules with data."""
    subs = [
        _make_sub("cadence-test", "green", 3,
                   median_days=2.5,
                   thresholds={"yellow_days": 5.0, "red_days": 10.0, "is_fallback": False}),
    ]
    data = _make_data(submodules=subs)
    html = _render(tmp_path, data)
    assert "~2.5 days" in html


def test_render_html_shows_thresholds(tmp_path):
    """HTML shows formatted threshold values for submodules with data."""
    subs = [
        _make_sub("threshold-test", "green", 3,
                   median_days=2.5,
                   thresholds={"yellow_days": 5.0, "red_days": 10.0, "is_fallback": False}),
    ]
    data = _make_data(submodules=subs)
    html = _render(tmp_path, data)
    assert "5d / 10d" in html


def test_render_html_unavailable_shows_dashes_in_cadence_columns(tmp_path):
    """Unavailable submodules show dashes in median cadence and thresholds columns."""
    subs = [
        _make_sub("unavail", None, None, status="unavailable"),
    ]
    data = _make_data(submodules=subs)
    html = _render(tmp_path, data)
    # The HTML should contain dash characters for both new columns
    # Count occurrences of "—" — should have at least 3 (days_behind + median_cadence + thresholds)
    assert html.count("—") >= 3


# --- Linkification and structural tests ---


def test_html_name_links_to_repo(tmp_path):
    """Submodule name is a link to its GitHub repo (LINK-01)."""
    html = _render(tmp_path)
    assert 'href="https://github.com/sonic-net/sonic-swss"' in html
    assert ">sonic-swss</a>" in html


def test_html_sha_links_to_commit(tmp_path):
    """Pinned SHA links to the exact commit on GitHub (LINK-02)."""
    html = _render(tmp_path)
    # sonic-swss has pinned_sha starting with c20ded7
    assert 'href="https://github.com/sonic-net/sonic-swss/commit/c20ded7bcef07eb68995aa2347f39c4bc22c9191"' in html
    assert "<code>c20ded7</code>" in html


def test_html_has_header_with_description(tmp_path):
    """Page has header with project description (VIS-04)."""
    html = _render(tmp_path)
    assert "<header>" in html
    assert "sonic-net/sonic-buildimage" in html
    assert 'class="description"' in html


def test_html_has_footer_source_link(tmp_path):
    """Page has footer linking to sonic-buildcop source repo (LINK-04)."""
    html = _render(tmp_path)
    assert "<footer>" in html
    assert 'href="https://github.com/hdwhdw/sonic-buildcop"' in html


def test_html_path_column_removed(tmp_path):
    """Path column is removed from the table (LINK-03)."""
    html = _render(tmp_path)
    assert "<th>Path</th>" not in html


def test_html_unavailable_sha_not_linked(tmp_path):
    """Unavailable submodules show 'unavailable' without a commit link."""
    html = _render(tmp_path)
    # sonic-dash-ha is unavailable — should show "unavailable" text, not a link
    assert "<em>unavailable</em>" in html


# --- Dark mode and badge refinement tests ---


def test_html_has_dark_mode_media_query(tmp_path):
    """Dashboard CSS includes dark mode support via prefers-color-scheme (VIS-02)."""
    html = _render(tmp_path)
    assert "prefers-color-scheme: dark" in html


def test_html_dark_mode_defines_body_colors(tmp_path):
    """Dark mode block defines dark background and light text."""
    html = _render(tmp_path)
    # Dark mode section should define body background and text
    dark_section_start = html.index("prefers-color-scheme: dark")
    dark_section = html[dark_section_start:]
    assert "#0d1117" in dark_section  # dark background
    assert "#c9d1d9" in dark_section  # light text


def test_html_badge_has_dot_indicator(tmp_path):
    """Status badges show dot indicator with status text (VIS-03)."""
    html = _render(tmp_path)
    # sonic-swss has staleness_status="green"
    assert "● Green" in html


def test_html_badge_pill_shape(tmp_path):
    """Badge CSS uses pill shape with rounded corners (VIS-01)."""
    html = _render(tmp_path)
    assert "border-radius: 12px" in html


def test_html_dark_mode_badge_colors(tmp_path):
    """Dark mode defines adjusted badge colors for readability."""
    html = _render(tmp_path)
    dark_start = html.index("prefers-color-scheme: dark")
    dark_section = html[dark_start:]
    assert "#238636" in dark_section  # dark green badge
    assert "#da3633" in dark_section  # dark red badge


def test_html_table_has_border(tmp_path):
    """Table has a border for a contained professional look (VIS-01)."""
    html = _render(tmp_path)
    assert "border-radius: 6px" in html


# --- Expandable detail row tests ---


def test_html_has_toggle_icon(tmp_path):
    """Each row has a toggle icon for expanding details (EXPAND-01)."""
    html = _render(tmp_path)
    assert 'class="toggle-icon"' in html
    assert 'toggleDetail' in html


def test_html_has_detail_rows(tmp_path):
    """Hidden detail rows exist for each submodule (EXPAND-01)."""
    html = _render(tmp_path)
    assert 'class="detail-row"' in html
    assert 'display:none' in html


def test_html_has_expand_all_button(tmp_path):
    """Expand All button exists in header area (EXPAND-01)."""
    html = _render(tmp_path)
    assert 'class="expand-all-btn"' in html
    assert 'toggleAll()' in html
    assert 'Expand All' in html


def test_html_has_toggle_js_functions(tmp_path):
    """Toggle JavaScript functions exist in the page."""
    html = _render(tmp_path)
    assert 'function toggleDetail' in html
    assert 'function toggleAll' in html


def test_html_detail_shows_open_bot_pr(tmp_path):
    """Detail panel shows open bot PR link and age when data exists (EXPAND-02)."""
    subs = [_make_sub("test-sub", "green", 3, open_bot_pr={
        "url": "https://github.com/sonic-net/sonic-buildimage/pull/101",
        "age_days": 5.2,
        "ci_status": "pass",
    })]
    html = _render(tmp_path, _make_data(submodules=subs))
    assert 'href="https://github.com/sonic-net/sonic-buildimage/pull/101"' in html
    assert '5.2' in html
    assert 'ci-pass' in html


def test_html_detail_null_open_pr(tmp_path):
    """Detail panel shows placeholder when no open PR (EXPAND-02)."""
    html = _render(tmp_path)
    assert 'No open PR' in html


def test_html_detail_ci_status_fail(tmp_path):
    """CI status fail is rendered with fail indicator (EXPAND-02)."""
    subs = [_make_sub("test-sub", "green", 3, open_bot_pr={
        "url": "https://example.com/pr/1",
        "age_days": 2.0,
        "ci_status": "fail",
    })]
    html = _render(tmp_path, _make_data(submodules=subs))
    assert 'ci-fail' in html


def test_html_detail_ci_status_pending(tmp_path):
    """CI status pending is rendered with pending indicator (EXPAND-02)."""
    subs = [_make_sub("test-sub", "green", 3, open_bot_pr={
        "url": "https://example.com/pr/1",
        "age_days": 1.0,
        "ci_status": "pending",
    })]
    html = _render(tmp_path, _make_data(submodules=subs))
    assert 'ci-pending' in html


def test_html_detail_shows_last_merged_pr(tmp_path):
    """Detail panel shows last merged PR link with date (EXPAND-03)."""
    subs = [_make_sub("test-sub", "green", 3, last_merged_bot_pr={
        "url": "https://github.com/sonic-net/sonic-buildimage/pull/99",
        "merged_at": "2025-01-12T15:30:00Z",
    })]
    html = _render(tmp_path, _make_data(submodules=subs))
    assert 'href="https://github.com/sonic-net/sonic-buildimage/pull/99"' in html
    assert '2025-01-12' in html


def test_html_detail_shows_latest_commit(tmp_path):
    """Detail panel shows latest repo commit link with date (EXPAND-04)."""
    subs = [_make_sub("test-sub", "green", 3, latest_repo_commit={
        "url": "https://github.com/sonic-net/sonic-swss/commit/abc123",
        "date": "2025-02-19T08:00:00Z",
    })]
    html = _render(tmp_path, _make_data(submodules=subs))
    assert 'href="https://github.com/sonic-net/sonic-swss/commit/abc123"' in html
    assert '2025-02-19' in html


def test_html_detail_shows_avg_delay(tmp_path):
    """Detail panel shows average delay metric (EXPAND-05)."""
    subs = [_make_sub("test-sub", "green", 3, avg_delay_days=4.2)]
    html = _render(tmp_path, _make_data(submodules=subs))
    assert '4.2' in html


def test_html_detail_null_avg_delay(tmp_path):
    """Detail panel shows placeholder when avg delay is null (EXPAND-05)."""
    html = _render(tmp_path)
    assert 'Not enough data' in html


def test_html_detail_colspan_matches_columns(tmp_path):
    """Detail row colspan matches total column count (9 with toggle)."""
    html = _render(tmp_path)
    assert 'colspan="9"' in html


def test_html_detail_dark_mode_styles(tmp_path):
    """Dark mode CSS includes detail panel and CI status styles."""
    html = _render(tmp_path)
    dark_start = html.index("prefers-color-scheme: dark")
    dark_section = html[dark_start:]
    assert '.detail-panel' in dark_section
    assert '.ci-pass' in dark_section
    assert '.ci-fail' in dark_section
