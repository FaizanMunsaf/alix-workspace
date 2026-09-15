import pytest

from core.utils.edits import PatchConflict, apply_text_patch, parse_llm_json


def test_apply_text_patch_replaces_first_match_only():
    html = "<p>The cap is 24 months of fees. The cap is 24 months of fees.</p>"
    updated = apply_text_patch(html, "24 months of fees", "12 months of fees")
    assert updated.count("12 months of fees") == 1
    assert updated.count("24 months of fees") == 1


def test_apply_text_patch_raises_when_original_missing():
    with pytest.raises(PatchConflict):
        apply_text_patch("<p>Unrelated clause.</p>", "liability cap", "new text")


def test_parse_llm_json_reads_fenced_payload():
    raw = """```json
{"after": "Mutual confidentiality.", "rationale": "Make both parties bound."}
```"""
    payload = parse_llm_json(raw)
    assert payload["after"] == "Mutual confidentiality."
