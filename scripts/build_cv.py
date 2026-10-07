"""A public academic CV rendered from the same YAML data as the homepage."""
from __future__ import annotations

from datetime import datetime
from html import escape, unescape
from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import BaseDocTemplate, Flowable, Frame, Image, KeepTogether, PageTemplate, Paragraph, Spacer, Table, TableStyle

VENUES = {
    "TPAMI": "IEEE Transactions on Pattern Analysis and Machine Intelligence",
    "CJE": "Chinese Journal of Electronics",
    "TGRS": "IEEE Transactions on Geoscience and Remote Sensing",
    "CVPR": "IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)",
    "ICCV": "IEEE/CVF International Conference on Computer Vision (ICCV)",
    "ECCV": "European Conference on Computer Vision (ECCV)",
    "ICLR": "International Conference on Learning Representations (ICLR)",
    "arXiv": "arXiv preprint",
}


def plain(value: str) -> str:
    return unescape(re.sub(r"<[^>]*>", "", value)).replace("—", "-").replace("–", "-")


def safe(value: str) -> str:
    return escape(plain(str(value)))


INK = colors.HexColor("#171717")
MUTED = colors.HexColor("#484848")
WINE = colors.HexColor("#990035")
RULE = colors.HexColor("#b8ce75")


class SectionHeading(Flowable):
    """The original CV's sans-serif headings and fading green rules."""
    keepWithNext = True
    spaceBefore = 14
    spaceAfter = 8

    def __init__(self, title):
        super().__init__()
        self.title = title
        self.height = 21

    def wrap(self, available_width, available_height):
        self.width = available_width
        return self.width, self.height

    def draw(self):
        self.canv.setFillColor(INK)
        self.canv.setFont("Helvetica-Bold", 13)
        self.canv.drawString(0, 8, self.title)
        # Small adjacent rectangles reproduce the original unobtrusive gradient.
        for index in range(64):
            fraction = index / 63
            self.canv.setFillColor(colors.linearlyInterpolatedColor(RULE, colors.white, 0, 1, fraction))
            self.canv.rect(index * self.width / 64, 2, self.width / 64 + .1, 2.4, stroke=0, fill=1)


class Marker(Flowable):
    """Vector bookmarks and numbered circles; no icon fonts are required."""
    def __init__(self, number=None):
        super().__init__()
        self.number = number
        self.width = 15
        self.height = 14

    def draw(self):
        self.canv.setFillColor(WINE)
        if self.number is not None:
            self.canv.circle(7, 7, 7, stroke=0, fill=1)
            self.canv.setFillColor(colors.white)
            self.canv.setFont("Helvetica", 8.5)
            self.canv.drawCentredString(7, 4, str(self.number))
        else:
            shape = self.canv.beginPath()
            shape.moveTo(3, 2)
            shape.lineTo(3, 12)
            shape.lineTo(9, 12)
            shape.lineTo(9, 2)
            shape.lineTo(6, 4)
            shape.close()
            self.canv.drawPath(shape, stroke=0, fill=1)


