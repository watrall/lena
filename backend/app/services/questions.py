"""Question and answer storage for feedback correlation."""

from __future__ import annotations

from typing import Any

from .storage import append_jsonl, read_jsonl, storage_path


def _answers_path():
    """Return the path to the answers storage file."""
    return storage_path("answers.jsonl")


def record_answer(payload: dict[str, Any]) -> None:
    """Persist an answer record for later feedback correlation.

    Args:
        payload: Answer details including question, answer text, and citations.
    """
    append_jsonl(_answers_path(), payload)


def lookup_answer(question_id: str) -> dict[str, Any] | None:
    """Look up a recorded answer by question ID.

    Args:
        question_id: The question ID to look up.

    Returns:
        The answer record, or None if not found.
    """
    for entry in reversed(read_jsonl(_answers_path())):
        if entry.get("question_id") == question_id:
            return entry
    return None
