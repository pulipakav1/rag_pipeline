from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from loguru import logger

from src.ingestion.loader import Document
from config.settings import settings


class EmbeddingModel:
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.embedding_model
        logger.info(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    def embed_single(self, text: str) -> list[float]:
        return self.embed([text])[0]


class VectorStore:
    def __init__(
        self,
        persist_dir: Optional[str] = None,
        collection_name: Optional[str] = None,
        embedding_model: Optional[EmbeddingModel] = None,
    ):
        self.persist_dir = persist_dir or settings.chroma_persist_dir
        self.collection_name = collection_name or settings.collection_name
        self.embedding_model = embedding_model or EmbeddingModel()

        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            f"ChromaDB initialized | collection: {self.collection_name} "
            f"| documents: {self.collection.count()}"
        )

    def upsert(self, documents: list[Document]) -> int:
        if not documents:
            return 0

        texts = [doc.content for doc in documents]
        ids = [doc.doc_id for doc in documents]
        metadatas = [doc.metadata if doc.metadata else {"source": "unknown"} for doc in documents]

        logger.info(f"Embedding {len(texts)} chunks...")
        embeddings = self.embedding_model.embed(texts)

        self.collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        logger.info(f"Upserted {len(documents)} chunks into ChromaDB")
        return len(documents)

    def query(self, query_text: str, top_k: Optional[int] = None) -> list[dict]:
        top_k = top_k or settings.top_k
        query_embedding = self.embedding_model.embed_single(query_text)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        chunks = []
        for i, doc in enumerate(results["documents"][0]):
            chunks.append({
                "content": doc,
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
                "relevance_score": 1 - results["distances"][0][i],
            })

        return chunks

    def delete_collection(self):
        self.client.delete_collection(self.collection_name)
        logger.warning(f"Deleted collection: {self.collection_name}")

    def count(self) -> int:
        return self.collection.count()
