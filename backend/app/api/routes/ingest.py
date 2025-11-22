from fastapi import APIRouter, HTTPException

from ...rag.ingest import IngestResult, run_ingest

router = APIRouter()

@router.post("/ingest/run", response_model=IngestResult)
def ingest_run() -> IngestResult:
    try:
        return run_ingest()
    except Exception as exc:  # pragma: no cover - surfaced to clients
        raise HTTPException(status_code=500, detail=str(exc)) from exc
