from __future__ import annotations

import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from .api.routes import admin, chat, courses, feedback, health, ingest, insights
from .services import storage

# Rate limiter configuration - uses client IP address
# Default: 100 requests/minute, /ask endpoint: 10 requests/minute
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    application_limits=["200/minute"],
)

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

# Configure CORS from environment; defaults to common localhost variants for development.
_cors_origins_env = os.getenv("LENA_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
CORS_ORIGINS = [origin.strip() for origin in _cors_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Accept"],
)

storage.ensure_storage()

app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(courses.router)
app.include_router(chat.router)
app.include_router(feedback.router)
app.include_router(admin.router)
app.include_router(insights.router)
