"""Prepare the two submission lists from the supplied manuscript."""

import logging
import re
from pathlib import Path
from xml.sax.saxutils import escape

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate


logging.disable(logging.CRITICAL)
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf"
PAPER = OUTPUT / "main.pdf"
source = (ROOT / "overleaf" / "main.tex").read_text(encoding="utf-8")
reader = PdfReader(PAPER)

for name, filename in (
    ("SubmissionTimes", "times.ttf"),
    ("SubmissionTimesBold", "timesbd.ttf"),
):
    pdfmetrics.registerFont(TTFont(name, str(Path("C:/Windows/Fonts") / filename)))


def plain_tex(text):
    text = text.replace(r"\LaTeX{}", "LaTeX")
    text = re.sub(r"\\(?:ref|label)\{[^}]*\}", "", text)
    text = text.replace("``", '"').replace("''", '"')
    text = text.replace("--", "-").replace(r"\%", "%")
    return " ".join(text.split())


def normalize(text):
    text = text.replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    # Ignore typesetting line breaks, including discretionary hyphenation.
    text = re.sub(r"-\s*\n\s*", "", text)
    return re.sub(r"\s+", "", text)


title = re.search(r"\\title\{([^}]+)\}", source).group(1)
authors = "Selim S. Balcisoy, Sena Kahya, and Sude Tiras"
first_footnote, affiliation = re.findall(r"\\thanks\{([^}]+)\}", source)
figures = re.findall(r"\\begin\{figure\*?\}(.*?)\\end\{figure\*?\}", source, re.S)
captions = [
    plain_tex(re.search(r"\\caption\{(.*?)\}\s*\\label", figure, re.S).group(1))
    for figure in figures
]
assert len(captions) == 2, "Expected exactly the two figures in the supplied PDF."

pdf_affiliation = re.search(
    r"The authors are with.*?sude\.tiras@sabanciuniv\.edu\)\.",
    reader.pages[0].extract_text(),
    re.S,
).group(0)
assert normalize(affiliation) == normalize(pdf_affiliation)
for page_index, caption in zip((3, 7), captions):
    assert any(normalize(caption) in normalize(page.extract_text()) for page in reader.pages)

heading = ParagraphStyle(
    "DocumentHeading",
    fontName="SubmissionTimesBold",
    fontSize=16,
    leading=20,
    alignment=TA_CENTER,
    spaceAfter=16,
    textColor=colors.black,
)
paper_title = ParagraphStyle(
    "PaperTitle",
    fontName="SubmissionTimesBold",
    fontSize=12,
    leading=16,
    alignment=TA_CENTER,
    spaceAfter=8,
)
author_style = ParagraphStyle(
    "Authors",
    fontName="SubmissionTimes",
    fontSize=11,
    leading=15,
    alignment=TA_CENTER,
    spaceAfter=30,
)


def make_document(filename, heading_text, paragraphs, leading):
    document = SimpleDocTemplate(
        str(OUTPUT / filename),
        pagesize=letter,
        leftMargin=72,
        rightMargin=72,
        topMargin=72,
        bottomMargin=72,
        title=f"{heading_text} - {title}",
        author=authors,
    )
    body = ParagraphStyle(
        "Body",
        fontName="SubmissionTimes",
        fontSize=12,
        leading=leading,
        spaceAfter=18,
        splitLongWords=False,
    )
    story = [
        Paragraph(escape(heading_text), heading),
        Paragraph(escape(title), paper_title),
        Paragraph(escape(authors), author_style),
    ]
    story.extend(Paragraph(escape(text), body) for text in paragraphs)
    document.build(story)
    result = PdfReader(OUTPUT / filename)
    assert len(result.pages) == 1, f"{filename} must remain a single page."
    print(filename, "1 page", "body leading", leading, "pt")


make_document("Footnotes.pdf", "Footnotes", ["Manuscript received", first_footnote, affiliation], 24)
make_document(
    "Figure_Captions.pdf",
    "Figure Captions",
    [f"Fig. {i}. {caption}" for i, caption in enumerate(captions, start=1)],
    18,
)
