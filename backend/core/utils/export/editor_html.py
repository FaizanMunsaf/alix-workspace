from core.utils.export.ast_to_html import ast_to_html


def editor_html(ast_json: dict | None) -> str:
    if not ast_json:
        return ""
    stored = ast_json.get("html")
    if isinstance(stored, str) and stored.strip():
        return stored
    return ast_to_html(ast_json.get("nodes") or [])
