"""Render data.json into a static HTML dashboard using Jinja2."""

import json
import os

from jinja2 import Environment, FileSystemLoader


_TIER_ORDER = {"red": 0, "yellow": 1, "green": 2}


def sort_submodules(submodules: list[dict]) -> list[dict]:
    """Sort submodules by staleness severity: red → yellow → green → unknown.

    Within the same tier, sort by days_behind descending (most stale first).
    Unavailable/unknown submodules (staleness_status=None) sort last.
    Returns a new sorted list; does not mutate the input.
    """
    def _sort_key(sub):
        tier = _TIER_ORDER.get(sub.get("staleness_status"), 3)
        days = -(sub.get("days_behind") or 0)
        return (tier, days)

    return sorted(submodules, key=_sort_key)


def compute_summary(submodules: list[dict]) -> str:
    """Compute aggregate summary string with colored emoji counts.

    Returns format: "🟢 N · 🟡 N · 🔴 N"
    Submodules with staleness_status=None are excluded from counts.
    """
    counts = {"green": 0, "yellow": 0, "red": 0}
    for sub in submodules:
        status = sub.get("staleness_status")
        if status in counts:
            counts[status] += 1
    return f"\U0001f7e2 {counts['green']} \u00b7 \U0001f7e1 {counts['yellow']} \u00b7 \U0001f534 {counts['red']}"


def render_dashboard(data_path: str, site_dir: str) -> None:
    """Read data.json, render HTML template, write to site_dir/index.html."""
    # Load data
    with open(data_path, "r") as f:
        data = json.load(f)

    # Setup Jinja2 — templates/ is sibling of scripts/
    template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
    env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
    template = env.get_template("dashboard.html")

    # Sort and summarize
    sorted_subs = sort_submodules(data["submodules"])
    summary_text = compute_summary(data["submodules"])

    # Render
    html = template.render(
        generated_at=data["generated_at"],
        submodules=sorted_subs,
        summary_text=summary_text,
    )

    # Write output
    os.makedirs(site_dir, exist_ok=True)
    with open(os.path.join(site_dir, "index.html"), "w") as f:
        f.write(html)

    # Create .nojekyll to prevent GitHub Pages Jekyll processing
    with open(os.path.join(site_dir, ".nojekyll"), "w") as f:
        pass

    print(f"Dashboard rendered: {os.path.join(site_dir, 'index.html')}")
    print(f"Submodules: {len(data['submodules'])}")


def main():
    """Entry point when run as script."""
    data_path = os.environ.get("DATA_PATH", "data.json")
    site_dir = os.environ.get("SITE_DIR", "site")
    render_dashboard(data_path, site_dir)


if __name__ == "__main__":
    main()
