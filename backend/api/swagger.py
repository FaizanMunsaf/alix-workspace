from fastapi import APIRouter, Depends, Request
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse

from core.config.security import require_docs_auth
from core.config.settings import settings

router = APIRouter(tags=["Swagger"], include_in_schema=False)


@router.get("/docs", response_class=HTMLResponse)
def swagger_docs(_: None = Depends(require_docs_auth)):
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=f"{settings.APP_NAME} · Swagger",
    )


@router.get("/redoc", response_class=HTMLResponse)
def redoc_docs(_: None = Depends(require_docs_auth)):
    return get_redoc_html(
        openapi_url="/openapi.json",
        title=f"{settings.APP_NAME} · ReDoc",
    )


@router.get("/openapi.json")
def openapi_spec(request: Request, _: None = Depends(require_docs_auth)):
    return JSONResponse(request.app.openapi())
