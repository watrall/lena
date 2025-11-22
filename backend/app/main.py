from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import admin, chat, courses, feedback, health, ingest, insights
from .services import storage

app = FastAPI(title="LENA Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

storage.ensure_storage()

app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(courses.router)
app.include_router(chat.router)
app.include_router(feedback.router)
app.include_router(admin.router)
app.include_router(insights.router)
