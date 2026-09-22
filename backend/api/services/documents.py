import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import BackgroundTasks, HTTPException, status

from api.backgrounds import enqueue_document_parse, ingest_parsed_version
from core.ast.parsers import ASTNode, parse_docx
from core.config.settings import BACKEND_DIR
from core.database import get_sync_db_session
from core.models.document_version import DocumentVersion
from core.repositories import (
    document_change_crud,
    document_crud,
    document_version_crud,
)
from core.schemas.document import (
    CreateDocument,
    DocumentDetailResponse,
    DocumentListItem,
    DocumentUploadResponse,
)
from core.schemas.document_version import (
    CreateDocumentVersion,
    DocumentVersionResponse,
)
from core.schemas.history import CreateDocumentChange, UpdateDocumentChange
from core.utils.export import editor_html, html_to_docx, html_to_text

logger = logging.getLogger(__name__)

UPLOAD_DIR = BACKEND_DIR / "uploads"
DOCX_CONTENT_TYPES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/octet-stream",
}
_UNSAFE_FILENAME = re.compile(r"[^A-Za-z0-9._-]+")


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


def list_documents() -> list[DocumentListItem]:
    with get_sync_db_session() as db:
        documents = sorted(
            document_crud.get_all(db),
            key=lambda document: document.created_at,
            reverse=True,
        )
        items: list[DocumentListItem] = []
        for document in documents:
            versions = document_version_crud.list_by_document_id(db, str(document.id))
            latest = versions[-1] if versions else None
            items.append(
                DocumentListItem(
                    document_id=document.id,
                    version_id=latest.id if latest else None,
                    title=document.title,
                    status=document.status,
                    processing_status=latest.processing_status if latest else "pending",
                    version_number=latest.version_number if latest else 1,
                    created_at=document.created_at,
                )
            )
        return items


def get_document(document_id: str) -> DocumentDetailResponse:
    with get_sync_db_session() as db:
        return _document_detail(db, document_id)


def save_document_content(
    document_id: str,
    *,
    html: str,
    version_id: str | None = None,
) -> DocumentDetailResponse:
    markup = html.strip()
    if not markup:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document content is empty.",
        )
    with get_sync_db_session() as db:
        document = document_crud.get(db, document_id)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document was not found.",
            )
        versions = document_version_crud.list_by_document_id(db, document_id)
        if not versions:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Document has no versions to save.",
            )
        if editor_html(versions[-1].ast_json).strip() == markup:
            return _document_detail(db, document_id)
    return create_checkpoint(
        document_id,
        html=markup,
        actor="user",
        instruction="Manual save",
        target="Document",
    )


def restore_version(document_id: str, version_id: str) -> DocumentDetailResponse:
    with get_sync_db_session() as db:
        versions = document_version_crud.list_by_document_id(db, document_id)
        source = _pick_version(versions, version_id)
        html = editor_html(source.ast_json)
        if not html.strip() and source.raw_text:
            html = f"<p>{source.raw_text}</p>"
        number = source.version_number
    return create_checkpoint(
        document_id,
        html=html,
        actor="user",
        instruction=f"Restore version {number}",
        target=f"Version {number}",
        after=html,
    )


