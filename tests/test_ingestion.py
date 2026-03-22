import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingestion.loader import Document, DocumentLoader, TextChunker


class TestDocument:
    def test_doc_id_auto_generated(self):
        doc = Document(content="Hello world")
        assert doc.doc_id != ""
        assert len(doc.doc_id) == 32

    def test_same_content_same_id(self):
        doc1 = Document(content="Same content")
        doc2 = Document(content="Same content")
        assert doc1.doc_id == doc2.doc_id

    def test_different_content_different_id(self):
        doc1 = Document(content="Content A")
        doc2 = Document(content="Content B")
        assert doc1.doc_id != doc2.doc_id

    def test_custom_doc_id(self):
        doc = Document(content="Hello", doc_id="custom-id-123")
        assert doc.doc_id == "custom-id-123"




class TestDocumentLoader:
    def test_load_txt_file(self, tmp_path):
        file = tmp_path / "test.txt"
        file.write_text("This is test content.")
        loader = DocumentLoader()
        content = loader.load_file(file)
        assert content == "This is test content."

    def test_load_md_file(self, tmp_path):
        file = tmp_path / "test.md"
        file.write_text("# Header\nSome markdown content.")
        loader = DocumentLoader()
        content = loader.load_file(file)
        assert "Header" in content

    def test_unsupported_extension_raises(self, tmp_path):
        file = tmp_path / "test.csv"
        file.write_text("col1,col2")
        loader = DocumentLoader()
        with pytest.raises(ValueError, match="Unsupported file type"):
            loader.load_file(file)

    def test_load_directory(self, tmp_path):
        (tmp_path / "doc1.txt").write_text("Document one content.")
        (tmp_path / "doc2.md").write_text("Document two content.")
        (tmp_path / "skip.csv").write_text("should,be,skipped")

        loader = DocumentLoader()
        docs = loader.load_directory(tmp_path)
        assert len(docs) == 2

    def test_load_directory_empty(self, tmp_path):
        loader = DocumentLoader()
        docs = loader.load_directory(tmp_path)
        assert docs == []


class TestTextChunker:
    def test_short_text_single_chunk(self):
        chunker = TextChunker(chunk_size=1000, chunk_overlap=50)
        text = "This is a short sentence."
        chunks = chunker.chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0].content.strip() != ""

    def test_long_text_multiple_chunks(self):
        chunker = TextChunker(chunk_size=100, chunk_overlap=20)
        text = " ".join(["This is sentence number {}.".format(i) for i in range(50)])
        chunks = chunker.chunk_text(text)
        assert len(chunks) > 1

    def test_metadata_passed_to_chunks(self):
        chunker = TextChunker(chunk_size=1000)
        metadata = {"source": "test.txt", "file_type": ".txt"}
        chunks = chunker.chunk_text("Some text content here.", metadata=metadata)
        for chunk in chunks:
            assert chunk.metadata["source"] == "test.txt"

    def test_metadata_not_shared_between_chunks(self):
        chunker = TextChunker(chunk_size=50, chunk_overlap=10)
        text = " ".join(["Sentence {}.".format(i) for i in range(20)])
        chunks = chunker.chunk_text(text, metadata={"source": "test"})
        chunks[0].metadata["source"] = "modified"
        assert chunks[1].metadata["source"] == "test"

    def test_empty_text_returns_empty(self):
        chunker = TextChunker()
        chunks = chunker.chunk_text("   ")
        assert chunks == []

    def test_chunk_size_respected(self):
        chunker = TextChunker(chunk_size=100, chunk_overlap=0)
        text = " ".join(["Word"] * 500)
        chunks = chunker.chunk_text(text)
        for chunk in chunks:
            assert len(chunk.content) <= 200
