import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingestion.loader import Document
from src.ingestion.vector_store import VectorStore
from src.retrieval.retriever import Retriever


@pytest.fixture
def tmp_vector_store(tmp_path):
    store = VectorStore(
        persist_dir=str(tmp_path / "chroma_test"),
        collection_name="test_collection",
    )
    yield store
    store.delete_collection()


@pytest.fixture
def sample_documents():
    return [
        Document(
            content="Python is a high-level programming language known for its simplicity.",
            metadata={"source": "python_docs.txt"},
        ),
        Document(
            content="Machine learning is a subset of artificial intelligence that learns from data.",
            metadata={"source": "ml_intro.txt"},
        ),
        Document(
            content="FastAPI is a modern Python web framework for building APIs quickly.",
            metadata={"source": "fastapi_docs.txt"},
        ),
        Document(
            content="ChromaDB is an open-source vector database for storing embeddings.",
            metadata={"source": "chromadb_docs.txt"},
        ),
        Document(
            content="RAG stands for Retrieval-Augmented Generation, combining search and LLMs.",
            metadata={"source": "rag_overview.txt"},
        ),
    ]


class TestVectorStore:
    def test_upsert_and_count(self, tmp_vector_store, sample_documents):
        count = tmp_vector_store.upsert(sample_documents)
        assert count == len(sample_documents)
        assert tmp_vector_store.count() == len(sample_documents)

    def test_query_returns_results(self, tmp_vector_store, sample_documents):
        tmp_vector_store.upsert(sample_documents)
        results = tmp_vector_store.query("What is Python?", top_k=3)
        assert len(results) > 0
        assert "content" in results[0]
        assert "relevance_score" in results[0]

    def test_query_top_k_respected(self, tmp_vector_store, sample_documents):
        tmp_vector_store.upsert(sample_documents)
        results = tmp_vector_store.query("programming", top_k=2)
        assert len(results) <= 2

    def test_relevance_scores_between_0_and_1(self, tmp_vector_store, sample_documents):
        tmp_vector_store.upsert(sample_documents)
        results = tmp_vector_store.query("machine learning AI", top_k=5)
        for r in results:
            assert 0.0 <= r["relevance_score"] <= 1.0

    def test_upsert_empty_list(self, tmp_vector_store):
        count = tmp_vector_store.upsert([])
        assert count == 0

    def test_deduplication_on_same_id(self, tmp_vector_store):
        doc = Document(content="Unique content here", doc_id="fixed-id-001")
        tmp_vector_store.upsert([doc])
        tmp_vector_store.upsert([doc])
        assert tmp_vector_store.count() == 1


class TestRetriever:
    def test_retrieve_returns_chunks(self, tmp_vector_store, sample_documents):
        tmp_vector_store.upsert(sample_documents)
        retriever = Retriever(vector_store=tmp_vector_store, top_k=3)
        chunks = retriever.retrieve("What is RAG?")
        assert len(chunks) > 0

    def test_retrieve_filters_low_relevance(self, tmp_vector_store, sample_documents):
        tmp_vector_store.upsert(sample_documents)
        retriever = Retriever(vector_store=tmp_vector_store, top_k=5)
        chunks = retriever.retrieve("xyzzy foobar nonsense 12345")
        for chunk in chunks:
            assert chunk.relevance_score >= retriever.RELEVANCE_THRESHOLD

    def test_retrieve_as_context_format(self, tmp_vector_store, sample_documents):
        tmp_vector_store.upsert(sample_documents)
        retriever = Retriever(vector_store=tmp_vector_store, top_k=3)
        context = retriever.retrieve_as_context("What is Python?")
        assert isinstance(context, str)
        assert len(context) > 0

    def test_retrieve_ranks_assigned(self, tmp_vector_store, sample_documents):
        tmp_vector_store.upsert(sample_documents)
        retriever = Retriever(vector_store=tmp_vector_store, top_k=3)
        chunks = retriever.retrieve("machine learning")
        for i, chunk in enumerate(chunks):
            assert chunk.rank == i + 1
