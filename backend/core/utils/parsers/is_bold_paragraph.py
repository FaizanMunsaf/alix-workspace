from docx.text.paragraph import Paragraph


def is_bold_paragraph(paragraph: Paragraph) -> bool:
    runs = [run for run in paragraph.runs if run.text.strip()]
    return bool(runs) and all(run.bold for run in runs)
