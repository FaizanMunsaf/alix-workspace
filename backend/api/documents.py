from fastapi import APIRouter, BackgroundTasks, File, Form, UploadFile, status

from api.services.diff import diff_document_versions
from api.services.documents import upload_document
from core.schemas.diff import ASTDiffResponse, DiffRequest

router = APIRouter(prefix="/documents", tags=["Documents"])


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
