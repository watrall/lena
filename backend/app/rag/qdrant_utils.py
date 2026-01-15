"""Qdrant vector database client utilities.

Provides connection management and collection initialization for the Qdrant
vector store. Supports both hosted Qdrant instances and in-memory mode for testing.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from qdrant_client.http.exceptions import UnexpectedResponse

from ..models.embeddings import get_embedder
from ..settings import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_qdrant_client() -> QdrantClient:
    """Return a cached Qdrant client instance.

    Uses the in-memory location if configured, otherwise connects to the
    configured host and port.
    """
    if settings.qdrant_location:
        logger.info("Connecting to Qdrant at %s", settings.qdrant_location)
        return QdrantClient(location=settings.qdrant_location)
    logger.info("Connecting to Qdrant at %s:%d", settings.qdrant_host, settings.qdrant_port)
    return QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)


def ensure_collection() -> None:
    """Ensure the target collection exists with the expected vector size.

    Recreates the collection if the dimension does not match the current
    embedding model.
    """
    client = get_qdrant_client()
    dim = get_embedder().get_sentence_embedding_dimension()

    try:
        info = client.get_collection(settings.qdrant_collection)
        existing_config = info.config.params.vectors
        if isinstance(existing_config, dict):
            size = next(iter(existing_config.values())).size
        else:
            size = existing_config.size

        if size != dim:
            logger.warning(
                "Collection %s has dimension %d, expected %d. Recreating.",
                settings.qdrant_collection,
                size,
                dim,
            )
            _recreate_collection(client, dim)
    except (UnexpectedResponse, ValueError, AttributeError) as exc:
        logger.info("Creating collection %s: %s", settings.qdrant_collection, exc)
        _recreate_collection(client, dim)


def _recreate_collection(client: QdrantClient, dim: int) -> None:
    """Create or recreate the vector collection with specified dimensions."""
    client.recreate_collection(
        collection_name=settings.qdrant_collection,
        vectors_config=qmodels.VectorParams(size=dim, distance=qmodels.Distance.COSINE),
    )
