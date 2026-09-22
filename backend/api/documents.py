from fastapi import APIRouter, BackgroundTasks, File, Form, Query, UploadFile, status
from fastapi.responses import Response

from api.services.diff import diff_document_versions
from api.services.documents import (
    export_document_docx,
    get_document,
    list_documents,
    read_document_media,
    restore_version,
    save_document_content,
    upload_document,
)
from core.schemas.diff import ASTDiffResponse, DiffRequest
from core.schemas.document import (
    DocumentDetailResponse,
    DocumentListItem,
    SaveDocumentContent,
)
from core.schemas.history import RestoreVersionRequest

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("/", response_model=list[DocumentListItem])
def list_uploaded_documents():
    return list_documents()


@router.get("/{document_id}/export")
def export_document(
    document_id: str,
    version_id: str | None = Query(default=None),
):
    data, filename = export_document_docx(document_id, version_id=version_id)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{document_id}/media/{filename}")
def document_media(document_id: str, filename: str):
    data, content_type = read_document_media(document_id, filename)
    return Response(content=data, media_type=content_type)


@router.put("/{document_id}/content", response_model=DocumentDetailResponse)
def save_content(document_id: str, body: SaveDocumentContent):
    return save_document_content(
        document_id,
        html=body.html,
        version_id=str(body.version_id) if body.version_id else None,
    )


@router.post("/{document_id}/restore", response_model=DocumentDetailResponse)
def restore_document_version(document_id: str, body: RestoreVersionRequest):
    return restore_version(document_id, str(body.version_id))


@router.get("/{document_id}", response_model=DocumentDetailResponse)
def read_document(document_id: str):
    return get_document(document_id)


@router.post("/diff", response_model=ASTDiffResponse)
def diff_versions(body: DiffRequest):
    return diff_document_versions(
        from_version_id=str(body.from_version_id),
        to_version_id=str(body.to_version_id),
    )


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
):
    data = await file.read()
    return upload_document(
        filename=file.filename or "untitled.docx",
        data=data,
        content_type=file.content_type,
        title=title,
        background_tasks=background_tasks,
    )
