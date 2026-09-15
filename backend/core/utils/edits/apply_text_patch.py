class PatchConflict(ValueError):
    pass


def apply_text_patch(html: str, before: str, after: str) -> str:
    target = (before or "").strip()
    if not target:
        raise PatchConflict("The original text is empty.")
    if target not in html:
        raise PatchConflict("The original text is no longer in the document.")
    return html.replace(target, after, 1)
