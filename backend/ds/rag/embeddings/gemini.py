from typing import Any

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from core.config.settings import settings

from .base import EmbeddingModel


class GeminiEmbedding(EmbeddingModel):
    def __init__(
        self,
        model_name: str | None = None,
        api_key: str | None = None,
        dimension: int | None = None,
    ):
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self.api_key = api_key or settings.GEMINI_API_KEY or None
        self._dimension = dimension or settings.EMBEDDING_DIMENSION
        self._client: GoogleGenerativeAIEmbeddings | None = None

    @property
    def dimension(self) -> int:
        return self._dimension

    def get_embedding_client(self) -> GoogleGenerativeAIEmbeddings:
        if self._client is None:
            kwargs: dict[str, Any] = {
                "model": self.model_name,
                "output_dimensionality": self._dimension,
            }
            if self.api_key:
                kwargs["google_api_key"] = self.api_key
            self._client = GoogleGenerativeAIEmbeddings(**kwargs)
        return self._client

    def embed_query(self, text: str) -> list[float]:
        return self.get_embedding_client().embed_query(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.get_embedding_client().embed_documents(texts)
