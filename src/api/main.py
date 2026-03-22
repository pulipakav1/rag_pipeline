from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from pydantic import BaseModel

from src.pipeline import RAGPipeline


pipeline: RAGPipeline = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pipeline
    logger.info("Initializing RAG Pipeline...")
    pipeline = RAGPipeline()
    logger.info("RAG Pipeline ready")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="Production RAG System",
    description="RAG pipeline with evaluation using Claude + ChromaDB",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str
    top_k: int = 5
    evaluate: bool = False


class IngestTextRequest(BaseModel):
    text: str
    source_name: str = "api_input"


class IngestDirRequest(BaseModel):
    dir_path: str


@app.get("/health")
def health():
    return {"status": "ok", "pipeline_ready": pipeline is not None}


@app.get("/stats")
def stats():
    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    return pipeline.get_stats()


@app.post("/query")
def query(request: QueryRequest):
    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")

    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        if request.evaluate:
            response, evaluation = pipeline.query_with_eval(request.question)
            return {
                "question": response.question,
                "answer": response.answer,
                "sources": response.sources,
                "tokens_used": response.tokens_used,
                "evaluation": evaluation.to_dict()["metrics"],
                "overall_score": evaluation.overall_score,
            }
        else:
            response = pipeline.query(question=request.question, top_k=request.top_k)
            return {
                "question": response.question,
                "answer": response.answer,
                "sources": response.sources,
                "tokens_used": response.tokens_used,
            }
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/text")
def ingest_text(request: IngestTextRequest):
    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")

    count = pipeline.ingest_text(text=request.text, source_name=request.source_name)
    return {"chunks_added": count, "source": request.source_name}


@app.post("/ingest/directory")
def ingest_directory(request: IngestDirRequest):
    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")

    try:
        count = pipeline.ingest_directory(request.dir_path)
        return {"chunks_added": count, "dir_path": request.dir_path}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/eval/batch")
def eval_batch(test_cases: list[dict]):
    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")

    if not test_cases:
        raise HTTPException(status_code=400, detail="No test cases provided")

    summary = pipeline.evaluator.evaluate_batch(test_cases)
    return summary.to_dict()
