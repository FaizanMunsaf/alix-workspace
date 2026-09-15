import json
import re


def parse_llm_json(raw: str | dict) -> dict:
    if isinstance(raw, dict):
        if any(key in raw for key in ("after", "patches", "plan")):
            return raw
        inner = raw.get("response")
        if isinstance(inner, dict):
            return inner
        if isinstance(inner, str):
            raw = inner
        else:
            return raw
    text = str(raw).strip()
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fenced:
        text = fenced.group(1).strip()
    return json.loads(text)
