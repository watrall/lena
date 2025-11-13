from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, List
from uuid import uuid4

from .storage import append_jsonl, read_jsonl, storage_path


def _records_path():
    return storage_path("escalations.jsonl")


def append_request(payload: dict[str, Any]) -> dict[str, Any]:
    """Persist a learner escalation request for instructor follow-up."""
    record = {
        "id": payload.get("id") or uuid4().hex,
        "question_id": payload.get("question_id"),
        "question": payload.get("question"),
        "student": payload.get("student_name"),
        "student_email": payload.get("student_email"),
        "course_id": payload.get("course_id"),
        "submitted_at": payload.get("submitted_at") or datetime.utcnow().isoformat() + "Z",
        "delivered": bool(payload.get("delivered", False)),
    }
    append_jsonl(_records_path(), record)
    return record


def list_requests(course_id: str | None = None) -> List[dict[str, Any]]:
    """Return all recorded escalation requests, optionally filtered by course."""
    entries = read_jsonl(_records_path())
    if course_id is None:
        return entries
    return [entry for entry in entries if entry.get("course_id") == course_id]
