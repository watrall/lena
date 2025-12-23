from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()

@router.get("/healthz")
def healthcheck() -> dict[str, bool]:
    """Basic readiness probe for infrastructure integrations."""
    return {"ok": True}
