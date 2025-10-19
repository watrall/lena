from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    embed_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333
    qdrant_collection: str = "lena_pilot"
    data_dir: Path = Field(default=PROJECT_ROOT / "data")

    class Config:
        env_file = ".env"
        env_prefix = "LENA_"


settings = Settings()
