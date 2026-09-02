from core.config.settings import settings

from .base import ClientInitializer, DataStore, DeleteIndex
from .pgvector import PgVectorClient

__all__ = [
    "ClientInitializer",
    "DataStore",
    "DeleteIndex",
    "PgVectorClient",
    "get_vectorstore",
]


def get_vectorstore() -> PgVectorClient:
    name = settings.CURRENT_VECTORSTORE.lower()
    if name == "pgvector":
        return PgVectorClient()
    raise ValueError(f"Unsupported vectorstore '{settings.CURRENT_VECTORSTORE}'.")
