#!/usr/bin/env python3
"""Seed demo FAQ entries into storage/faq.json.

This writes course-scoped FAQ entries so the frontend FAQ page (which queries
/faq?course_id=...) has something to render.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STORAGE_DIR = Path("storage")
COURSES_PATH = STORAGE_DIR / "courses.json"
FAQ_PATH = STORAGE_DIR / "faq.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        text = path.read_text(encoding="utf-8").strip()
        return json.loads(text) if text else default
    except Exception:
        return default


def _load_courses() -> list[dict[str, str]]:
    payload = _read_json(COURSES_PATH, default=[])
    if isinstance(payload, list) and payload:
        courses: list[dict[str, str]] = []
        for entry in payload:
            if isinstance(entry, dict) and entry.get("id"):
                courses.append({"id": str(entry["id"]), "name": str(entry.get("name") or entry["id"])})
        if courses:
            return courses
    return [
        {"id": "anth101", "name": "ANTH 101"},
        {"id": "anth204", "name": "ANTH 204"},
    ]


def _demo_faq_for_course(course_id: str) -> list[dict[str, Any]]:
    now = _utc_now()
    common = [
        {
            "question": "How do I ask LENA about assignment dates?",
            "answer": "Ask natural questions like “When is Assignment 1 due?” and LENA will cite the relevant policy or schedule.",
            "source_path": "syllabus.md",
            "updated_at": now,
            "course_id": course_id,
        },
        {
            "question": "What should I include in a discussion post?",
            "answer": "State your claim, support it with a reading example, and end with one question for peers. Keep it concise and specific.",
            "source_path": "discussions.md",
            "updated_at": now,
            "course_id": course_id,
        },
        {
            "question": "How do I cite course readings?",
            "answer": "Use the citation style required by the instructor (often APA). Include author, year, title, and page number when quoting.",
            "source_path": "citation-guide.md",
            "updated_at": now,
            "course_id": course_id,
        },
        {
            "question": "Where can I find office hours and contact info?",
            "answer": "Check the syllabus and the weekly announcements; office hours are listed there along with the instructor email.",
            "source_path": "syllabus.md",
            "updated_at": now,
            "course_id": course_id,
        },
    ]
    if course_id == "anth204":
        common.append(
            {
                "question": "What is the best way to prep for the field notes assignment?",
                "answer": "Bring a notebook, record observations with timestamps, and separate description from interpretation; include sketches if helpful.",
                "source_path": "assignments/field-notes.md",
                "updated_at": now,
                "course_id": course_id,
            }
        )
    else:
        common.append(
            {
                "question": "What is cultural relativism?",
                "answer": "It’s the practice of interpreting beliefs and behaviors in their own cultural context rather than judging them by outside standards.",
                "source_path": "lectures/week-1.md",
                "updated_at": now,
                "course_id": course_id,
            }
        )
    return common


def seed(course_id: str | None, overwrite: bool) -> int:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    courses = _load_courses()
    selected_course_ids = [course_id] if course_id else [c["id"] for c in courses]

    existing = _read_json(FAQ_PATH, default=[])
    existing_entries = existing if isinstance(existing, list) else []
    if overwrite:
        existing_entries = []

    existing_keys = {
        (str(entry.get("course_id") or ""), str(entry.get("question") or ""))
        for entry in existing_entries
        if isinstance(entry, dict)
    }

    added = 0
    for cid in selected_course_ids:
        for entry in _demo_faq_for_course(cid):
            key = (entry["course_id"], entry["question"])
            if key in existing_keys:
                continue
            existing_entries.append(entry)
            existing_keys.add(key)
            added += 1

    FAQ_PATH.write_text(json.dumps(existing_entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {FAQ_PATH} (+{added} entries).")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--course-id", default=None, help="Seed only this course_id (default: all)")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite storage/faq.json instead of merging",
    )
    args = parser.parse_args()
    return seed(course_id=args.course_id, overwrite=args.overwrite)


if __name__ == "__main__":
    raise SystemExit(main())

