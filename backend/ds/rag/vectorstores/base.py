from abc import ABC, abstractmethod
from typing import Any, List
from langchain_core.documents import Document


class ClientInitializer(ABC):
    """
    Abstract class for initializing any external service client
    such as OpenAI, Azure, Pinecone, etc.
    """

    @abstractmethod
    def initialize(self) -> Any:
        pass


class DataStore(ABC):
    """
    Abstract class for storing and retrieving documents
    with embedding-based vector databases.
    """

    @abstractmethod
    def store(self, documents: List[Document]) -> None:
        pass

    @abstractmethod
    def search(self, query: str, top_k: int = 5, filter: dict = None) -> List[Document]:
        pass

    @abstractmethod
    def ingest_text(
        self, text: str, metadata: dict, chunk_size: int, chunk_overlap: int
    ) -> list[Document]:
        pass


class InformationExtractor(ABC):
    """
    Abstract class for extracting and chunking documents from raw input.
    Handles splitting based on chunk size and overlap.
    """

    @abstractmethod
    def extract(
        self, raw_input: Any, chunk_size: int = 500, chunk_overlap: int = 50
    ) -> List[Document]:
        pass


class DeleteIndex(ABC):
    """
    Abstract base class for deleting vectors from a vector store.

    Subclasses must implement the `delete` method to define how vectors
    identified by their IDs should be removed from the underlying store.
    """

    @abstractmethod
    def delete(self, ids: List[str]) -> None:
        pass
