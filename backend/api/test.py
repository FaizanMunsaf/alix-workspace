from fastapi import APIRouter

router = APIRouter(prefix="/test", tags=["Test"])

@router.get("/")
def read_root():
    return {"message": "Hello from FastAPI!"}
