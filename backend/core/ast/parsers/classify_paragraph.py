import re

from docx.text.paragraph import Paragraph

from .ast import ASTNode
from .helpers.heading_level import heading_level
from .helpers.is_bold_paragraph import is_bold_paragraph
from .helpers.leading_bold_label import leading_bold_label
from .helpers.truncate import truncate

_ARTICLE_RE = re.compile(
    r"^(article|section|clause)\s+([\dA-Za-z.]+)(?:[:.\-]\s*|\s+)(.*)$",
    re.IGNORECASE,
)
_QUESTION_RE = re.compile(r"^(Q\d+)[.)]\s+(.*)$", re.IGNORECASE)
_NUMBERED_RE = re.compile(r"^(\d+(?:\.\d+)*)(?:[.)])?\s+(.*)$")
_LETTER_RE = re.compile(r"^\(([a-z])\)\s+(.*)$", re.IGNORECASE)
_ROMAN_RE = re.compile(r"^\(([ivxlcdm]+)\)\s+(.*)$", re.IGNORECASE)


def classify_paragraph(paragraph: Paragraph, text: str) -> ASTNode | None:
    level = heading_level(paragraph)
    if level is not None:
        return ASTNode(
            node_type="heading" if level > 1 else "section",
            level=level,
            title=truncate(text),
            metadata={"source": "style", "style": paragraph.style.name},
        )

    question = _QUESTION_RE.match(text)
    if question:
        number, rest = question.groups()
        return ASTNode(
            node_type="section",
            level=1,
            title=truncate(
                f"{number.upper()} {rest}".strip() if rest else number.upper()
            ),
            metadata={"source": "question", "number": number.upper(), "bold": True},
        )

    bold_label = leading_bold_label(paragraph)
    if bold_label:
        label, rest = bold_label
        return ASTNode(
            node_type="section",
            level=1,
            title=truncate(label.rstrip(":").strip()),
            content=rest or None,
            metadata={"source": "bold_label"},
        )

    if is_bold_paragraph(paragraph):
        return ASTNode(
            node_type="heading",
            level=1,
            title=truncate(text),
            metadata={"source": "bold"},
        )

    article = _ARTICLE_RE.match(text)
    if article:
        kind, number, rest = article.groups()
        return ASTNode(
            node_type="section",
            level=1,
            title=truncate(f"{kind.title()} {number}".strip()),
            content=rest.strip() or None,
            metadata={"source": "label", "number": number},
        )

    numbered = _NUMBERED_RE.match(text)
    if numbered:
        number, rest = numbered.groups()
        depth = number.count(".")
        return ASTNode(
            node_type="sub_clause" if depth else "clause",
            level=10 + depth,
            title=truncate(number),
            content=rest.strip() or None,
            metadata={"source": "number", "number": number},
        )

    letter = _LETTER_RE.match(text)
    if letter:
        mark, rest = letter.groups()
        return ASTNode(
            node_type="sub_clause",
            level=20,
            title=truncate(f"({mark.lower()})"),
            content=rest.strip() or None,
            metadata={"source": "letter", "number": mark.lower()},
        )

    roman = _ROMAN_RE.match(text)
    if roman:
        mark, rest = roman.groups()
        return ASTNode(
            node_type="sub_clause",
            level=21,
            title=truncate(f"({mark.lower()})"),
            content=rest.strip() or None,
            metadata={"source": "roman", "number": mark.lower()},
        )

    return None
