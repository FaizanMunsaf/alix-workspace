from fastapi import APIRouter, Query

from api.services import knowledge as knowledge_service
from core.schemas.knowledge import KnowledgeSourceResponse

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


@router.get("/", response_model=list[KnowledgeSourceResponse])
def list_sources(ensure_seed: bool = Query(default=True)):
    return knowledge_service.list_knowledge_sources(ensure_seed=ensure_seed)


@router.post("/seed")
def seed_sources(force: bool = Query(default=False)):
    return knowledge_service.seed_knowledge(force=force)
