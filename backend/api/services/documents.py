from fastapi import HTTPException

from core.config.settings import settings
from core.database import get_sync_db_session
from core.models.document_version import DocumentVersion
from core.models.documents import Document
from ds.rag.vectorstores import get_vectorstore


def upload_document(
    *,
    filename: str,
    data: bytes,
    content_type: str | None,
    title: str | None,
) -> dict:
    try:
        content = data.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400, detail="File must be UTF-8 text."
        ) from None
    if not content.strip():
        raise HTTPException(status_code=400, detail="File is empty.")

    doc_title = (title or filename).strip() or "untitled"
    suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"

    with get_sync_db_session() as db:
        document = Document(
            title=doc_title,
            document_type=suffix,
            status="ingested",
            metadata_info={"filename": filename, "content_type": content_type},
        )
        db.add(document)
        db.flush()

        version = DocumentVersion(
            document_id=document.id,
            version_number=1,
            raw_text=content,
            file_path=filename,
            processing_status="completed",
        )
        db.add(version)
        db.flush()

        document_id = str(document.id)
        version_id = str(version.id)
        db.commit()

    chunks = get_vectorstore().ingest_text(
        text=content,
        metadata={
            "document_id": document_id,
            "version_id": version_id,
            "title": doc_title,
            "filename": filename,
        },
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
    )

    return {
        "document_id": document_id,
        "version_id": version_id,
        "title": doc_title,
        "chunks": len(chunks),
    }
