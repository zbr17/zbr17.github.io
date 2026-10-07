"""Build the homepage and academic CV from one content source.

Default: refresh the root index.html and English CV for local/legacy hosting.
--output-dir dist: create a clean, minimal GitHub Pages deployment bundle.
"""
from __future__ import annotations

import argparse
import os
import shutil
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import unquote, urlsplit

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from build_cv import generate_cv

ROOT_DIR = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT_DIR / "content"
PAPER_DIR = CONTENT_DIR / "papers"
TEMPLATE_DIR = ROOT_DIR / "src" / "templates"
JOURNALS = {"TPAMI", "CJE", "TGRS", "TIP", "T-IP", "JMLR"}
# One ordered list drives both the rendered sections and the static navigation.
SECTIONS = [
    {"id": "about", "title": "About", "nav": "About"},
    {"id": "research", "title": "Research", "nav": "Research"},
    {"id": "news", "title": "News", "nav": "News"},
    {"id": "publications", "title": "Selected Publications", "nav": "Publications",
     "note": "* indicates equal contribution"},
    {"id": "preprints", "title": "Preprints", "nav": "Preprints"},
    {"id": "experience", "title": "Education & Appointments", "nav": "Experience"},
    {"id": "loopeva", "title": "Building at LoopEva", "nav": "LoopEva"},
    {"id": "honors", "title": "Honors & Awards", "nav": "Honors"},
    {"id": "services", "title": "Academic Services", "nav": "Services"},
]


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    if not isinstance(data, dict):
        raise ValueError(f"{path.relative_to(ROOT_DIR)} must contain a YAML mapping.")
    return data


def load_papers() -> list[dict]:
    papers = []
    titles = set()
    for path in sorted(PAPER_DIR.glob("*.y*ml")):
        paper = load_yaml(path)
        for key in ("title", "authors", "venue", "year", "type"):
            if not paper.get(key):
                raise ValueError(f"{path.name}: missing {key}.")
        if type(paper["year"]) is not int:
            raise ValueError(f"{path.name}: year must be an integer.")
        if paper["type"] not in ("publication", "preprint"):
            raise ValueError(f"{path.name}: type must be publication or preprint.")
        if not isinstance(paper["authors"], list) or not all(
            isinstance(author, dict) and author.get("name") for author in paper["authors"]
        ):
            raise ValueError(f"{path.name}: authors must be a non-empty list of names.")
        if paper["title"] in titles:
            raise ValueError(f"{path.name}: duplicate paper title.")
        titles.add(paper["title"])
        paper.setdefault("selected", True)
        if type(paper["selected"]) is not bool:
            raise ValueError(f"{path.name}: selected must be true or false.")
        paper.setdefault("kind", "journal" if paper["venue"] in JOURNALS else "conference")
        if paper["kind"] not in ("journal", "conference"):
            raise ValueError(f"{path.name}: kind must be journal or conference.")
        for link in paper.get("links", []):
            if not link.get("name") or urlsplit(link.get("url", "")).scheme not in ("http", "https"):
                raise ValueError(f"{path.name}: paper links require a name and an HTTP(S) URL.")
        if paper["selected"]:
            for key in ("image", "abstract", "links"):
                if not paper.get(key):
                    raise ValueError(f"{path.name}: selected papers require {key}.")
        papers.append(paper)
    return sorted(papers, key=lambda paper: (paper["year"], paper["title"]), reverse=True)


def profile_links(config: dict) -> list[dict]:
    links = []
    for entry in config["profile_links"]:
        link = dict(entry)
        link["url"] = entry.get("prefix", "") + config["basic_info"][entry["field"]]
        links.append(link)
    return links


