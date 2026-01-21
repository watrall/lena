"""Escalation request storage (with optional PII encryption)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, List
from uuid import uuid4

from .crypto import decrypt_pii, encrypt_pii
from .storage import append_jsonl, read_jsonl, storage_path, utc_timestamp


def _records_path() -> Path:
    """Return the path to the escalations storage file."""
    return storage_path("escalations.jsonl")


def append_request(payload: dict[str, Any]) -> dict[str, Any]:
    """Persist a learner escalation request for instructor follow-up."""
    # Encrypt PII fields before storage
    student_name = payload.get("student_name") or ""
    student_email = payload.get("student_email") or ""

    record = {
        "id": payload.get("id") or uuid4().hex,
        "question_id": payload.get("question_id"),
        "question": payload.get("question"),
        "student": encrypt_pii(student_name),
        "student_email": encrypt_pii(student_email),
        "course_id": payload.get("course_id"),
        "submitted_at": payload.get("submitted_at") or utc_timestamp(),
        "delivered": bool(payload.get("delivered", False)),
    }
    append_jsonl(_records_path(), record)
    return record


def list_requests(course_id: str | None = None) -> List[dict[str, Any]]:
    """Return recorded escalation requests, optionally filtered by course."""
    entries = read_jsonl(_records_path())

    # Decrypt PII fields for each entry
    decrypted_entries = []
    for entry in entries:
        decrypted_entry = {**entry}
        if "student" in decrypted_entry:
            decrypted_entry["student"] = decrypt_pii(str(decrypted_entry["student"]))
        if "student_email" in decrypted_entry:
            decrypted_entry["student_email"] = decrypt_pii(str(decrypted_entry["student_email"]))
        decrypted_entries.append(decrypted_entry)

    if course_id is None:
        return decrypted_entries
    return [entry for entry in decrypted_entries if entry.get("course_id") == course_id]
