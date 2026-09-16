import re

from docx.text.paragraph import Paragraph

_HEADING_RE = re.compile(r"^heading\s*(\d+)$", re.I)


def heading_level(paragraph: Paragraph) -> int | None:
    style_name = (paragraph.style.name or "").strip()
    if style_name.lower() == "title":
        return 1
    match = _HEADING_RE.match(style_name)
    if match:
        return int(match.group(1))
    try:
        outline = paragraph._p.pPr.outlineLvl
        if outline is not None:
            return int(outline.val) + 1
    except AttributeError:
        pass
    return None
