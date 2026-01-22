"""Escalation request storage (with optional PII encryption)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Literal, Optional
from uuid import uuid4

from .crypto import decrypt_pii, encrypt_pii
from .storage import append_jsonl, read_jsonl, storage_path, utc_timestamp, write_jsonl


def _records_path() -> Path:
    """Return the path to the escalations storage file."""
    return storage_path("escalations.jsonl")

def _events_path() -> Path:
    """Return the path to the escalation events storage file."""
    return storage_path("escalation_events.jsonl")


EscalationStatus = Literal["new", "in_process", "contacted", "resolved"]


def _normalize_record(entry: dict[str, Any]) -> dict[str, Any]:
    submitted_at = entry.get("submitted_at") or utc_timestamp()
    status = entry.get("status") or ("resolved" if bool(entry.get("delivered")) else "new")

    confidence = entry.get("confidence")
    try:
        confidence_value = float(confidence) if confidence is not None else None
    except (TypeError, ValueError):
        confidence_value = None

    normalized = {
        **entry,
        "submitted_at": submitted_at,
        "status": status,
        "notes": entry.get("notes") or "",
        "last_viewed_at": entry.get("last_viewed_at"),
        "updated_at": entry.get("updated_at") or submitted_at,
        "contacted_at": entry.get("contacted_at"),
        "resolved_at": entry.get("resolved_at"),
        "confidence": confidence_value,
        "escalation_reason": entry.get("escalation_reason") or "low_confidence",
    }
    # Keep legacy field in sync for existing insights UI.
    normalized["delivered"] = bool(entry.get("delivered", False) or status in {"contacted", "resolved"})
    return normalized


def _decrypt_record(entry: dict[str, Any]) -> dict[str, Any]:
    decrypted = {**entry}
    if "student" in decrypted:
        decrypted["student"] = decrypt_pii(str(decrypted["student"]))
    if "student_email" in decrypted:
        decrypted["student_email"] = decrypt_pii(str(decrypted["student_email"]))
    return decrypted


def _append_event(*, escalation_id: str, course_id: str, event_type: str, meta: dict[str, Any] | None = None) -> None:
    append_jsonl(
        _events_path(),
        {
            "id": uuid4().hex,
            "escalation_id": escalation_id,
            "course_id": course_id,
            "type": event_type,
            "actor": "instructor",
            "at": utc_timestamp(),
            "meta": meta or {},
        },
    )


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
        "status": payload.get("status") or "new",
        "notes": payload.get("notes") or "",
        "last_viewed_at": payload.get("last_viewed_at"),
        "updated_at": payload.get("updated_at"),
        "contacted_at": payload.get("contacted_at"),
        "resolved_at": payload.get("resolved_at"),
        "confidence": payload.get("confidence"),
        "escalation_reason": payload.get("escalation_reason") or "low_confidence",
        "delivered": bool(payload.get("delivered", False)),
    }
    normalized = _normalize_record(record)
    append_jsonl(_records_path(), normalized)
    _append_event(
        escalation_id=str(normalized["id"]),
        course_id=str(normalized.get("course_id") or ""),
        event_type="created",
        meta={"reason": normalized.get("escalation_reason"), "confidence": normalized.get("confidence")},
    )
    return normalized


def list_requests(course_id: str | None = None) -> List[dict[str, Any]]:
    """Return recorded escalation requests, optionally filtered by course."""
    entries = read_jsonl(_records_path())

    # Decrypt PII fields for each entry
    decrypted_entries = []
    for entry in entries:
        decrypted_entries.append(_decrypt_record(_normalize_record({**entry})))

    if course_id is None:
        return decrypted_entries
    return [entry for entry in decrypted_entries if entry.get("course_id") == course_id]


def get_request(escalation_id: str) -> dict[str, Any] | None:
    for entry in list_requests(course_id=None):
        if str(entry.get("id") or "") == escalation_id:
            return entry
    return None


def list_events(*, escalation_id: str, course_id: str) -> list[dict[str, Any]]:
    events = read_jsonl(_events_path())
    filtered = [
        event
        for event in events
        if str(event.get("escalation_id") or "") == escalation_id and str(event.get("course_id") or "") == course_id
    ]
    filtered.sort(key=lambda event: str(event.get("at") or ""), reverse=True)
    return filtered


def mark_viewed(*, escalation_id: str, course_id: str) -> dict[str, Any] | None:
    records = read_jsonl(_records_path())
    updated: list[dict[str, Any]] = []
    found: dict[str, Any] | None = None

    for record in records:
        normalized = _normalize_record(record)
        if str(normalized.get("id") or "") != escalation_id:
            updated.append(record)
            continue
        if str(normalized.get("course_id") or "") != course_id:
            updated.append(record)
            continue

        if normalized.get("last_viewed_at"):
            updated.append(record)
            found = normalized
            continue

        next_record = {**record, "last_viewed_at": utc_timestamp(), "updated_at": utc_timestamp()}
        updated.append(next_record)
        found = _normalize_record(next_record)

    if found is None:
        return None

    write_jsonl(_records_path(), updated)
    _append_event(escalation_id=escalation_id, course_id=course_id, event_type="viewed")
    return _decrypt_record(found)


def update_request(
    *,
    escalation_id: str,
    course_id: str,
    status: Optional[EscalationStatus] = None,
    notes: Optional[str] = None,
) -> dict[str, Any] | None:
    records = read_jsonl(_records_path())
    updated: list[dict[str, Any]] = []
    found: dict[str, Any] | None = None

    for record in records:
        normalized = _normalize_record(record)
        if str(normalized.get("id") or "") != escalation_id:
            updated.append(record)
            continue
        if str(normalized.get("course_id") or "") != course_id:
            updated.append(record)
            continue

        next_record = {**record}
        now = utc_timestamp()

        if notes is not None:
            next_record["notes"] = notes

        if status is not None:
            next_record["status"] = status
            if status == "new":
                next_record["last_viewed_at"] = None
            if status == "contacted" and not normalized.get("contacted_at"):
                next_record["contacted_at"] = now
            if status == "resolved":
                if not normalized.get("resolved_at"):
                    next_record["resolved_at"] = now
                if not normalized.get("contacted_at"):
                    next_record["contacted_at"] = now
            if status != "resolved":
                next_record["resolved_at"] = None

            next_record["delivered"] = status in {"contacted", "resolved"}

        next_record["updated_at"] = now

        updated.append(next_record)
        found = _normalize_record(next_record)

        if status is not None and status != normalized.get("status"):
            _append_event(
                escalation_id=escalation_id,
                course_id=course_id,
                event_type="status_changed",
                meta={"from": normalized.get("status"), "to": status},
            )
        if notes is not None and notes != str(normalized.get("notes") or ""):
            _append_event(
                escalation_id=escalation_id,
                course_id=course_id,
                event_type="note_updated",
            )

    if found is None:
        return None

    write_jsonl(_records_path(), updated)
    return _decrypt_record(found)


def log_reply_initiated(*, escalation_id: str, course_id: str) -> None:
    _append_event(escalation_id=escalation_id, course_id=course_id, event_type="reply_initiated")
