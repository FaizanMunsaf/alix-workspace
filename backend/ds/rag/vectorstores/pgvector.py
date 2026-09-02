from typing import List

from langchain_core.documents import Document
from langchain_postgres import PGEngine, PGVectorStore
from langchain_postgres.v2.indexes import DistanceStrategy
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import inspect

from core.config.settings import settings
from core.database import sync_engine
from ds.rag.embeddings import EmbeddingModel, get_embedding_model

from .base import ClientInitializer, DataStore, DeleteIndex

_DISTANCE_STRATEGIES = {
    "cosine": DistanceStrategy.COSINE_DISTANCE,
    "euclidean": DistanceStrategy.EUCLIDEAN,
    "l2": DistanceStrategy.EUCLIDEAN,
    "inner_product": DistanceStrategy.INNER_PRODUCT,
    "ip": DistanceStrategy.INNER_PRODUCT,
}


class PgVectorClient(ClientInitializer, DataStore, DeleteIndex):
    def __init__(
        self,
        embedding: EmbeddingModel | None = None,
        table_name: str = "rag_vectors",
        schema_name: str = "public",
        metric: str = "cosine",
        connection_string: str | None = None,
    ):
        self.embedding = embedding or get_embedding_model()
        self.table_name = table_name
        self.schema_name = schema_name
        self.metric = metric
        self.connection_string = connection_string or settings.PSYCOPG_DATABASE_URL
        self.pg_engine: PGEngine | None = None
        self.vector_store: PGVectorStore | None = None

    def initialize(self) -> PGVectorStore:
        embeddings = self.embedding.get_embedding_client()
        distance_strategy = _DISTANCE_STRATEGIES.get(
            self.metric.lower(), DistanceStrategy.COSINE_DISTANCE
        )

        self.pg_engine = PGEngine.from_connection_string(url=self.connection_string)
        if not self._table_exists():
            self.pg_engine.init_vectorstore_table(
                table_name=self.table_name,
                vector_size=self.embedding.dimension,
                schema_name=self.schema_name,
            )

        self.vector_store = PGVectorStore.create_sync(
            engine=self.pg_engine,
            table_name=self.table_name,
            schema_name=self.schema_name,
            embedding_service=embeddings,
            distance_strategy=distance_strategy,
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

    def _ensure_initialized(self) -> PGVectorStore:
        if self.vector_store is None:
            return self.initialize()
        return self.vector_store

    def _table_exists(self) -> bool:
        inspector = inspect(sync_engine)
        return inspector.has_table(self.table_name, schema=self.schema_name)
