from docx.text.paragraph import Paragraph


def leading_bold_label(paragraph: Paragraph) -> tuple[str, str] | None:
    runs = paragraph.runs
    if not runs or not runs[0].bold:
        return None

    label_parts: list[str] = []
    rest_parts: list[str] = []
    seen_normal = False
    for run in runs:
        if run.bold and not seen_normal:
            label_parts.append(run.text)
        else:
            seen_normal = True
            rest_parts.append(run.text)

    label = "".join(label_parts).strip()
    rest = "".join(rest_parts).strip()
    if not label or not rest or len(label) > 80:
        return None
    if label.endswith((":", "-", "—")) or label.startswith("Q"):
        return label, rest
    return None
