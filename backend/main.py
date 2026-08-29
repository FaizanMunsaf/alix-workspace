import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.admin.admin import init_admin
from backend.api.healthcheck import router as health_router


from backend.core.config.settings import settings
from core.messaging import broker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await broker.connect()
    yield
    await broker.close()


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

init_admin(app)


app.include_router(health_router)
