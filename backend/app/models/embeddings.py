"""Embedding model utilities for semantic search.

Provides a cached SentenceTransformer instance for generating dense vector
representations of text. The model is loaded lazily on first use.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from ..settings import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformer:
    """Load the sentence-transformers model once per process.

    Returns:
        A cached SentenceTransformer instance configured for CPU inference.
    """
    logger.info("Loading embedding model: %s", settings.embed_model)
    return SentenceTransformer(settings.embed_model, device="cpu")
