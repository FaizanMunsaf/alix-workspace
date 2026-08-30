from fastapi import APIRouter
from api.services.health_test import health_check

router = APIRouter(prefix="/test", tags=["Test"])


@router.get("/")
def read_root():
    return health_check()
