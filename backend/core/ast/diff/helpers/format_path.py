def format_path(parts: list[str]) -> str:
    return " / ".join(part for part in parts if part)
