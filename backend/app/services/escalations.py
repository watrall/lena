"""Escalation request management."""

from __future__ import annotations

from typing import Any, List
from uuid import uuid4

from .storage import append_jsonl, read_jsonl, storage_path, utc_timestamp


def _records_path():
    """Return the path to the escalations storage file."""
    return storage_path("escalations.jsonl")


def append_request(payload: dict[str, Any]) -> dict[str, Any]:
    """Persist a learner escalation request for instructor follow-up.

    Args:
        payload: Escalation details including student info and question.

    Returns:
        The persisted record with generated ID and timestamp.
    """
    record = {
        "id": payload.get("id") or uuid4().hex,
        "question_id": payload.get("question_id"),
        "question": payload.get("question"),
        "student": payload.get("student_name"),
        "student_email": payload.get("student_email"),
        "course_id": payload.get("course_id"),
        "submitted_at": payload.get("submitted_at") or utc_timestamp(),
        "delivered": bool(payload.get("delivered", False)),
    }
    append_jsonl(_records_path(), record)
    return record


def list_requests(course_id: str | None = None) -> List[dict[str, Any]]:
    """Return all recorded escalation requests, optionally filtered by course.

    Args:
        course_id: Optional course ID to filter by.

    Returns:
        A list of escalation request records.
    """
    entries = read_jsonl(_records_path())
    if course_id is None:
        return entries
    return [entry for entry in entries if entry.get("course_id") == course_id]
