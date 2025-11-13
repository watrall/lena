from __future__ import annotations

from datetime import datetime
from typing import Any, List
from uuid import uuid4

from .storage import append_jsonl, read_json, read_jsonl, storage_path, write_json, write_jsonl


def load_faq(course_id: str | None = None) -> List[dict[str, Any]]:
    entries = read_json(storage_path("faq.json"), default=[])
    if not isinstance(entries, list):
        return []
    if course_id is None:
        return entries
    return [entry for entry in entries if entry.get("course_id") == course_id]


def save_faq(entries: List[dict[str, Any]]) -> None:
    write_json(storage_path("faq.json"), entries)


def list_review_queue() -> List[dict[str, Any]]:
    return read_jsonl(storage_path("review_queue.jsonl"))


def append_review_item(item: dict[str, Any]) -> dict[str, Any]:
    payload = {
        **item,
        "id": item.get("id") or uuid4().hex,
        "submitted_at": datetime.utcnow().isoformat() + "Z",
    }
    append_jsonl(storage_path("review_queue.jsonl"), payload)
    return payload


def remove_review_item(item_id: str) -> dict[str, Any] | None:
    entries = list_review_queue()
    remaining = []
    removed = None
    for entry in entries:
        if entry.get("id") == item_id and removed is None:
            removed = entry
            continue
        remaining.append(entry)
    write_jsonl(storage_path("review_queue.jsonl"), remaining)
    return removed
