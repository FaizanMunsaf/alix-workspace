import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI

from admin.admin import init_admin
from api.documents import router as documents_router
from api.health_test import router as health_router
from api.qa import router as qa_router
from core.config.settings import settings
from core.database import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

init_admin(app)


app.include_router(health_router)
app.include_router(documents_router)
app.include_router(qa_router)
