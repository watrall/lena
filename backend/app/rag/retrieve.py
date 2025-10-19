from __future__ import annotations

import re
from typing import Iterable, List

from pydantic import BaseModel
from qdrant_client.http import models as qmodels

from ..models.embeddings import get_embedder
from ..settings import settings
from .qdrant_utils import ensure_collection, get_qdrant_client


class RetrievedChunk(BaseModel):
    id: str
    text: str
    score: float
    metadata: dict


def retrieve(query: str, top_k: int = 6) -> List[RetrievedChunk]:
    """Perform semantic search with optional keyword filtering."""
    embedder = get_embedder()
    ensure_collection()
    client = get_qdrant_client()

    query_vector = embedder.encode(query).tolist()
    search_result = client.search(
        collection_name=settings.qdrant_collection,
        query_vector=query_vector,
        limit=top_k,
        with_payload=True,
        with_vectors=False,
    )

    filtered = apply_keyword_bias(search_result, query)
    return [
        RetrievedChunk(
            id=str(hit.id),
            text=hit.payload.get("text", ""),
            score=hit.score,
            metadata={k: v for k, v in hit.payload.items() if k != "text"},
        )
        for hit in filtered
    ]


def apply_keyword_bias(results: Iterable[qmodels.ScoredPoint], query: str) -> List[qmodels.ScoredPoint]:
    """Promote results whose title or section contains query keywords."""
    keywords = {
        w.lower()
        for w in re.findall(r"\w+", query)
        if len(w) > 2
    }

    if not keywords:
        return list(results)

    preferred = []
    others = []

    for item in results:
        haystack = " ".join(
            [
                str(item.payload.get("title", "")).lower(),
                str(item.payload.get("section", "")).lower(),
            ]
        )
        if any(word in haystack for word in keywords):
            preferred.append(item)
        else:
            others.append(item)

    return preferred + others
