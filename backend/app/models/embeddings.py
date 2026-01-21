"""Embedding model loader (cached)."""

from __future__ import annotations

import logging
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from ..settings import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformer:
    """Load the sentence-transformers model once per process."""
    logger.info("Loading embedding model: %s", settings.embed_model)
    return SentenceTransformer(settings.embed_model, device="cpu")
