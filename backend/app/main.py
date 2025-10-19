from fastapi import APIRouter, FastAPI, HTTPException

from .rag.ingest import IngestResult, run_ingest

app = FastAPI(title="LENA Backend", version="0.1.0")
router = APIRouter()


@app.get("/healthz")
def healthcheck() -> dict[str, bool]:
    """Basic readiness probe for infrastructure integrations."""
    return {"ok": True}


@router.post("/ingest/run", response_model=IngestResult)
def ingest_run() -> IngestResult:
    try:
        return run_ingest()
    except Exception as exc:  # pragma: no cover - surfaced to clients
        raise HTTPException(status_code=500, detail=str(exc)) from exc


app.include_router(router, prefix="")
