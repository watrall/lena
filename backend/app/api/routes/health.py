"""Health check endpoint for infrastructure monitoring."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/healthz")
def healthcheck() -> dict[str, Any]:
    """Basic readiness probe for infrastructure integrations.

    Returns:
        A dictionary indicating the service is healthy.
    """
    return {"ok": True, "service": "lena-backend"}
