from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path

from docx import Document
from docx.shared import Inches
from docx.text.paragraph import Paragraph

from core.ast.parsers.helpers.extract_images import resolve_image_bytes
from core.config.settings import BACKEND_DIR

_DEFAULT_UPLOADS = BACKEND_DIR / "uploads"


class _Run:
    def __init__(self, text: str, bold: bool = False, italic: bool = False) -> None:
        self.text = text
        self.bold = bold
        self.italic = italic


class _HtmlToDocx(HTMLParser):
    def __init__(self, *, uploads_dir: Path) -> None:
        super().__init__(convert_charrefs=True)
        self.uploads_dir = uploads_dir
        self.document = Document()
        self.bold = 0
        self.italic = 0
        self.tags: list[str] = []
        self.runs: list[_Run] = []
        self.list_kind: str | None = None
        self.list_depth = 0
        self.in_table = False
        self.rows: list[list[str]] = []
        self.row: list[str] = []
        self.cell: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        self.tags.append(tag)
        if tag in {"strong", "b"}:
            self.bold += 1
        elif tag in {"em", "i"}:
            self.italic += 1
        elif tag == "br":
            self._append_text("\n")
        elif tag == "img":
            self._add_image(dict(attrs).get("src") or "")
        elif tag in {"ul", "ol"}:
            self.list_kind = tag
            self.list_depth += 1
        elif tag == "table":
            self.in_table = True
            self.rows = []
        elif tag == "tr":
            self.row = []
        elif tag in {"td", "th"}:
            self.cell = []

    def handle_endtag(self, tag: str) -> None:
        if tag in {"strong", "b"} and self.bold:
            self.bold -= 1
        elif tag in {"em", "i"} and self.italic:
            self.italic -= 1
        elif tag in {"p", "h1", "h2", "h3", "h4", "li"}:
            nested_in_list = tag == "p" and "li" in self.tags
            if not self.in_table and not nested_in_list:
                self._flush_block(tag)
        elif tag in {"td", "th"}:
            self.row.append("".join(self.cell).strip())
            self.cell = []
        elif tag == "tr":
            if self.row:
                self.rows.append(self.row)
            self.row = []
        elif tag == "table":
            self._flush_table()
            self.in_table = False
        elif tag in {"ul", "ol"}:
            self.list_depth = max(0, self.list_depth - 1)
            if self.list_depth == 0:
                self.list_kind = None
            else:
                # Restore outer list kind from remaining open tags.
                self.list_kind = "ol" if "ol" in self.tags[:-1] else "ul"
        if self.tags and self.tags[-1] == tag:
            self.tags.pop()
        elif tag in self.tags:
            self.tags.reverse()
            self.tags.remove(tag)
            self.tags.reverse()

    def handle_data(self, data: str) -> None:
        if self.in_table and ("td" in self.tags or "th" in self.tags):
            self.cell.append(data)
            return
        if self.in_table:
            return
        self._append_text(data)

    def _append_text(self, data: str) -> None:
        if not data:
            return
        self.runs.append(_Run(data, bold=self.bold > 0, italic=self.italic > 0))

    def _add_image(self, src: str) -> None:
        if self.runs:
            self._flush_block("p")
        blob = resolve_image_bytes(src, uploads_dir=self.uploads_dir)
        if blob is None:
            return
        try:
            self.document.add_picture(BytesIO(blob), width=Inches(5.5))
        except (OSError, ValueError, TypeError):
            return

    def _flush_block(self, tag: str) -> None:
        runs = self.runs
        self.runs = []
        if not any(run.text.strip() for run in runs):
            return
        if tag in {"h1", "h2", "h3", "h4"}:
            level = {"h1": 1, "h2": 2, "h3": 3, "h4": 4}[tag]
            self.document.add_heading("".join(run.text for run in runs), level=level)
            return
        if tag == "li":
            style = "List Number" if self.list_kind == "ol" else "List Bullet"
            paragraph = self._paragraph(style)
            # Visible indent for nested lists (Word auto-number levels are not rebuilt).
            if self.list_depth > 1:
                try:
                    paragraph.paragraph_format.left_indent = Inches(
                        0.25 * (self.list_depth - 1)
                    )
                except (AttributeError, ValueError):
                    pass
            _apply_runs(paragraph, runs)
            return
        paragraph = self.document.add_paragraph()
        _apply_runs(paragraph, runs)

    def _paragraph(self, style: str) -> Paragraph:
        try:
            return self.document.add_paragraph(style=style)
        except (KeyError, ValueError):
            return self.document.add_paragraph()

    def _flush_table(self) -> None:
        rows = [row for row in self.rows if any(cell.strip() for cell in row)]
        self.rows = []
        if not rows:
            return
        cols = max(len(row) for row in rows)
        table = self.document.add_table(rows=len(rows), cols=cols)
        for row_index, values in enumerate(rows):
            for col_index in range(cols):
                table.rows[row_index].cells[col_index].text = (
                    values[col_index] if col_index < len(values) else ""
                )


def _apply_runs(paragraph: Paragraph, runs: list[_Run]) -> None:
    for run in runs:
        docx_run = paragraph.add_run(run.text)
        docx_run.bold = run.bold
        docx_run.italic = run.italic


def html_to_docx(markup: str, *, uploads_dir: Path | None = None) -> bytes:
    parser = _HtmlToDocx(uploads_dir=uploads_dir or _DEFAULT_UPLOADS)
    parser.feed(markup or "")
    parser.close()
    if parser.runs:
        parser._flush_block("p")
    if not parser.document.paragraphs and not parser.document.tables:
        parser.document.add_paragraph()
    buffer = BytesIO()
    parser.document.save(buffer)
    return buffer.getvalue()
