from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    anthropic_api_key: str = Field(..., env="ANTHROPIC_API_KEY")
    model_name: str = "claude-sonnet-4-20250514"
    max_tokens: int = 1024
    temperature: float = 0.0

    embedding_model: str = "multi-qa-MiniLM-L6-cos-v1"

    chroma_persist_dir: str = "./chroma_db"
    collection_name: str = "rag_documents"

    chunk_size: int = 512
    chunk_overlap: int = 50

    top_k: int = 5

    log_level: str = "INFO"

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "protected_namespaces": ("settings_",),
    }


settings = Settings()
