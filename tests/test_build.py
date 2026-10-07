"""Integration checks for content consistency and safe static publishing."""
from __future__ import annotations

from html import unescape
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import yaml
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build


def normalized(text):
    return " ".join(unescape(text).split())


class BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT / "tmp").mkdir(exist_ok=True)
        cls.temporary = TemporaryDirectory(dir=ROOT / "tmp")
        cls.directory = Path(cls.temporary.name)
        cls.output = cls.directory / "public"
        cls.result = build.generate_site(cls.output)
        cls.html = (cls.output / "index.html").read_text(encoding="utf-8")
        cls.papers = build.load_papers()
        cls.config = build.load_yaml(ROOT / "content/site.yaml")
        cls.reader = PdfReader(cls.output / cls.config["basic_info"]["cv_link"])
        cls.pdf_text = normalized(" ".join(page.extract_text() for page in cls.reader.pages))

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_cv_covers_all_papers_and_homepage_only_selected(self):
        for paper in self.papers:
            self.assertIn(normalized(paper["title"]), self.pdf_text)
            self.assertEqual(paper["selected"], paper["title"] in unescape(self.html))
        self.assertEqual(self.result["papers"], len(self.papers))
        self.assertEqual(self.result["selected"], sum(paper["selected"] for paper in self.papers))
        self.assertNotIn("fourth-year Ph.D.", self.pdf_text)
        self.assertNotIn("Incoming Postdoctoral", self.html)
        for term in ("LoopEva", "Shuimu", "Embodied Intelligence Systems Group"):
            self.assertIn(term, self.pdf_text)
            self.assertIn(term, self.html)

    def test_current_email_is_consistent_in_page_cv_and_pdf_link(self):
        email = self.config["basic_info"]["email"]
        self.assertIn(f'mailto:{email}', self.html)
        self.assertIn(email, self.pdf_text)
        pdf_links = [str(annotation.get_object().get("/A", {}).get("/URI", ""))
                     for page in self.reader.pages for annotation in page.get("/Annots", [])]
        self.assertIn(f"mailto:{email}", pdf_links)
        self.assertNotIn("zhang-br21@mails.tsinghua.edu.cn", self.html + self.pdf_text)

    def test_navigation_and_download_work_in_static_html(self):
        parser = build.PageReferences()
        parser.feed(self.html)
        for section in build.SECTIONS:
            self.assertIn(section["id"], parser.ids)
            self.assertIn("#" + section["id"], parser.references)
        self.assertIn(self.config["basic_info"]["cv_link"], parser.references)
        self.assertEqual(len(parser.ids), len(set(parser.ids)))

    def test_bundle_contains_only_referenced_public_assets(self):
        actual = {path.relative_to(self.output) for path in self.output.rglob("*") if path.is_file()}
        expected = build.deployment_assets(self.html, self.config["basic_info"]["cv_link"])
        self.assertEqual(actual, expected | {Path("index.html"), Path(".nojekyll")})
        self.assertNotIn(Path("LoopEva-团队介绍-v1.pdf"), actual)
        self.assertNotIn(Path("assets/images/BoruiZhang.jpg"), actual)
        self.assertNotIn(Path("assets/resume/张博睿-清华大学iVisionGroup.pdf"), actual)

    def test_missing_or_private_assets_and_broken_anchors_fail(self):
        cv = self.config["basic_info"]["cv_link"]
        for reference in ("assets/missing.png", "LoopEva-团队介绍-v1.pdf", "assets/../README.md", "#missing-section"):
            with self.subTest(reference=reference), self.assertRaises(ValueError):
                build.deployment_assets(f'<a href="{reference}">Link</a>', cv)

    def test_rebuild_removes_stale_public_files(self):
        target = self.directory / "stale"
        build.generate_site(target)
        (target / "private.pdf").write_text("not a public asset", encoding="utf-8")
        build.generate_site(target)
        self.assertFalse((target / "private.pdf").exists())

    def test_non_build_and_source_directories_are_preserved(self):
        target = self.directory / "notes"
        target.mkdir()
        note = target / "note.txt"
        note.write_text("keep this", encoding="utf-8")
        with self.assertRaises(ValueError):
            build.generate_site(target)
        self.assertEqual(note.read_text(encoding="utf-8"), "keep this")
        with self.assertRaises(ValueError):
            build.generate_site(ROOT / "content")

    def test_new_paper_requires_only_yaml_and_referenced_image(self):
        fixture_dir = self.directory / "fixture-papers"
        fixture_dir.mkdir()
        # A new record uses an existing image, with no template, code, or CV edits.
        base = next(paper for paper in self.papers if paper["selected"])
        fixture = dict(base, title="New Research & Representation", year=2027)
        fixture.pop("selected")
        (fixture_dir / "2027_new.yaml").write_text(yaml.safe_dump(fixture), encoding="utf-8")
        target = self.directory / "new-paper"
        with patch.object(build, "PAPER_DIR", fixture_dir):
            result = build.generate_site(target)
        html = unescape((target / "index.html").read_text(encoding="utf-8"))
        text = normalized(" ".join(page.extract_text() for page in PdfReader(target / self.config["basic_info"]["cv_link"]).pages))
        self.assertIn(fixture["title"], html)
        self.assertIn(fixture["title"], text)
        self.assertEqual(result["selected"], 1)


if __name__ == "__main__":
    unittest.main()
