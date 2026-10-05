from pathlib import Path

from core.config.settings import BACKEND_DIR
from core.database import get_sync_db_session
from core.repositories.knowledge import knowledge_chunk_crud, knowledge_source_crud
from core.schemas.knowledge import CreateKnowledgeChunk, CreateKnowledgeSource
from ds.rag.embeddings import get_embedding_model

KNOWLEDGE_DIR = BACKEND_DIR / "data" / "knowledge"

_SEED_FILES: list[tuple[str, str, str, str]] = [
    (
        "playbook",
        "Negotiation playbook — Liability",
        "Private playbook: cap liability at 12 months of fees.",
        "playbook_liability.md",
    ),
    (
        "playbook",
        "Negotiation playbook — Confidentiality",
        "Private playbook: mutual confidentiality with 3-year survival.",
        "playbook_confidentiality.md",
    ),
    (
        "public_ref",
        "Public legal stub — UCTA / CRA summary",
        "Replaceable public/legal layer mock (not legal advice).",
        "public_ucta_summary.md",
    ),
]


def chunk_markdown(text: str, *, max_chars: int = 900) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    size = 0
    for block in text.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        if size + len(block) + 2 > max_chars and current:
            parts.append("\n\n".join(current))
            current = [block]
            size = len(block)
        else:
            current.append(block)
            size += len(block) + 2
    if current:
        parts.append("\n\n".join(current))
    return parts or [text.strip()]


def ensure_demo_knowledge(*, force: bool = False) -> dict:
    """Idempotently seed demo playbooks + public refs with embeddings."""
    with get_sync_db_session() as db:
        existing = knowledge_source_crud.list_with_counts(db)
        if existing and not force:
            return {
                "seeded": False,
                "sources": len(existing),
                "message": "Knowledge sources already present.",
            }
        if force and existing:
            for source in existing:
                knowledge_source_crud.delete(db, str(source.id))

    embedder = get_embedding_model()
    created = 0
    chunks_total = 0
    for layer, title, description, filename in _SEED_FILES:
        path = KNOWLEDGE_DIR / filename
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8").strip()
        pieces = chunk_markdown(text)
        vectors = embedder.embed_documents(pieces)
        with get_sync_db_session() as db:
            source = knowledge_source_crud.create(
                db,
                CreateKnowledgeSource(
                    title=title,
                    source_layer=layer,  # type: ignore[arg-type]
                    description=description,
                ),
            )
            rows = [
                CreateKnowledgeChunk(
                    source_id=source.id,
                    chunk_index=index,
                    content=piece,
                    embedding=vector,
                )
                for index, (piece, vector) in enumerate(
                    zip(pieces, vectors, strict=True)
                )
            ]
            knowledge_chunk_crud.create_many(db, rows)
        created += 1
        chunks_total += len(pieces)

    return {
        "seeded": True,
        "sources": created,
        "chunks": chunks_total,
        "message": "Demo playbooks and public references seeded.",
    }


def knowledge_dir() -> Path:
    return KNOWLEDGE_DIR
