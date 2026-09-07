import uuid
from pathlib import Path

from fastapi import BackgroundTasks, HTTPException, status

from api.backgrounds import enqueue_document_parse
from core.config.settings import BACKEND_DIR
from core.database import get_sync_db_session
from core.repositories import document_crud, document_version_crud
from core.schemas.document import CreateDocument, DocumentUploadResponse
from core.schemas.document_version import CreateDocumentVersion

UPLOAD_DIR = BACKEND_DIR / "uploads"
DOCX_CONTENT_TYPES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/octet-stream",
}


def upload_document(
    *,
    filename: str,
    data: bytes,
    content_type: str | None,
    title: str | None,
    background_tasks: BackgroundTasks,
) -> DocumentUploadResponse:
    safe_name = Path(filename).name
    if not safe_name.lower().endswith(".docx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .docx files are accepted.",
        )
    if content_type and content_type.lower() not in DOCX_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .docx files are accepted.",
        )
    if not data or not data.startswith(b"PK"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty or is not a valid .docx document.",
        )

    doc_title = (title or Path(safe_name).stem).strip() or "untitled"
    document_id = uuid.uuid4()
    version_id = uuid.uuid4()

    dest_dir = UPLOAD_DIR / str(document_id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    file_path = dest_dir / safe_name
    file_path.write_bytes(data)

    with get_sync_db_session() as db:
        document = document_crud.create(
            db,
            CreateDocument(
                id=document_id,
                title=doc_title,
                document_type="docx",
                status="processing",
                metadata_info={"filename": safe_name, "content_type": content_type},
            ),
        )
        version = document_version_crud.create(
            db,
            CreateDocumentVersion(
                id=version_id,
                document_id=document.id,
                version_number=1,
                file_path=str(file_path),
                processing_status="pending",
            ),
        )
        response = DocumentUploadResponse(
            document_id=document.id,
            version_id=version.id,
            title=document.title,
            status=document.status,
            processing_status=version.processing_status,
            message="Document uploaded. Parsing started in the background.",
            filename=safe_name,
            file_path=str(file_path),
        )

    enqueue_document_parse(
        background_tasks,
        document_id=str(response.document_id),
        version_id=str(response.version_id),
        file_path=response.file_path,
        title=response.title,
        filename=response.filename,
    )
    return response
