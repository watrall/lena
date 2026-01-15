"""Course catalog management.

Handles loading, validation, and retrieval of course metadata. Courses are
stored in a JSON file and seeded with defaults if the file doesn't exist.
"""

from __future__ import annotations

from typing import Any

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


def _coerce_courses(payload: Any) -> list[dict[str, str | None]]:
    """Validate and normalize course data from storage."""
    if isinstance(payload, list):
        sanitized: list[dict[str, str | None]] = []
        for entry in payload:
            if isinstance(entry, dict) and entry.get("id") and entry.get("name"):
                sanitized.append(
                    {
                        "id": str(entry["id"]),
                        "name": str(entry["name"]),
                        "code": str(entry["code"]) if entry.get("code") else None,
                        "term": str(entry["term"]) if entry.get("term") else None,
                    }
                )
        if sanitized:
            return sanitized
    return DEFAULT_COURSES


def load_courses() -> list[dict[str, str | None]]:
    """Load the list of courses from storage, seeding defaults when empty."""
    data = read_json(storage_path("courses.json"), default=DEFAULT_COURSES)
    return _coerce_courses(data)


def get_course(course_id: str | None) -> dict[str, str | None] | None:
    """Look up a course by ID.

    Args:
        course_id: The course identifier to look up.

    Returns:
        The course record, or None if not found.
    """
    if not course_id:
        return None
    return next((c for c in load_courses() if c["id"] == course_id), None)


def get_default_course() -> dict[str, str | None] | None:
    """Return the first configured course as the default."""
    courses = load_courses()
    return courses[0] if courses else None
