from __future__ import annotations

import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .api.routes import admin, chat, courses, export, feedback, health, ingest, insights, instructors
from .limiting import limiter
from .services import demo_seed
from .services import storage
from .settings import settings

app = FastAPI(
    title="LENA Backend",
    version="0.1.0",
    description="Learning Engagement & Navigation Assistant API",
    docs_url="/docs" if os.getenv("LENA_ENABLE_DOCS", "false").lower() == "true" else None,
    redoc_url="/redoc" if os.getenv("LENA_ENABLE_DOCS", "false").lower() == "true" else None,
)

# Register rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

trusted_hosts = [h.strip() for h in settings.trusted_hosts.split(",") if h.strip()]
if trusted_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)

# Basic hardening headers (auth is handled externally in real deployments).
@app.middleware("http")
async def security_headers(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            allowed_max = settings.max_request_body_bytes
            if request.url.path.endswith("/resources/upload"):
                allowed_max = max(allowed_max, 26_000_000)
            if int(content_length) > allowed_max:
                from fastapi.responses import JSONResponse

                return JSONResponse(
                    status_code=413,
                    content={"detail": "Request body too large"},
                )
        except ValueError:
            pass
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
    response.headers.setdefault("Cache-Control", "no-store")
    response.headers.setdefault("Pragma", "no-cache")
    return response

# Configure CORS from environment; defaults to common localhost variants for development.
_cors_origins_env = os.getenv("LENA_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
CORS_ORIGINS = [origin.strip() for origin in _cors_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Accept", "Authorization"],
    expose_headers=["Content-Disposition"],
)

storage.ensure_storage()
demo_seed.maybe_seed()

app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(courses.router)
app.include_router(chat.router)
app.include_router(feedback.router)
app.include_router(admin.router)
app.include_router(insights.router)
app.include_router(export.router)
app.include_router(instructors.router)
