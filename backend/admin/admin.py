from fastapi import FastAPI
from sqladmin import Admin

from admin.clause_embeddings import ClauseEmbeddingAdmin
from admin.document import DocumentAdmin
from admin.document_ast_node import DocumentASTNodeAdmin
from admin.document_version import DocumentVersionAdmin
from api.services.admin_auth import AdminAuth
from core.config.settings import settings
from core.database import engine


def init_admin(app: FastAPI) -> None:
    admin = Admin(
        app,
        engine,
        title=settings.APP_NAME,
        authentication_backend=AdminAuth(
            secret_key=settings.SECRET_KEY,
            username=settings.ADMIN_USERNAME,
            password=settings.ADMIN_PASSWORD,
        ),
    )
    admin.add_view(DocumentAdmin)
    admin.add_view(DocumentVersionAdmin)
    admin.add_view(DocumentASTNodeAdmin)
    admin.add_view(ClauseEmbeddingAdmin)
