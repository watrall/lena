"""Qdrant vector database client utilities.

Provides connection management and collection initialization for the Qdrant
vector store. Supports both hosted Qdrant instances and in-memory mode for testing.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any, Dict, Iterable, List, Optional

try:
    from qdrant_client import QdrantClient  # type: ignore
    from qdrant_client.http import models as qmodels  # type: ignore
    from qdrant_client.http.exceptions import UnexpectedResponse  # type: ignore
except ImportError:  # pragma: no cover - exercised when qdrant_client is missing
    QdrantClient = None  # type: ignore[assignment]
    UnexpectedResponse = Exception  # type: ignore[assignment]

    class _DistanceEnum:
        COSINE = "cosine"

    class _VectorParams:
        def __init__(self, size: int, distance: str):
            self.size = size
            self.distance = distance

    class _PointStruct:
        def __init__(self, id: Any, vector: list[float], payload: dict):
            self.id = id
            self.vector = vector
            self.payload = payload

    class _MatchValue:
        def __init__(self, value: Any):
            self.value = value

    class _FieldCondition:
        def __init__(self, key: str, match: "_MatchValue"):
            self.key = key
            self.match = match

    class _Filter:
        def __init__(self, must: Optional[list["_FieldCondition"]] = None):
            self.must = must or []

    class _FilterSelector:
        def __init__(self, filter: "_Filter"):
            self.filter = filter

    class _ScoredPoint:
        def __init__(self, id: Any, payload: dict, score: float):
            self.id = id
            self.payload = payload
            self.score = score

    class _CollectionInfo:
        def __init__(self, size: int):
            self.config = type(
                "cfg",
                (),
                {"params": type("params", (), {"vectors": type("vec", (), {"size": size})})},
            )

    class _InMemoryQdrantClient:
        """Tiny in-memory stand-in for qdrant_client used in test/offline environments."""

        def __init__(self):
            self._collections: Dict[str, Dict[str, Any]] = {}

        def _ensure_collection(self, name: str, size: Optional[int] = None):
            coll = self._collections.setdefault(name, {"points": [], "size": size or 0})
            if size is not None:
                coll["size"] = size
            return coll

        def recreate_collection(self, collection_name: str, vectors_config: "_VectorParams"):
            self._collections[collection_name] = {"points": [], "size": vectors_config.size}

        def delete_collection(self, collection_name: str):
            self._collections.pop(collection_name, None)

        def get_collection(self, collection_name: str):
            coll = self._collections.get(collection_name)
            if not coll:
                raise UnexpectedResponse("Collection missing")
            return _CollectionInfo(size=coll["size"])

        def upsert(self, collection_name: str, points: Iterable["_PointStruct"]):
            coll = self._ensure_collection(collection_name)
            coll.setdefault("points", [])
            coll["points"].extend(list(points))

        def search(
            self,
            collection_name: str,
            query_vector: list[float],
            limit: int,
            with_payload: bool,
            with_vectors: bool,
            query_filter: Optional["_Filter"] = None,
        ) -> List["_ScoredPoint"]:
            coll = self._collections.get(collection_name, {"points": []})
            points: list[_PointStruct] = coll["points"]
            filtered: list[_PointStruct] = []
            for point in points:
                if query_filter and query_filter.must:
                    keep = True
                    for cond in query_filter.must:
                        if cond.key not in point.payload or point.payload[cond.key] != cond.match.value:
                            keep = False
                            break
                    if not keep:
                        continue
                filtered.append(point)
            results: list[_ScoredPoint] = []
            for pt in filtered:
                score = self._cosine(query_vector, pt.vector)
                results.append(_ScoredPoint(id=pt.id, payload=pt.payload, score=score))
            results.sort(key=lambda item: item.score, reverse=True)
            return results[:limit]

        def delete(self, collection_name: str, points_selector: "_FilterSelector"):
            coll = self._collections.get(collection_name)
            if not coll:
                return
            def matches(point: _PointStruct) -> bool:
                if not points_selector.filter or not points_selector.filter.must:
                    return True
                for cond in points_selector.filter.must:
                    if point.payload.get(cond.key) != cond.match.value:
                        return False
                return True

            coll["points"] = [pt for pt in coll["points"] if not matches(pt)]

        @staticmethod
        def _cosine(a: list[float], b: list[float]) -> float:
            if not a or not b or len(a) != len(b):
                return 0.0
            import math

            dot = sum(x * y for x, y in zip(a, b))
            norm_a = math.sqrt(sum(x * x for x in a))
            norm_b = math.sqrt(sum(y * y for y in b))
            if norm_a == 0 or norm_b == 0:
                return 0.0
            return dot / (norm_a * norm_b)

    qmodels = type(
        "qmodels",
        (),
        {
            "VectorParams": _VectorParams,
            "Distance": _DistanceEnum,
            "PointStruct": _PointStruct,
            "Filter": _Filter,
            "FieldCondition": _FieldCondition,
            "MatchValue": _MatchValue,
            "FilterSelector": _FilterSelector,
            "ScoredPoint": _ScoredPoint,
        },
    )

from ..models.embeddings import get_embedder
from ..settings import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_qdrant_client() -> QdrantClient:
    """Return a cached Qdrant client instance.

    Uses the in-memory location if configured, otherwise connects to the
    configured host and port.
    """
    if QdrantClient is None:
        logger.warning("qdrant_client not installed; using in-memory stub")
        return _InMemoryQdrantClient()  # type: ignore[return-value]
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
