from api.services.qa import _format_context
from core.schemas.clause_embedding import ClauseSearchHit
from ds.rag.prompts import load_prompt
import uuid


def _hit(content: str, category: str = "paragraph") -> ClauseSearchHit:
    return ClauseSearchHit(
        id=uuid.uuid4(),
        version_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        ast_node_id=uuid.uuid4(),
        clause_category=category,
        content=content,
        distance=0.1,
    )


def test_qa_prompt_requires_grounding_placeholders():
    text = load_prompt("qa")
    assert "{context}" in text
    assert "{query}" in text
    assert "{selection}" in text
    assert "ONLY" in text or "only" in text


def test_format_context_labels_sources():
    blocks = _format_context(
        [
            _hit("Liability is capped at fees.", "paragraph"),
            _hit("Termination for convenience.", "heading"),
        ],
        selection="",
    )
    assert blocks[0].startswith("[Source 1] (paragraph)")
    assert "Liability is capped" in blocks[0]
    assert blocks[1].startswith("[Source 2] (heading)")


def test_format_context_puts_selection_first():
    selection = "Liability is capped at fees."
    blocks = _format_context(
        [_hit(selection), _hit("Other clause about renewal.")],
        selection=selection,
    )
    assert blocks[0].startswith("[Selected]")
    assert "Liability is capped" in blocks[0]
    assert len(blocks) == 2
    assert "renewal" in blocks[1]
    assert "Liability is capped" not in blocks[1]
