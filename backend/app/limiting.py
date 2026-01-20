"""Shared rate limiter configuration.

SlowAPI requires the limiter to be importable by route modules so that
per-endpoint limits can be applied without circular imports.
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

# Global limiter configuration - uses client IP address.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    application_limits=["200/minute"],
)

