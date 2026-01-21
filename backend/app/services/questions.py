"""Q&A storage to correlate feedback with the original answer."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .storage import append_jsonl, read_jsonl, storage_path


def _answers_path() -> Path:
    """Return the path to the answers storage file."""
    return storage_path("answers.jsonl")


def record_answer(payload: dict[str, Any]) -> None:
    """Persist an answer record for later feedback correlation."""
    append_jsonl(_answers_path(), payload)


def lookup_answer(question_id: str) -> dict[str, Any] | None:
    """Look up a recorded answer by question ID."""
    for entry in reversed(read_jsonl(_answers_path())):
        if entry.get("question_id") == question_id:
            return entry
    return None
