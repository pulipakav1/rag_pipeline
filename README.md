# RAG Pipeline

Retrieval-augmented Q&A over your documents: **ChromaDB** + **sentence-transformers** embeddings, **Claude** for answers, optional **LLM-as-judge** evaluation. Includes a **FastAPI** backend and a **Streamlit** chat UI.

## Features

- **Ingest**: `.txt`, `.md`, `.pdf` from a directory, or raw text via API / UI
- **Query**: semantic search, grounded answers with source chips and token usage
- **Optional eval**: faithfulness, answer relevance, retrieval precision (extra Claude calls)
- **Persistence**: Chroma stores vectors under `./chroma_db` (configurable)

## Project layout

```
rag_pipeline/
├── app.py                 # Streamlit frontend
├── config/settings.py     # Pydantic settings (.env)
├── src/
│   ├── api/main.py        # FastAPI app
│   ├── pipeline.py        # Orchestrates ingest → retrieve → generate → eval
│   ├── ingestion/         # Loaders, chunking, vector store
│   ├── retrieval/         # Retriever + relevance threshold
│   ├── generation/        # Claude RAG prompts
│   └── evaluation/        # RAG evaluator (judge prompts)
├── tests/
├── requirements.txt
└── .env                   # Create from .env.example (not committed secrets)
```

## Prerequisites

- Python 3.10+ recommended  
- [Anthropic API key](https://console.anthropic.com/)

## Setup

```powershell
cd path\to\rag_pipeline
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install streamlit requests
```

Copy `.env.example` to `.env` and set **`ANTHROPIC_API_KEY`**. Other variables are optional (see [Configuration](#configuration)).

## Configuration

| Variable | Purpose | Default (in code) |
|----------|---------|-------------------|
| `ANTHROPIC_API_KEY` | Required for Claude | — |
| `MODEL_NAME` | Anthropic model id | `claude-sonnet-4-20250514` |
| `CHROMA_PERSIST_DIR` | Chroma on-disk path | `./chroma_db` |
| `COLLECTION_NAME` | Chroma collection | `rag_documents` |
| `EMBEDDING_MODEL` | Sentence-transformers model | `all-MiniLM-L6-v2` |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | Text chunking | `512` / `50` |
| `TOP_K` | Default retrieval count | `5` |
| `MAX_TOKENS` / `TEMPERATURE` | Generation | `1024` / `0.0` |

Streamlit talks to the API URL from **`RAG_API_BASE`** (default `http://127.0.0.1:8000`). Set this if the API runs on another host/port.

## Run

### 1. API (required)

From the **project root** (folder that contains `src/` and `app.py`):

```powershell
.\venv\Scripts\Activate.ps1
python -m uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
```

First startup loads the embedding model and Chroma; it can take **30–60+ seconds**. Wait for `Application startup complete`.

**Windows / port errors:** If binding fails with `WinError 10013` on port `8000`, use another port (e.g. `8765`) and point the UI at it:

```powershell
python -m uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8765
```

### 2. Streamlit UI (optional)

```powershell
$env:RAG_API_BASE = "http://127.0.0.1:8765"   # only if API is not on 8000
streamlit run app.py
```

Open the URL shown in the terminal (usually `http://localhost:8501`).

### Health check

- API: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) (adjust host/port if needed)

## API reference

Base URL: `http://127.0.0.1:8000` (or your chosen port).

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness + pipeline initialized |
| `GET` | `/stats` | Chunk count, model names, etc. |
| `POST` | `/query` | Body: `{"question": "...", "top_k": 5, "evaluate": false}` |
| `POST` | `/ingest/text` | Body: `{"text": "...", "source_name": "optional"}` |
| `POST` | `/ingest/directory` | Body: `{"dir_path": "C:\\path\\to\\docs"}` |
| `POST` | `/eval/batch` | JSON array of `{"question","answer","context"}` |

Interactive docs: `/docs` (Swagger UI).

### Re-ingest a folder (PowerShell example)

```powershell
$dir = "C:\path\to\folder\with\pdfs"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/ingest/directory" -Method Post -ContentType "application/json" -Body (@{ dir_path = $dir } | ConvertTo-Json)
```

To **fully reset** the vector store, stop the API, delete the `chroma_db` directory (or your `CHROMA_PERSIST_DIR`), restart the API, and ingest again.

## Tests

```powershell
pytest tests\ -q
```

## PDF notes

- Text-based PDFs work best; **scanned** PDFs need OCR elsewhere first.
- After changing ingestion logic, **re-ingest** so Chroma reflects new chunks.

