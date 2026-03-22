from dataclasses import dataclass
from typing import Optional

from loguru import logger

from src.ingestion.vector_store import VectorStore
from config.settings import settings


@dataclass
class RetrievedChunk:
    content: str
    metadata: dict
    relevance_score: float
    rank: int


class Retriever:
    RELEVANCE_THRESHOLD = 0.3

    def __init__(self, vector_store: Optional[VectorStore] = None, top_k: Optional[int] = None):
        self.vector_store = vector_store or VectorStore()
        self.top_k = top_k or settings.top_k

    def retrieve(self, query: str, top_k: Optional[int] = None) -> list[RetrievedChunk]:
        top_k = top_k or self.top_k
        raw_results = self.vector_store.query(query_text=query, top_k=top_k)

        chunks = []
        for i, result in enumerate(raw_results):
            if result["relevance_score"] >= self.RELEVANCE_THRESHOLD:
                chunks.append(
                    RetrievedChunk(
                        content=result["content"],
                        metadata=result["metadata"],
                        relevance_score=result["relevance_score"],
                        rank=i + 1,
                    )
                )

        logger.debug(
            f"Retrieved {len(chunks)}/{len(raw_results)} chunks above threshold "
            f"({self.RELEVANCE_THRESHOLD}) for query: '{query[:60]}...'"
        )
        return chunks

    def chunks_as_context(self, chunks: list[RetrievedChunk]) -> str:
        if not chunks:
            return "No relevant context found."
        parts = []
        for chunk in chunks:
            source = chunk.metadata.get("source", "Unknown")
            parts.append(
                f"[Source: {source} | Relevance: {chunk.relevance_score:.2f}]\n{chunk.content}"
            )
        return "\n\n---\n\n".join(parts)

    def retrieve_as_context(self, query: str, top_k: Optional[int] = None) -> str:
        return self.chunks_as_context(self.retrieve(query=query, top_k=top_k))
