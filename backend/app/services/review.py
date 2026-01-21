"""FAQ and review queue storage."""

from __future__ import annotations

from typing import Any, List
from uuid import uuid4

from .storage import (
    append_jsonl,
    read_json,
    read_jsonl,
    storage_path,
    utc_timestamp,
    write_json,
    write_jsonl,
)


def load_faq(course_id: str | None = None) -> List[dict[str, Any]]:
    """Load FAQ entries, optionally filtered by course."""
    entries = read_json(storage_path("faq.json"), default=[])
    if not isinstance(entries, list):
        return []
    if course_id is None:
        return entries
    return [entry for entry in entries if entry.get("course_id") == course_id]


def save_faq(entries: List[dict[str, Any]]) -> None:
    """Persist FAQ entries to storage."""
    write_json(storage_path("faq.json"), entries)


def list_review_queue() -> List[dict[str, Any]]:
    """Load all items in the review queue."""
    return read_jsonl(storage_path("review_queue.jsonl"))


def append_review_item(item: dict[str, Any]) -> dict[str, Any]:
    """Add an item to the review queue."""
    payload = {
        **item,
        "id": item.get("id") or uuid4().hex,
        "submitted_at": utc_timestamp(),
    }
    append_jsonl(storage_path("review_queue.jsonl"), payload)
    return payload


def remove_review_item(item_id: str) -> dict[str, Any] | None:
    """Remove an item from the review queue."""
    entries = list_review_queue()
    remaining: List[dict[str, Any]] = []
    removed: dict[str, Any] | None = None

    for entry in entries:
        if entry.get("id") == item_id and removed is None:
            removed = entry
            continue
        remaining.append(entry)

    write_jsonl(storage_path("review_queue.jsonl"), remaining)
    return removed
