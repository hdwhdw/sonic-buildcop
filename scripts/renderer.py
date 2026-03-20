"""Render data.json into a static HTML dashboard using Jinja2."""

import json
import os

from jinja2 import Environment, FileSystemLoader


def render_dashboard(data_path: str, site_dir: str) -> None:
    """Read data.json, render HTML template, write to site_dir/index.html."""
    # Load data
    with open(data_path, "r") as f:
        data = json.load(f)

    # Setup Jinja2 — templates/ is sibling of scripts/
    template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
    env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
    template = env.get_template("dashboard.html")

    # Render
    html = template.render(
        generated_at=data["generated_at"],
        submodules=data["submodules"],
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
