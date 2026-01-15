from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import admin, chat, courses, feedback, health, ingest, insights
from .services import storage

app = FastAPI(
    title="LENA Backend",
    version="0.1.0",
    description="Learning Engagement & Navigation Assistant API",
    docs_url="/docs" if os.getenv("LENA_ENABLE_DOCS", "true").lower() == "true" else None,
    redoc_url="/redoc" if os.getenv("LENA_ENABLE_DOCS", "true").lower() == "true" else None,
)

# Configure CORS from environment; defaults to localhost for development.
_cors_origins_env = os.getenv("LENA_CORS_ORIGINS", "http://localhost:3000")
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
