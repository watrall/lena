from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    embed_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333
    qdrant_collection: str = "lena_pilot"
    qdrant_location: Optional[str] = None
    data_dir: Path = Field(default=PROJECT_ROOT / "data")
    storage_dir: Path = Field(default=PROJECT_ROOT / "storage")
    llm_mode: str = Field(default="hf", pattern="^(hf|off)$")
    hf_model: str = "HuggingFaceH4/zephyr-7b-beta"
    hf_max_new_tokens: int = 256
    retrieval_top_k: int = 6
    embedding_batch_size: int = 16

    class Config:
        env_file = ".env"
        env_prefix = "LENA_"
        extra = "ignore"


settings = Settings()
