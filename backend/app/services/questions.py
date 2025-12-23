from __future__ import annotations

from typing import Any

from .storage import append_jsonl, read_jsonl, storage_path


def _answers_path():
    return storage_path("answers.jsonl")


def record_answer(payload: dict[str, Any]) -> None:
    append_jsonl(_answers_path(), payload)


def lookup_answer(question_id: str) -> dict[str, Any] | None:
    for entry in reversed(read_jsonl(_answers_path())):
        if entry.get("question_id") == question_id:
            return entry
    return None
