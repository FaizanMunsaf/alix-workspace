from core.config.settings import settings

from .base import EmbeddingModel
from .gemini import GeminiEmbedding

__all__ = ["EmbeddingModel", "GeminiEmbedding", "get_embedding_model"]


def get_embedding_model() -> EmbeddingModel:
    name = settings.CURRENT_EMBEDDING.lower()
    if name == "gemini":
        return GeminiEmbedding()
    raise ValueError(f"Unsupported embedding '{settings.CURRENT_EMBEDDING}'.")
