def truncate(value: str, limit: int = 255) -> str:
    value = value.strip()
    return value if len(value) <= limit else value[: limit - 1] + "…"
