from __future__ import annotations

from typing import Any, List

from .storage import read_json, storage_path

DEFAULT_COURSES: list[dict[str, str]] = [
    {
        "id": "anth101",
        "name": "ANTH 101 · Cultural Anthropology",
        "code": "ANTH 101",
        "term": "Fall 2024",
    },
    {
        "id": "anth204",
        "name": "ANTH 204 · Archaeology of Everyday Life",
        "code": "ANTH 204",
        "term": "Fall 2024",
    },
]


def _coerce_courses(payload: Any) -> list[dict[str, str]]:
    if isinstance(payload, list):
        sanitized: list[dict[str, str]] = []
        for entry in payload:
            if isinstance(entry, dict) and entry.get("id") and entry.get("name"):
                sanitized.append(
                    {
                        "id": str(entry["id"]),
                        "name": str(entry["name"]),
                        "code": entry.get("code"),
                        "term": entry.get("term"),
                    }
                )
        if sanitized:
            return sanitized
    return DEFAULT_COURSES


def load_courses() -> List[dict[str, str]]:
    """Load the list of courses from storage, seeding defaults when empty."""
    data = read_json(storage_path("courses.json"), default=DEFAULT_COURSES)
    return _coerce_courses(data)


def get_course(course_id: str | None) -> dict[str, str] | None:
    if not course_id:
        return None
    return next((course for course in load_courses() if course["id"] == course_id), None)


def get_default_course() -> dict[str, str] | None:
    courses = load_courses()
    return courses[0] if courses else None
