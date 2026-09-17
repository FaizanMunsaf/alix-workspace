from api.services.documents import _snapshot_html
from core.schemas.history import CreateDocumentChange, RestoreVersionRequest
from core.utils.export import html_to_docx


def test_create_change_defaults_to_pending():
    payload = CreateDocumentChange(
        document_id="11111111-1111-1111-1111-111111111111",
        actor="ai",
        target="Selected text",
        before="old",
        after="new",
    )
    assert payload.decision == "pending"
    assert payload.decided_at is None


def test_restore_request_requires_version_id():
    body = RestoreVersionRequest(version_id="22222222-2222-2222-2222-222222222222")
    assert str(body.version_id) == "22222222-2222-2222-2222-222222222222"


def test_snapshot_html_keeps_editor_markup():
    markup = "<p>The liability cap is 24 months of fees.</p>"
    ast_json, raw_text = _snapshot_html(markup, html_to_docx(markup), fallback={})
    assert ast_json["html"] == markup
    assert "liability cap" in raw_text.lower()
    assert ast_json.get("nodes")
