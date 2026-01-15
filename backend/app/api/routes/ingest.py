"""Content ingestion endpoint for populating the vector store."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from ...rag.ingest import IngestResult, run_ingest

router = APIRouter(tags=["ingest"])
logger = logging.getLogger(__name__)


@router.post("/ingest/run", response_model=IngestResult)
def ingest_run() -> IngestResult:
    """Run the content ingestion pipeline.

    Parses documents from the data directory, generates embeddings,
    and upserts them into the vector store.

    Raises:
        HTTPException: If ingestion fails.
    """
    try:
        result = run_ingest()
        logger.info(
            "Ingestion complete: %d docs, %d chunks",
            result.counts.docs,
            result.counts.chunks,
        )
        return result
    except Exception as exc:
        logger.exception("Ingestion failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
