"""Application configuration loaded from environment variables.

All settings use the LENA_ prefix and can be overridden via environment
variables or a .env file in the project root.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Application configuration loaded from environment variables.

    Attributes:
        embed_model: Sentence transformer model for embeddings.
        qdrant_host: Hostname of the Qdrant vector store.
        qdrant_port: Port number for Qdrant connection.
        qdrant_collection: Name of the Qdrant collection.
        qdrant_location: Optional path for local Qdrant (e.g., ':memory:').
        data_dir: Directory containing course materials to ingest.
        storage_dir: Directory for persisting feedback and analytics.
        llm_mode: Generation mode ('hf' for Hugging Face, 'off' for extractive).
        hf_model: Hugging Face model identifier for generation.
        hf_max_new_tokens: Maximum tokens to generate per response.
        retrieval_top_k: Number of chunks to retrieve per query.
        embedding_batch_size: Batch size for embedding generation.
        escalation_confidence_threshold: Confidence below which to suggest escalation.
        analytics_history_days: Days of analytics history to retain.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="LENA_",
        extra="ignore",
    )

    # Embedding configuration
    embed_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Qdrant vector store configuration
    qdrant_host: str = "qdrant"
    qdrant_port: int = Field(default=6333, ge=1, le=65535)
    qdrant_collection: str = "lena_pilot"
    qdrant_location: Optional[str] = None

    # File paths
    data_dir: Path = Field(default=PROJECT_ROOT / "data")
    storage_dir: Path = Field(default=PROJECT_ROOT / "storage")

    # LLM configuration
    llm_mode: Literal["hf", "off"] = "hf"
    hf_model: str = "HuggingFaceH4/zephyr-7b-beta"
    hf_max_new_tokens: int = Field(default=256, ge=1, le=2048)

    # Retrieval settings
    retrieval_top_k: int = Field(default=6, ge=1, le=50)
    embedding_batch_size: int = Field(default=16, ge=1, le=256)

    # Escalation and analytics
    escalation_confidence_threshold: float = Field(default=0.55, ge=0.0, le=1.0)
    analytics_history_days: int = Field(default=90, ge=1, le=365)

    @field_validator("data_dir", "storage_dir", mode="before")
    @classmethod
    def coerce_path(cls, value: str | Path) -> Path:
        """Convert string paths to Path objects."""
        return Path(value) if isinstance(value, str) else value


settings = Settings()
