from __future__ import annotations

from datetime import datetime
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape


ROOT_DIR = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT_DIR / "content"
PAPER_DIR = CONTENT_DIR / "papers"
TEMPLATE_DIR = ROOT_DIR / "src" / "templates"
OUTPUT_FILE = ROOT_DIR / "index.html"


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    return data or {}


def load_papers() -> list[dict]:
    papers: list[dict] = []
    if not PAPER_DIR.exists():
        return papers

    for path in sorted(PAPER_DIR.glob("*.y*ml")):
        paper = load_yaml(path)
        if paper:
            papers.append(paper)

    return sorted(
        papers,
        key=lambda paper: (paper.get("year", 0), paper.get("title", "")),
        reverse=True,
    )


def generate_site() -> None:
    config = load_yaml(CONTENT_DIR / "site.yaml")
    papers = load_papers()

    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(enabled_extensions=("html", "xml")),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("index.html")

    html = template.render(
        config=config,
        preprints=[paper for paper in papers if paper.get("type") == "preprint"],
        publications=[paper for paper in papers if paper.get("type") == "publication"],
        last_updated=datetime.now().strftime("%b. %d, %Y"),
    )

    OUTPUT_FILE.write_text(html, encoding="utf-8")
    print(f"Website generated successfully at {OUTPUT_FILE.relative_to(ROOT_DIR)}")


if __name__ == "__main__":
    generate_site()
