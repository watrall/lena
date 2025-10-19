from functools import lru_cache

from sentence_transformers import SentenceTransformer

from ..settings import settings


@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformer:
    """Load the sentence-transformers model once per process."""
    return SentenceTransformer(settings.embed_model, device="cpu")
