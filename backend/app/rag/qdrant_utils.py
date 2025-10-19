from functools import lru_cache

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from ..models.embeddings import get_embedder
from ..settings import settings


@lru_cache(maxsize=1)
def get_qdrant_client() -> QdrantClient:
    """Return a cached Qdrant client."""
    return QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)


def ensure_collection() -> None:
    """Ensure the target collection exists with the expected vector size."""
    client = get_qdrant_client()
    dim = get_embedder().get_sentence_embedding_dimension()
    try:
        info = client.get_collection(settings.qdrant_collection)
        existing = info.config.params.vectors
        if isinstance(existing, dict):
            size = next(iter(existing.values())).size  # type: ignore[attr-defined]
        else:
            size = existing.size  # type: ignore[attr-defined]
        if size != dim:
            client.recreate_collection(
                collection_name=settings.qdrant_collection,
                vectors_config=qmodels.VectorParams(size=dim, distance=qmodels.Distance.COSINE),
            )
    except Exception:
        client.recreate_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=qmodels.VectorParams(size=dim, distance=qmodels.Distance.COSINE),
        )
