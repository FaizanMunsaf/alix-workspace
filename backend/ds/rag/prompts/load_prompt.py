from pathlib import Path

_DIR = Path(__file__).resolve().parent


def load_prompt(name: str) -> str:
    path = _DIR / f"{name}.txt"
    if not path.is_file():
        raise FileNotFoundError(f"Prompt '{name}' was not found at {path}")
    return path.read_text(encoding="utf-8")
