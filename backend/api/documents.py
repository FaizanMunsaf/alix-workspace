from fastapi import APIRouter, File, Form, UploadFile

from api.services.documents import upload_document

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload")
async def upload(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
):
    data = await file.read()
    return upload_document(
        filename=file.filename or "untitled.txt",
        data=data,
        content_type=file.content_type,
        title=title,
    )
