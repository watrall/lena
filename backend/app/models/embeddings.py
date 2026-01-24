"""Embedding model loader (cached)."""

from __future__ import annotations

import logging
from functools import lru_cache

try:
    from sentence_transformers import SentenceTransformer
    from sentence_transformers.util import import_from_string
except ImportError:  # pragma: no cover - fallback exercised when dep missing
    SentenceTransformer = None  # type: ignore[assignment]

    def import_from_string(_path: str):
        raise ImportError("sentence_transformers is not installed")

from ..settings import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformer:
    """Load the sentence-transformers model once per process."""
    logger.info("Loading embedding model: %s", settings.embed_model)

    try:
        return SentenceTransformer(settings.embed_model, device="cpu")
    except Exception as exc:  # pragma: no cover - exercised via runtime path
        logger.error("Embedding model load failed (%s); falling back to MiniLM", exc)
        try:
            # Lazy import to avoid hard dependency during fallback
            fallback_cls = import_from_string("sentence_transformers.models.DistilBertModel")
            model = fallback_cls.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
            return SentenceTransformer(modules=[model])
        except Exception:
            logger.exception("Fallback embedding model failed; using dummy encoder")

            class DummyEmbedder:
                def __init__(self, dim: int = 16):
                    self._dim = dim

                def encode(self, text):
                    # Lightweight deterministic embedding for resilience.
                    import numpy as np

                    if isinstance(text, list):
                        return np.array([self.encode(t) for t in text])
                    seed = abs(hash(text)) % (10**6)
                    return np.array([(seed + i * 31) % 997 / 997 for i in range(self._dim)], dtype=float)

                def get_sentence_embedding_dimension(self):
                    return self._dim

            return DummyEmbedder()
