"""Tests for the HTML dashboard renderer."""

import json
import os
import sys

# Allow importing from scripts/ directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from renderer import render_dashboard


def _make_data(submodules=None, generated_at="2026-03-20T06:00:00Z"):
    """Helper: create a data dict matching the data.json schema."""
    if submodules is None:
        submodules = [
            {
                "name": "sonic-swss",
                "path": "src/sonic-swss",
                "url": "https://github.com/sonic-net/sonic-swss",
                "pinned_sha": "c20ded7bcef07eb68995aa2347f39c4bc22c9191",
                "branch": "master",
                "commits_behind": 5,
                "days_behind": 12,
                "compare_url": "https://github.com/sonic-net/sonic-swss/compare/c20ded7...master",
                "status": "ok",
                "error": None,
            },
            {
                "name": "sonic-dash-ha",
                "path": "src/sonic-dash-ha",
                "url": "https://github.com/sonic-net/sonic-dash-ha",
                "pinned_sha": None,
                "branch": None,
                "commits_behind": None,
                "days_behind": None,
                "compare_url": None,
                "status": "unavailable",
                "error": "API returned 403 after 3 retries",
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
    """HTML output contains all 6 table column headers."""
    html = _render(tmp_path)
    assert "<th>Submodule</th>" in html
    assert "<th>Path</th>" in html
    assert "<th>Pinned SHA</th>" in html
    assert "<th>Commits Behind</th>" in html
    assert "<th>Days Behind</th>" in html
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
            "pinned_sha": "abc123def4567890",
            "branch": "master",
            "commits_behind": 0,
            "days_behind": 0,
            "compare_url": "https://github.com/test/test-sub/compare/abc123d...master",
            "status": "ok",
            "error": None,
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
    """HTML output contains the generated_at timestamp."""
    html = _render(tmp_path)
    assert "2026-03-20T06:00:00Z" in html


def test_render_creates_site_directory(tmp_path):
    """render_dashboard creates the site directory if it doesn't exist."""
    data_path = _write_data(tmp_path)
    site_dir = str(tmp_path / "nonexistent" / "site")
    render_dashboard(data_path, site_dir)
    assert os.path.isdir(site_dir)
    assert os.path.isfile(os.path.join(site_dir, "index.html"))
