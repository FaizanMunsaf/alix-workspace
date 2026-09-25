import pytest

from core.utils.edits import (
    PatchConflict,
    apply_text_patch,
    count_plain_matches,
    parse_llm_json,
    plain_text_in_html,
    uniquify_excerpt,
)


def test_apply_text_patch_replaces_first_match_only():
    html = "<p>The cap is 24 months of fees. The cap is 24 months of fees.</p>"
    updated = apply_text_patch(html, "24 months of fees", "12 months of fees")
    assert updated.count("12 months of fees") == 1
    assert updated.count("24 months of fees") == 1


def test_apply_text_patch_uses_occurrence_index():
    html = "<p>The cap is 24 months of fees. The cap is 24 months of fees.</p>"
    updated = apply_text_patch(
        html, "24 months of fees", "12 months of fees", occurrence=1
    )
    assert updated.startswith("<p>The cap is 24 months of fees. The cap is 12 months")


def test_apply_text_patch_raises_when_original_missing():
    with pytest.raises(PatchConflict):
        apply_text_patch("<p>Unrelated clause.</p>", "liability cap", "new text")


def test_apply_text_patch_matches_across_html_tags():
    html = "<p>The <strong>liability</strong> cap is twelve months.</p>"
    updated = apply_text_patch(
        html, "liability cap is twelve months", "liability cap is six months"
    )
    assert "liability cap is six months" in updated
    assert "twelve months" not in updated
    assert updated.count("<strong>") == updated.count("</strong>")
    assert "<p>" in updated and "</p>" in updated


def test_plain_text_in_html_finds_split_runs():
    html = "<p>Confidential <em>Information</em> means…</p>"
    assert plain_text_in_html(html, "Confidential Information means")


def test_count_and_uniquify_excerpt():
    html = "<p>Fee is due. Fee is late.</p>"
    assert count_plain_matches(html, "Fee is") == 2
    unique = uniquify_excerpt(html, "Fee is", "Fee is due. Fee is late.")
    assert unique is not None
    assert count_plain_matches(html, unique) == 1
    assert unique.startswith("Fee is")
    assert len(unique) > len("Fee is")


def test_apply_occurrence_second_duplicate():
    html = "<p>Alpha clause. Alpha clause.</p>"
    updated = apply_text_patch(html, "Alpha clause", "Beta clause", occurrence=1)
    assert updated == "<p>Alpha clause. Beta clause.</p>"

    raw = """```json
{"after": "Mutual confidentiality.", "rationale": "Make both parties bound."}
```"""
    payload = parse_llm_json(raw)
    assert payload["after"] == "Mutual confidentiality."
