"""Application configuration loaded from environment variables.

All settings use the LENA_ prefix and can be overridden via environment
variables or a .env file in the project root.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

from pydantic import Field, field_validator, model_validator
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

    # Feature flags (no authentication in pilot mode; disable risky endpoints by default).
    enable_ingest_endpoint: bool = Field(
        default=False,
        description="Enable POST /ingest/run (expensive; should be restricted in deployments).",
    )
    enable_admin_endpoints: bool = Field(
        default=False,
        description="Enable instructor/admin endpoints (review queue + promote).",
    )
    enable_export_endpoint: bool = Field(
        default=False,
        description="Enable GET /admin/export (bulk data export).",
    )
    enable_pii_export: bool = Field(
        default=False,
        description="Allow include_pii=true in exports (requires LENA_ENCRYPTION_KEY).",
    )

    # Export safety limits
    export_max_file_bytes: int = Field(
        default=50_000_000,
        ge=1_000_000,
        le=1_000_000_000,
        description="Maximum on-disk file size (bytes) allowed for export inputs.",
    )
    export_max_records: int = Field(
        default=200_000,
        ge=1_000,
        le=5_000_000,
        description="Maximum records per exported component (to reduce memory/CPU abuse).",
    )
    export_max_components: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of components per export request.",
    )

    # HTTP hardening
    trusted_hosts: str = Field(
        default="localhost,127.0.0.1,testserver",
        description="Comma-separated hostnames allowed by TrustedHostMiddleware.",
    )
    max_request_body_bytes: int = Field(
        default=1_000_000,
        ge=10_000,
        le=50_000_000,
        description="Max request body size in bytes (best-effort via Content-Length).",
    )

    # Demo helpers
    demo_seed_data: bool = Field(
        default=False,
        description="Seed synthetic interaction logs for demo exports when storage is empty.",
    )

    # Demo instructor auth (NOT production authentication)
    instructor_username: str = Field(default="demo", description="Demo instructor username.")
    instructor_password: str = Field(default="demo", description="Demo instructor password.")
    instructor_auth_secret: str = Field(
        default="demo-secret-change-me",
        description="HMAC secret for demo bearer tokens (rotate in any real pilot).",
    )
    instructor_token_ttl_seconds: int = Field(
        default=60 * 60 * 8,
        ge=60,
        le=60 * 60 * 24 * 7,
        description="Demo token TTL in seconds.",
    )
    enable_instructor_auth: bool = Field(
        default=True,
        description="Require demo instructor auth for instructor-only endpoints.",
    )
    uploads_dir: Optional[Path] = Field(
        default=None,
        description="Writable directory for uploaded course resources and link snapshots (defaults to storage_dir/uploads).",
    )
    uploads_allowed_extensions: str = Field(
        default=".md,.markdown,.txt,.ics",
        description="Comma-separated list of allowed upload file extensions (matched case-insensitively).",
    )
    uploads_max_bytes: int = Field(
        default=25_000_000,
        ge=1_000_000,
        le=100_000_000,
        description="Maximum allowed bytes for a single uploaded file.",
    )
    link_snapshot_allowed_ports: str = Field(
        default="80,443",
        description="Comma-separated list of allowed ports for link snapshots.",
    )
    link_snapshot_max_redirects: int = Field(
        default=5,
        ge=0,
        le=20,
        description="Maximum redirects to follow when fetching link snapshots.",
    )
    link_snapshot_timeout_seconds: float = Field(
        default=10.0,
        ge=1.0,
        le=60.0,
        description="Timeout in seconds for link snapshot fetches.",
    )

    @field_validator("data_dir", "storage_dir", "uploads_dir", mode="before")
    @classmethod
    def coerce_path(cls, value: str | Path | None) -> Path | None:
        """Convert string paths to Path objects."""
        if value is None:
            return None
        return Path(value) if isinstance(value, str) else value

    @model_validator(mode="after")
    def default_uploads_dir(self):
        if self.uploads_dir is None:
            self.uploads_dir = self.storage_dir / "uploads"
        return self


settings = Settings()
