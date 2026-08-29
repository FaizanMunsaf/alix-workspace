from fastapi import FastAPI
from sqladmin import Admin


from backend.services.admin_auth import AdminAuth
from backend.core.database import engine


def init_admin(app: FastAPI) -> None:
    from backend.core.config.settings import settings

    # admin = Admin(
    #     app,
    #     engine,
    #     templates_dir="backend/admin/static",
    #     authentication_backend=AdminAuth(
    #         secret_key=settings.SECRET_KEY,
    #         username=settings.ADMIN_USERNAME,
    #         password=settings.ADMIN_PASSWORD,
    #     ),
    # )
