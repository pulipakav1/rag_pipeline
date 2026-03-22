from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from loguru import logger

from src.ingestion.loader import DocumentLoader, TextChunker
from src.ingestion.vector_store import VectorStore
from src.retrieval.retriever import Retriever
from src.generation.generator import Generator
from src.evaluation.evaluator import RAGEvaluator, EvaluationResult
from config.settings import settings


@dataclass
class RAGResponse:
    question: str
    answer: str
    sources: list[dict]
    context: str
    tokens_used: dict


class RAGPipeline:
    def __init__(self):
        self.vector_store = VectorStore()
        self.retriever = Retriever(vector_store=self.vector_store)
        self.generator = Generator()
        self.evaluator = RAGEvaluator()
        self.loader = DocumentLoader()
        self.chunker = TextChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        logger.info("RAG Pipeline initialized")

    def ingest_directory(self, dir_path: str) -> int:
        path = Path(dir_path)
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")

        raw_docs = self.loader.load_directory(path)
        if not raw_docs:
            logger.warning(f"No supported documents found in {dir_path}")
            return 0

        all_chunks = []
        for file_path, content in raw_docs:
            metadata = {
                "source": file_path.name,
                "file_path": str(file_path),
                "file_type": file_path.suffix,
            }
            chunks = self.chunker.chunk_text(text=content, metadata=metadata)
            all_chunks.extend(chunks)

        count = self.vector_store.upsert(all_chunks)
        logger.info(f"Ingested {len(raw_docs)} documents → {count} chunks stored")
        return count

    def ingest_text(self, text: str, source_name: str = "manual_input") -> int:
        metadata = {"source": source_name, "file_type": "text"}
        chunks = self.chunker.chunk_text(text=text, metadata=metadata)
        return self.vector_store.upsert(chunks)

    def query(self, question: str, top_k: Optional[int] = None) -> RAGResponse:
        chunks = self.retriever.retrieve(query=question, top_k=top_k)

        if not chunks:
            return RAGResponse(
                question=question,
                answer="I could not find relevant information in the knowledge base to answer your question.",
                sources=[],
                context="",
                tokens_used={"input": 0, "output": 0},
            )

        context = self.retriever.chunks_as_context(chunks)
        generation = self.generator.generate(question=question, context=context)

        sources = [
            {
                "source": chunk.metadata.get("source", "Unknown"),
                "relevance_score": round(chunk.relevance_score, 3),
                "rank": chunk.rank,
            }
            for chunk in chunks
        ]

        return RAGResponse(
            question=question,
            answer=generation.answer,
            sources=sources,
            context=context,
            tokens_used={
                "input": generation.input_tokens,
                "output": generation.output_tokens,
            },
        )

    def query_with_eval(self, question: str) -> tuple[RAGResponse, EvaluationResult]:
        response = self.query(question)
        evaluation = self.evaluator.evaluate(
            question=question,
            answer=response.answer,
            context=response.context,
        )
        return response, evaluation

    def get_stats(self) -> dict:
        return {
            "total_chunks": self.vector_store.count(),
            "collection_name": self.vector_store.collection_name,
            "embedding_model": settings.embedding_model,
            "llm_model": settings.model_name,
            "top_k": settings.top_k,
        }
