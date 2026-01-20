"""Content ingestion endpoint for populating the vector store."""

import logging

from fastapi import APIRouter, HTTPException, Request

from ...rag.ingest import IngestResult, run_ingest
from ...limiting import limiter
from ...settings import settings

router = APIRouter(tags=["ingest"])
logger = logging.getLogger(__name__)


@router.post("/ingest/run", response_model=IngestResult)
@limiter.limit("2/minute")
async def ingest_run(request: Request) -> IngestResult:
    """Run the content ingestion pipeline.

    Parses documents from the data directory, generates embeddings,
    and upserts them into the vector store.

    Raises:
        HTTPException: If ingestion fails.
    """
    if not settings.enable_ingest_endpoint:
        raise HTTPException(status_code=404, detail="Not found")
    try:
        result = run_ingest()
        logger.info(
            "Ingestion complete: %d docs, %d chunks",
            result.counts.docs,
            result.counts.chunks,
        )
        return result
    except Exception as exc:
        # Log full exception for debugging but return generic message to client
        logger.exception("Ingestion failed: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="Ingestion failed. Check server logs for details."
        ) from exc
