from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.app.services import escalations
from backend.app.settings import settings


def _read_escalations_raw() -> list[dict]:
    path = Path(settings.storage_dir) / "escalations.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_append_request_requires_course_and_question(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "storage_dir", tmp_path)
    with pytest.raises(ValueError):
        escalations.append_request(
            {
                "question_id": "",
                "question": "Missing course id",
                "student_name": "Test",
                "student_email": "test@example.com",
                "course_id": "",
            }
        )


def test_append_request_deduplicates_by_course_and_question(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "storage_dir", tmp_path)
    (tmp_path / "courses.json").write_text(
        '[{"id": "courseA", "name": "Course A"}]',
        encoding="utf-8",
    )

    first = escalations.append_request(
        {
            "question_id": "q1",
            "question": "When is the exam?",
            "student_name": "Test",
            "student_email": "test@example.com",
            "course_id": "courseA",
            "status": "contacted",
        }
    )
    second = escalations.append_request(
        {
            "question_id": "q1",
            "question": "When is the exam?",
            "student_name": "Test",
            "student_email": "test@example.com",
            "course_id": "courseA",
            "status": "resolved",  # should be ignored for dedupe
        }
    )

    assert first["id"] == second["id"]
    records = _read_escalations_raw()
    assert len(records) == 1
    # Status should remain the original (contacted is valid) not overwritten by duplicate
    assert records[0]["status"] == "contacted"
