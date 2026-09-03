from typing import List

from langchain_core.documents import Document
from langchain_postgres import PGVector
from langchain_postgres.vectorstores import DistanceStrategy
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy.engine import Engine

from core.database import sync_engine
from ds.rag.embeddings import EmbeddingModel, get_embedding_model

from .base import ClientInitializer, DataStore, DeleteIndex

_DISTANCE_STRATEGIES = {
    "cosine": DistanceStrategy.COSINE,
    "euclidean": DistanceStrategy.EUCLIDEAN,
    "l2": DistanceStrategy.EUCLIDEAN,
    "inner_product": DistanceStrategy.MAX_INNER_PRODUCT,
    "ip": DistanceStrategy.MAX_INNER_PRODUCT,
}


class PgVectorClient(ClientInitializer, DataStore, DeleteIndex):
    def __init__(
        self,
        embedding: EmbeddingModel | None = None,
        collection_name: str = "rag_vectors",
        metric: str = "cosine",
        connection: Engine | str | None = None,
    ):
        self.embedding = embedding or get_embedding_model()
        self.collection_name = collection_name
        self.metric = metric
        self.connection = connection or sync_engine
        self.vector_store: PGVector | None = None

    def initialize(self) -> PGVector:
        self.vector_store = PGVector(
            embeddings=self.embedding.get_embedding_client(),
            connection=self.connection,
            collection_name=self.collection_name,
            embedding_length=self.embedding.dimension,
            distance_strategy=_DISTANCE_STRATEGIES.get(
                self.metric.lower(), DistanceStrategy.COSINE
            ),
            create_extension=False,
            use_jsonb=True,
        )
        return self.vector_store

    def store(self, documents: List[Document]) -> None:
        store = self._ensure_initialized()
        ids = [
            str(doc.metadata["id"])
            for doc in documents
            if doc.metadata.get("id") is not None
        ]
        if len(ids) == len(documents):
            store.add_documents(documents, ids=ids)
        else:
            store.add_documents(documents)

    def search(self, query: str, top_k: int = 5, filter: dict = None) -> List[Document]:
        store = self._ensure_initialized()
        return store.similarity_search(query, k=top_k, filter=filter)

    def ingest_text(
        self, text: str, metadata: dict, chunk_size: int, chunk_overlap: int
    ) -> list[Document]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        documents = splitter.create_documents([text], metadatas=[metadata or {}])
        self.store(documents)
        return documents

    def delete(self, ids: List[str]) -> None:
        store = self._ensure_initialized()
        store.delete(ids=ids)

    def _ensure_initialized(self) -> PGVector:
        if self.vector_store is None:
            return self.initialize()
        return self.vector_store
