"""Health check endpoint for infrastructure monitoring."""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/healthz")
def healthcheck() -> Dict[str, Any]:
    """Basic readiness probe for infrastructure integrations."""
    return {"ok": True, "service": "lena-backend"}