def create_checkpoint(
    document_id: str,
    *,
    html: str,
    actor: Literal["user", "ai"],
    instruction: str | None,
    target: str,
    before: str | None = None,
    after: str | None = None,
    rationale: str | None = None,
    change_id: str | None = None,
) -> DocumentDetailResponse:
    markup = html.strip()
    if not markup:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document content is empty.",
        )

    tree: list[ASTNode] | None = None
    with get_sync_db_session() as db:
        document = document_crud.get(db, document_id)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document was not found.",
            )
        versions = document_version_crud.list_by_document_id(db, document_id)
        if not versions:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Document has no versions to save.",
            )
        latest = versions[-1]
        if change_id:
            change = document_change_crud.get(db, change_id)
            if change is None or str(change.document_id) != str(document.id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Change was not found.",
                )
            if change.decision != "pending":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Change is no longer pending.",
                )
        previous_html = editor_html(latest.ast_json)
        new_number = latest.version_number + 1
        dest_dir = UPLOAD_DIR / str(document.id)
        dest_dir.mkdir(parents=True, exist_ok=True)
        file_path = dest_dir / f"v{new_number}.docx"
        docx_bytes = html_to_docx(markup)
        file_path.write_bytes(docx_bytes)
        ast_json, raw_text, tree = _snapshot_html(
            markup,
            docx_bytes,
            fallback=dict(latest.ast_json or {}),
            document_id=document_id,
            media_dir=dest_dir / "media",
        )
        version = document_version_crud.create(
            db,
            CreateDocumentVersion(
                document_id=document.id,
                version_number=new_number,
                raw_text=raw_text,
                file_path=str(file_path),
                ast_json=ast_json,
                processing_status="completed",
            ),
        )
        version_id = str(version.id)
        now = datetime.now(timezone.utc)
        if change_id:
            document_change_crud.update(
                db,
                change_id,
                UpdateDocumentChange(
                    result_version_id=version.id,
                    decision="accepted",
                    decided_at=now,
                ),
            )
        else:
            document_change_crud.create(
                db,
                CreateDocumentChange(
                    document_id=document.id,
                    version_id=latest.id,
                    result_version_id=version.id,
                    actor=actor,
                    instruction=instruction,
                    target=target,
                    before=before if before is not None else previous_html,
                    after=after if after is not None else markup,
                    rationale=rationale,
                    decision="accepted",
                    decided_at=now,
                ),
            )
        detail = _document_detail(db, document_id)

    if tree:
        try:
            ingest_parsed_version(
                document_id=document_id,
                version_id=version_id,
                tree=tree,
            )
        except Exception:
            logger.exception(
                "Failed to index embeddings for document %s version %s",
                document_id,
                version_id,
            )

    return detail


def _snapshot_html(
    markup: str,
    data: bytes,
    *,
    fallback: dict,
    document_id: str | None = None,
    media_dir: Path | None = None,
) -> tuple[dict, str, list[ASTNode] | None]:
    try:
        raw_text, tree = parse_docx(
            data,
            document_id=document_id,
            media_dir=media_dir,
        )
        return (
            {"nodes": [node.to_dict() for node in tree], "html": markup},
            raw_text or html_to_text(markup),
            tree,
        )
    except Exception:  # noqa: BLE001
        snapshot = dict(fallback)
        snapshot["html"] = markup
        return snapshot, html_to_text(markup), None


def read_document_media(document_id: str, filename: str) -> tuple[bytes, str]:
    from core.ast.parsers.helpers.extract_images import (
        guess_content_type,
        media_file_path,
    )

    path = media_file_path(
        uploads_dir=UPLOAD_DIR,
        document_id=document_id,
        filename=filename,
    )
    if path is None or not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file was not found.",
        )
    with get_sync_db_session() as db:
        if document_crud.get(db, document_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document was not found.",
            )
    return path.read_bytes(), guess_content_type(filename)


def export_document_docx(
    document_id: str,
    *,
    version_id: str | None = None,
) -> tuple[bytes, str]:
    with get_sync_db_session() as db:
        document = document_crud.get(db, document_id)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document was not found.",
            )
        versions = document_version_crud.list_by_document_id(db, document_id)
        if not versions:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Document has no versions to export.",
            )
        version = _pick_version(versions, version_id)
        markup = editor_html(version.ast_json)
        if markup.strip():
            data = html_to_docx(markup)
        elif version.file_path and Path(version.file_path).is_file():
            data = Path(version.file_path).read_bytes()
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Document has no editable content to export yet.",
            )
        filename = _safe_filename(document.title) + ".docx"
        return data, filename


def _document_detail(db, document_id: str) -> DocumentDetailResponse:
    document = document_crud.get(db, document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document was not found.",
        )
    versions = document_version_crud.list_by_document_id(db, document_id)
    payload = [_version_response(version) for version in versions]
    latest = payload[-1] if payload else None
    return DocumentDetailResponse(
        document_id=document.id,
        title=document.title,
        status=document.status,
        document_type=document.document_type,
        html=latest.html if latest else None,
        active_version_id=latest.id if latest else None,
        versions=payload,
    )


def _version_response(version: DocumentVersion) -> DocumentVersionResponse:
    return DocumentVersionResponse.model_validate(version).model_copy(
        update={"html": editor_html(version.ast_json)}
    )


def _pick_version(
    versions: list[DocumentVersion], version_id: str | None
) -> DocumentVersion:
    if version_id is None:
        return versions[-1]
    for version in versions:
        if str(version.id) == str(version_id):
            return version
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Document version was not found.",
    )


def _safe_filename(title: str) -> str:
    cleaned = _UNSAFE_FILENAME.sub("-", (title or "contract").strip())[:80]
    return cleaned.strip("-") or "contract"