def generate_cv(config: dict, papers: list[dict], links: list[dict], output: Path, updated: datetime) -> None:
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("CVTitle", fontName="Helvetica-Bold", fontSize=20, leading=25, textColor=INK, spaceAfter=5))
    styles.add(ParagraphStyle("CVBody", fontName="Times-Roman", fontSize=10.5, leading=14, textColor=INK, spaceAfter=0))
    styles.add(ParagraphStyle("CVContact", fontName="Courier", fontSize=8, leading=12, textColor=INK, spaceAfter=2))
    styles.add(ParagraphStyle("CVSubsection", fontName="Helvetica-Bold", fontSize=11, leading=15, textColor=INK, spaceBefore=10, spaceAfter=6, keepWithNext=True))
    styles.add(ParagraphStyle("CVSmall", parent=styles["CVBody"], fontSize=9.5, leading=12, textColor=MUTED))
    styles.add(ParagraphStyle("CVDate", parent=styles["CVContact"], fontSize=8, leading=12, spaceAfter=0))
    styles.add(ParagraphStyle("CVPublication", parent=styles["CVBody"], fontSize=10.3, leading=13.5))
    info = config["basic_info"]
    width = A4[0] - 44 * mm
    story = []

    def p(text, style="CVBody"):
        return Paragraph(text, styles[style])

    def section(title):
        story.append(SectionHeading(title))

    def add_group(items):
        # Keep section/subsection headings with their first complete entry.
        while story and isinstance(story[-1], (Paragraph, SectionHeading)) and story[-1].getKeepWithNext():
            items.insert(0, story.pop())
        story.append(KeepTogether(items))

    def table(cells, columns, bottom=4):
        item = Table(cells, colWidths=columns, hAlign="LEFT")
        item.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), bottom),
        ]))
        return item

    def bullet(text, number=None, style="CVBody", bottom=5):
        return table([[Marker(number), p(text, style)]], [22, width - 22], bottom)

    def record(item, key, description=""):
        date = safe(item["date"]).replace(" - ", "<br/>- ")
        text = f'<b>{safe(item[key])}</b>, {safe(item["organization"])}.'
        if description:
            text += f'<br/><font color="#484848">{safe(description)}</font>'
        add_group([table([[p(date, "CVDate"), Marker(), p(text)]],
                         [24 * mm, 18, width - 24 * mm - 18], 6)])

    photo_relative = Path(info.get("cv_image", info["profile_image"]))
    root = Path(__file__).resolve().parents[1]
    photo_path = (root / photo_relative).resolve()
    if not photo_path.is_relative_to(root / "assets") or not photo_path.is_file():
        raise ValueError("The CV portrait must be an existing file inside assets/.")
    photo_width, photo_height = ImageReader(str(photo_path)).getSize()
    photo = Image(str(photo_path), width=52, height=52 * photo_height / photo_width)
    contact = f'<link href="mailto:{escape(info["email"], quote=True)}" color="#990035">{safe(info["email"])}</link>'
    public_links = [link for link in links if link.get("cv")]
    public_links.append({"url": config["company"]["url"], "name": config["company"]["name"]})
    link_line = '  |  '.join(f'<link href="{escape(link["url"], quote=True)}" color="#990035">{safe(link["name"])}</link>' for link in public_links)
    header = [
        p(safe(info["name"]), "CVTitle"),
        p(f'{safe(info["role"])}, {safe(info["university"])}', "CVSmall"),
        p(f'{safe(config["company"]["role"])}, {safe(config["company"]["name"])}', "CVSmall"),
        Spacer(1, 5), p(contact, "CVContact"), p(link_line, "CVContact"),
    ]
    masthead = table([[header, photo]], [width - 52, 52], 0)
    masthead.setStyle(TableStyle([("VALIGN", (0, 0), (0, 0), "MIDDLE")]))
    story.append(masthead)
    story.append(Spacer(1, 4))

    section("About Me")
    add_group([bullet(safe(info["cv_summary"]), bottom=0)])
    section("Appointments")
    for item in config["experience"]:
        record(item, "role")
    section("Education")
    for item in config["education"]:
        description = ""
        if item["degree"].startswith("Ph.D."):
            description = f'Advisor: {info["advisor_name"]}.'
        elif item["degree"].startswith("B.E."):
            description = item["description"]
        record(item, "degree", description)
    section("Research Interests")
    for area in config["research_areas"]:
        add_group([bullet(safe(area["title"]), bottom=2)])

    section("Research Publications")
    # Attach the note to the section and first subgroup to avoid lonely headings.
    note = p("* indicates equal contribution. Borui Zhang's name is shown in bold.", "CVSmall")
    note.keepWithNext = True
    story.append(note)
    groups = [
        ("Journal Articles", [paper for paper in papers if paper["type"] == "publication" and paper["kind"] == "journal"]),
        ("Conference Proceedings", [paper for paper in papers if paper["type"] == "publication" and paper["kind"] == "conference"]),
        ("Preprints", [paper for paper in papers if paper["type"] == "preprint"]),
    ]
    for title, entries in groups:
        if not entries:
            continue
        story.append(p(title, "CVSubsection"))
        for number, paper in enumerate(entries, 1):
            names = []
            for author in paper["authors"]:
                name = safe(author["name"])
                if author.get("highlight") or author["name"] == info["name"]:
                    name = f"<b>{name}</b>"
                if author.get("equal_contrib"):
                    name += "<super>*</super>"
                names.append(name)
            paper_title = safe(paper["title"])
            if paper.get("links"):
                url = escape(paper["links"][0]["url"], quote=True)
                paper_title = f'<link href="{url}" color="#171717">{paper_title}</link>'
            venue = safe(paper.get("venue_full", VENUES.get(paper["venue"], paper["venue"])))
            citation = f'{", ".join(names)}, "{paper_title}," <i>{venue}</i>, {paper["year"]}'
            if paper.get("pages"):
                citation += f', pp. {safe(paper["pages"])}'
            citation += "."
            add_group([bullet(citation, number, "CVPublication", bottom=7)])

    section("Honors and Awards")
    # Keep this short award section on one page, with one date per year.
    honor_groups = {}
    for honor in config["honors"]:
        honor_groups.setdefault(honor["year"], []).append(honor["title"])
    rows = []
    for year, titles in honor_groups.items():
        rows.extend([[p(safe(year) if index == 0 else "", "CVDate"), Marker(), p(f"<b>{safe(title)}</b>")]
                     for index, title in enumerate(titles)])
    add_group([table(rows, [24 * mm, 18, width - 24 * mm - 18], 4)])

    section("Academic Services")
    add_group([bullet(f'<b>Conference reviewer.</b> {safe(config["services"]["conference"])}', bottom=5)])
    add_group([bullet(f'<b>Journal reviewer.</b> {safe(config["services"]["journal"])}', bottom=0)])
    section("Teaching")
    for item in config["teaching"]:
        record(item, "role")
    section("Interests")
    add_group([bullet(safe(config["interests"]), bottom=0)])

    def decorate(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(MUTED)
        if doc.page > 1:
            canvas.setFont("Helvetica", 8)
            canvas.drawString(22 * mm, A4[1] - 12 * mm, f"{info['name']} | Curriculum Vitae")
        canvas.setFont("Times-Italic", 8)
        canvas.drawString(22 * mm, 10 * mm, f"Updated {updated.strftime('%d %b %Y')}")
        canvas.drawRightString(A4[0] - 22 * mm, 10 * mm, str(doc.page))
        canvas.restoreState()

    doc = BaseDocTemplate(
        str(output), pagesize=A4, leftMargin=22 * mm, rightMargin=22 * mm,
        topMargin=18 * mm, bottomMargin=19 * mm,
        title=f"{info['name']} - Academic CV", author=info["name"],
        subject="Academic curriculum vitae", invariant=1,
    )
    # A zero-padding frame keeps rules, tables, photographs, and footers on
    # precisely the same margins; the default six-point inset breaks alignment.
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates(PageTemplate(id="CV", frames=[frame], onPage=decorate))
    doc.build(story)