class PageReferences(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.references = []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if "id" in attrs:
            if attrs["id"] in self.ids:
                raise ValueError(f"Duplicate HTML id: {attrs['id']}")
            self.ids.add(attrs["id"])
        for attr in ("src", "href"):
            if attrs.get(attr):
                self.references.append(attrs[attr])


def deployment_assets(html: str, cv_path: str) -> set[Path]:
    """Allow only checked local assets, never entire source folders."""
    parser = PageReferences()
    parser.feed(html)
    assets = set()
    for reference in parser.references:
        url = urlsplit(reference)
        if url.scheme or url.netloc:
            if url.scheme not in ("http", "https", "mailto"):
                raise ValueError(f"Unsupported link scheme: {reference}")
            continue
        if not url.path:
            if url.fragment and unquote(url.fragment) not in parser.ids:
                raise ValueError(f"Broken section link: {reference}")
            continue
        local_path = Path(unquote(url.path))
        resolved = (ROOT_DIR / local_path).resolve()
        if not resolved.is_relative_to(ROOT_DIR / "assets"):
            raise ValueError(f"Only assets/ files may be published: {reference}")
        if local_path.as_posix() != cv_path and not resolved.is_file():
            raise ValueError(f"Missing asset: {reference}")
        assets.add(local_path)
    return assets


def build_time() -> datetime:
    zone = timezone(timedelta(hours=8))
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    return datetime.fromtimestamp(int(epoch), zone) if epoch else datetime.now(zone)


def generate_site(output_dir: Path | None = None) -> dict:
    requested = output_dir or ROOT_DIR
    if requested.is_symlink():
        raise ValueError("The output directory cannot be a symbolic link.")
    output = requested.resolve()
    if not output.is_relative_to(ROOT_DIR):
        raise ValueError("The output directory must be inside this project.")
    protected = ("assets", "content", "src", "scripts", "tests", ".git", ".github")
    if any(output.is_relative_to(ROOT_DIR / name) for name in protected):
        raise ValueError("The output directory cannot overwrite source directories.")
    if output != ROOT_DIR and (ROOT_DIR / "tmp").is_relative_to(output):
        raise ValueError("The output directory cannot replace the build scratch directory.")
    if output != ROOT_DIR and output.exists() and any(output.iterdir()) and not (output / ".nojekyll").is_file():
        raise ValueError("Use an empty output directory; existing non-build files will not be deleted.")

    config = load_yaml(CONTENT_DIR / "site.yaml")
    papers = load_papers()
    selected = [paper for paper in papers if paper["selected"]]
    links = profile_links(config)
    cv_path = config["basic_info"]["cv_link"]
    cv_relative = Path(cv_path)
    if cv_relative.suffix.lower() != ".pdf" or not (ROOT_DIR / cv_relative).resolve().is_relative_to(ROOT_DIR / "assets" / "resume"):
        raise ValueError("cv_link must point to a PDF inside assets/resume/.")
    updated = build_time()
    description = (
        f"{config['basic_info']['name']} - postdoctoral researcher at Tsinghua University "
        "and co-founder & CEO of LoopEva. Embodied intelligence, efficient multimodal "
        "models, and explainable learning."
    )
    sections = [dict(section, note=section.get("note", "")) for section in SECTIONS
                if section["id"] not in ("publications", "preprints")
                or any(paper["type"] == ("publication" if section["id"] == "publications" else "preprint") for paper in selected)]
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(("html", "xml")),
        undefined=StrictUndefined,
        trim_blocks=True, lstrip_blocks=True,
    )
    html = env.get_template("index.html").render(
        config=config, sections=sections, profile_links=links,
        publications=[p for p in selected if p["type"] == "publication"],
        preprints=[p for p in selected if p["type"] == "preprint"],
        description=description, current_year=updated.year,
        last_updated=updated.strftime("%d %b %Y"),
    )
    assets = deployment_assets(html, cv_path)
    # Complete and validate the bundle before replacing any previous output.
    scratch = ROOT_DIR / "tmp"
    scratch.mkdir(exist_ok=True)
    with TemporaryDirectory(prefix="site-build-", dir=scratch) as directory:
        stage = Path(directory)
        (stage / "index.html").write_text(html, encoding="utf-8")
        (stage / ".nojekyll").touch()
        for asset in assets - {cv_relative}:
            destination = stage / asset
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT_DIR / asset, destination)
        cv_output = stage / cv_relative
        cv_output.parent.mkdir(parents=True, exist_ok=True)
        generate_cv(config, papers, links, cv_output, updated)
        if output != ROOT_DIR and output.exists():
            # Both the resolved workspace boundary and build ownership were checked above.
            shutil.rmtree(output)
        output.mkdir(parents=True, exist_ok=True)
        for source in stage.rglob("*"):
            if source.is_file():
                destination = output / source.relative_to(stage)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
    return {"selected": len(selected), "papers": len(papers), "assets": len(assets), "output": output}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT_DIR,
                        help="Output directory inside the project (e.g. dist).")
    arguments = parser.parse_args()
    try:
        result = generate_site(arguments.output_dir)
    except (ValueError, KeyError) as error:
        parser.exit(1, f"Build failed: {error}\n")
    print(f"Built {result['selected']} selected papers, {result['papers']} CV entries: {result['output']}")
