"""Shared rate limiter configuration.

SlowAPI requires the limiter to be importable by route modules so that
per-endpoint limits can be applied without circular imports.
"""

from __future__ import annotations

try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address
except ImportError:  # pragma: no cover - offline/test fallback
    def get_remote_address(_request):
        return "0.0.0.0"

    class Limiter:
        def __init__(self, *_, **__):
            pass

        def limit(self, *_args, **_kwargs):
            def decorator(func):
                return func

            return decorator

# Global limiter configuration - uses client IP address.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    application_limits=["200/minute"],
)
