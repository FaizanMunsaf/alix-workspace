import logging
import sys
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from admin.admin import init_admin
from api.documents import router as documents_router
from api.edits import router as edits_router
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


api_v1 = APIRouter(prefix="/api/v1")
for router in (health_router, documents_router, edits_router, qa_router):
    api_v1.include_router(router)
app.include_router(api_v1)
