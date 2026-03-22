import hashlib
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from loguru import logger
from pypdf import PdfReader


@dataclass
class Document:
    content: str
    metadata: dict = field(default_factory=dict)
    doc_id: str = ""

    def __post_init__(self):
        if not self.doc_id:
            self.doc_id = hashlib.md5(self.content.encode()).hexdigest()


class DocumentLoader:
    SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}

    def load_file(self, file_path: Path) -> str:
        suffix = file_path.suffix.lower()

        if suffix not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {suffix}")

        if suffix == ".pdf":
            return self._load_pdf(file_path)
        else:
            return file_path.read_text(encoding="utf-8")

    def _load_pdf(self, file_path: Path) -> str:
        reader = PdfReader(str(file_path))
        if getattr(reader, "is_encrypted", False):
            try:
                reader.decrypt("")
            except Exception:
                logger.warning("PDF appears encrypted (password may be required): %s", file_path.name)

        parts: list[str] = []
        for i, page in enumerate(reader.pages, start=1):
            raw = self._extract_pdf_page_text(page)
            raw = (raw or "").strip()
            if raw:
                parts.append(f"--- Page {i} ---\n{raw}")

        text = "\n\n".join(parts)
        text = self._normalize_pdf_text(text)

        n_pages = len(reader.pages)
        if n_pages and len(text.strip()) < max(50, n_pages * 20):
            logger.warning(
                "Very little text extracted from %s (%d pages). "
                "Scanned/image-only PDFs need OCR; multi-column PDFs may still be imperfect.",
                file_path.name,
                n_pages,
            )
        return text.strip()

    @staticmethod
    def _extract_pdf_page_text(page) -> str:
        t = ""
        try:
            t = page.extract_text(extraction_mode="layout") or ""
        except TypeError:
            t = page.extract_text() or ""
        except Exception as e:
            logger.debug("layout extract failed, using plain: %s", e)
            try:
                t = page.extract_text() or ""
            except Exception:
                t = ""
        if not str(t).strip():
            try:
                t = page.extract_text() or ""
            except Exception:
                t = ""
        return str(t)

    @staticmethod
    def _normalize_pdf_text(text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"-\s*\n\s*", "", text)
        text = re.sub(r"[\u00ad\u200b\u200c\u200d\ufeff]", "", text)
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n[ \t]+", "\n", text)
        return text

    def load_directory(self, dir_path: Path) -> list[tuple[Path, str]]:
        documents = []
        for file_path in dir_path.rglob("*"):
            if file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                try:
                    content = self.load_file(file_path)
                    if content.strip():
                        documents.append((file_path, content))
                        logger.info(f"Loaded: {file_path.name}")
                except Exception as e:
                    logger.warning(f"Failed to load {file_path.name}: {e}")
        return documents


class TextChunker:
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str, metadata: Optional[dict] = None) -> list[Document]:
        metadata = metadata or {}
        text = self._clean_text(text)
        sentences = self._split_into_sentences(text)
        sentences = self._burst_oversized_segments(sentences)

        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            if current_length + sentence_length > self.chunk_size and current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append(Document(content=chunk_text, metadata=metadata.copy()))

                overlap_sentences = []
                overlap_length = 0
                for s in reversed(current_chunk):
                    if overlap_length + len(s) <= self.chunk_overlap:
                        overlap_sentences.insert(0, s)
                        overlap_length += len(s)
                    else:
                        break

                current_chunk = overlap_sentences
                current_length = overlap_length

            current_chunk.append(sentence)
            current_length += sentence_length

        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(Document(content=chunk_text, metadata=metadata.copy()))

        logger.debug(f"Split text into {len(chunks)} chunks")
        return chunks

    _PARA_MARK = "\uffffPARA\uffff"

    def _clean_text(self, text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"\n\s*\n+", self._PARA_MARK, text)
        text = re.sub(r"\s*\n\s*", " ", text)
        text = re.sub(r" +", " ", text)
        text = text.replace(self._PARA_MARK, "\n\n")
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _split_into_sentences(self, text: str) -> list[str]:
        sentence_endings = re.compile(r"(?<=[.!?])\s+")
        out: list[str] = []
        for block in re.split(r"\n\s*\n+", text.strip()):
            block = block.strip()
            if not block:
                continue
            pieces = sentence_endings.split(block)
            out.extend(p.strip() for p in pieces if p.strip())
        return out

    def _burst_oversized_segments(self, segments: list[str]) -> list[str]:
        if not segments:
            return []
        result: list[str] = []
        step = max(self.chunk_size - self.chunk_overlap, 1)
        for seg in segments:
            if len(seg) <= self.chunk_size:
                result.append(seg)
                continue
            for i in range(0, len(seg), step):
                result.append(seg[i : i + self.chunk_size])
        return result
