# RAG Data Platform: Customer Review Intelligence

<p align="center">
  <img src="https://img.shields.io/badge/Claude-Anthropic-412991?style=flat-square&logo=anthropic&logoColor=white"/>
  <img src="https://img.shields.io/badge/ChromaDB-FF6B35?style=flat-square&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white"/>
  <img src="https://img.shields.io/badge/sentence--transformers-FFD21E?style=flat-square&logo=huggingface&logoColor=black"/>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white"/>
</p>

> Retrieval-augmented Q&A over documents — semantic search via
> **ChromaDB + sentence-transformers**, grounded answers from
> **Claude**, and optional **LLM-as-judge** evaluation.
> Business users query customer sentiment in plain English —
> no SQL required.

---

## Why This Exists

Traditional keyword search over customer reviews breaks down
at scale — it can't handle synonyms, intent, or nuance.

This platform replaces keyword search with **semantic retrieval**:
embed documents once, query with natural language, get grounded
answers with source citations. No database expertise needed.

---

## What It Does

| Capability | Detail |
|---|---|
| **Ingest** | `.txt`, `.md`, `.pdf` from a directory or raw text via API / UI |
| **Embed** | `sentence-transformers` (`all-MiniLM-L6-v2`) chunked at 512 tokens |
| **Retrieve** | Semantic search over ChromaDB with relevance threshold |
| **Generate** | Claude (`claude-sonnet-4-20250514`) produces grounded answers with source chips |
| **Evaluate** | Optional LLM-as-judge: faithfulness, answer relevance, retrieval precision |
| **Persist** | Chroma stores vectors on disk under `./chroma_db` |

---

## Architecture

```
User Query (natural language)
        │
        ▼
┌───────────────────────────────────────┐
│         Streamlit UI (app.py)         │
│  Chat interface · Source chips        │
│  Token usage display                  │
└───────────────┬───────────────────────┘
                │  HTTP
                ▼
┌───────────────────────────────────────┐
│       FastAPI Backend (src/api/)      │
│                                       │
│  ┌─────────────────────────────────┐  │
│  │        pipeline.py              │  │
│  │                                 │  │
│  │  1. INGEST                      │  │
│  │     Loaders → Chunking          │  │
│  │     → Embeddings → ChromaDB     │  │
│  │                                 │  │
│  │  2. RETRIEVE                    │  │
│  │     Query embedding             │  │
│  │     → Semantic search           │  │
│  │     → Relevance threshold       │  │
│  │                                 │  │
│  │  3. GENERATE                    │  │
│  │     Retrieved chunks + query    │  │
│  │     → Claude RAG prompt         │  │
│  │     → Grounded answer           │  │
│  │                                 │  │
│  │  4. EVALUATE (optional)         │  │
│  │     LLM-as-judge scoring        │  │
│  │     Faithfulness · Relevance    │  │
│  │     Retrieval precision         │  │
│  └─────────────────────────────────┘  │
│                                       │
│  ┌─────────────────────────────────┐  │
│  │   ChromaDB (./chroma_db)        │  │
│  │   Persistent vector store       │  │
│  └─────────────────────────────────┘  │
└───────────────────────────────────────┘
        │
        ▼
  Grounded answer + sources + token usage
```

---

## Stack

| Layer | Technology |
|---|---|
| Embeddings | `sentence-transformers` (`all-MiniLM-L6-v2`) |
| Vector Store | ChromaDB (persistent, on-disk) |
| LLM | Claude (`claude-sonnet-4-20250514`) via Anthropic API |
| API | FastAPI + Uvicorn |
| UI | Streamlit |
| Config | Pydantic Settings (`.env`) |
| Testing | pytest |
| Language | Python 3.10+ |

---

## Quick Start

### Prerequisites
- Python 3.10+
- Anthropic API key → [console.anthropic.com](https://console.anthropic.com)

### Setup

```bash
git clone https://github.com/pulipakav1/rag_data.git
cd rag_data

python -m venv venv
source venv/bin/activate        # macOS/Linux
# .\venv\Scripts\Activate.ps1  # Windows

pip install -r requirements.txt

cp .env.example .env
# Set ANTHROPIC_API_KEY in .env
```

### Run

**Step 1 — Start the API** (from project root):

```bash
python -m uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
```

Wait for `Application startup complete` — first startup loads
the embedding model and Chroma (30–60 seconds).

**Step 2 — Start the UI** (optional):

```bash
streamlit run app.py
```

Open **http://localhost:8501**

API docs at **http://localhost:8000/docs**

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Liveness + pipeline status |
| `GET` | `/stats` | Chunk count, model names, config |
| `POST` | `/query` | `{"question": "...", "top_k": 5, "evaluate": false}` |
| `POST` | `/ingest/text` | `{"text": "...", "source_name": "optional"}` |
| `POST` | `/ingest/directory` | `{"dir_path": "/path/to/docs"}` |
| `POST` | `/eval/batch` | Array of `{"question", "answer", "context"}` |

### Example query

```bash
POST /query
{
  "question": "What do customers complain about most?",
  "top_k": 5,
  "evaluate": true
}
```

### Ingest a folder

```bash
POST /ingest/directory
{
  "dir_path": "/path/to/reviews"
}
```

---

## Configuration

| Variable | Purpose | Default |
|---|---|---|
| `ANTHROPIC_API_KEY` | Required for Claude | — |
| `MODEL_NAME` | Anthropic model ID | `claude-sonnet-4-20250514` |
| `CHROMA_PERSIST_DIR` | Vector store path | `./chroma_db` |
| `COLLECTION_NAME` | Chroma collection name | `rag_documents` |
| `EMBEDDING_MODEL` | Sentence-transformers model | `all-MiniLM-L6-v2` |
| `CHUNK_SIZE` | Token chunk size | `512` |
| `CHUNK_OVERLAP` | Chunk overlap | `50` |
| `TOP_K` | Retrieved chunks per query | `5` |
| `MAX_TOKENS` | Claude max output tokens | `1024` |
| `TEMPERATURE` | Claude temperature | `0.0` |
| `RAG_API_BASE` | API URL for Streamlit | `http://127.0.0.1:8000` |

---

## Project Structure

```
rag_pipeline/
├── app.py                    # Streamlit chat UI
├── requirements.txt
├── .env.example
├── config/
│   └── settings.py           # Pydantic settings
├── src/
│   ├── api/
│   │   └── main.py           # FastAPI app + routes
│   ├── pipeline.py           # Ingest → retrieve → generate → eval
│   ├── ingestion/            # Loaders, chunking, vector store
│   ├── retrieval/            # Retriever + relevance threshold
│   ├── generation/           # Claude RAG prompts
│   └── evaluation/           # LLM-as-judge eval prompts
└── tests/
```

---

## Evaluation (LLM-as-Judge)

Set `"evaluate": true` in `/query` to get per-response scores:

- **Faithfulness** — does the answer stay grounded in retrieved chunks?
- **Answer Relevance** — does the answer address the question?
- **Retrieval Precision** — are the retrieved chunks actually useful?

Scores are generated by Claude evaluating its own output against
the retrieved context — no labeled data required.

---

## Tests

```bash
pytest tests/ -q
```

---

## Notes

- **PDF support** — text-based PDFs work out of the box.
  Scanned PDFs need OCR preprocessing first.
- **Reset vector store** — stop the API, delete `./chroma_db`,
  restart and re-ingest.
- **Swap the LLM** — generation is isolated in `src/generation/`.
  Replace Claude with any OpenAI-compatible API by updating
  the prompt module only.

---

## License

MIT — use and modify freely.

---

