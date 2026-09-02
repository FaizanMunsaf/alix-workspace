from abc import ABC, abstractmethod
from typing import Any


class EmbeddingModel(ABC):
    """
    Abstract class for embedding text or documents.
    Allows plugging in different embedding models (OpenAI, Azure, Cohere, etc.)
    """

    @property
    @abstractmethod
    def dimension(self) -> int:
        pass

    @abstractmethod
    def get_embedding_client(self) -> Any:
        pass

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        pass

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        pass
