"""Seed synthetic interaction data for demo environments.

The pilot ships with demo course materials, but exports are based on interaction
logs under storage/. In a fresh demo, those logs are empty until someone uses
the chat UI. This module optionally seeds a small, clearly synthetic dataset so
export users can see the data structure immediately.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ..settings import settings
from . import courses, escalations, questions, review
from .analytics import log_event
from .storage import read_json, storage_path, utc_timestamp, write_json


def _file_has_content(name: str) -> bool:
    path = storage_path(name)
    if not path.exists():
        return False
    try:
        return path.stat().st_size > 0
    except OSError:
        return False


def _already_seeded() -> bool:
    marker = storage_path("demo_seed.json")
    if not marker.exists():
        return False
    try:
        payload = read_json(marker, default={})
        return isinstance(payload, dict) and payload.get("seeded") is True
    except Exception:
        return True


def _demo_escalation_count() -> int:
    try:
        entries = escalations.list_requests()
    except Exception:
        return 0
    return sum(1 for e in entries if "demo_escalation" in str(e.get("question_id") or ""))


def maybe_seed() -> None:
    """Seed demo logs if enabled and storage is empty."""
    if not getattr(settings, "demo_seed_data", False):
        return

    seeded_marker = _already_seeded()
    need_escalations = _demo_escalation_count() < 20

    now = datetime.now(timezone.utc)
    course_list = courses.load_courses()
    if not course_list:
        return

    def ts(days_ago: int) -> str:
        return (now - timedelta(days=days_ago)).isoformat().replace("+00:00", "Z")

    # Create a few synthetic Q&A records per course (only once).
    if not seeded_marker:
        for idx, course in enumerate(course_list, start=1):
            course_id = str(course.get("id") or f"course{idx}")

            qid1 = f"demo_{course_id}_q1"
            qid2 = f"demo_{course_id}_q2"

            log_event(
                {
                    "type": "ask",
                    "question_id": qid1,
                    "question": "When is Assignment 1 due? (demo seed)",
                    "confidence": 0.82,
                    "course_id": course_id,
                    "timestamp": ts(2),
                }
            )
            questions.record_answer(
                {
                    "question_id": qid1,
                    "course_id": course_id,
                    "question": "When is Assignment 1 due? (demo seed)",
                    "answer": "Demo answer: Assignment 1 is due on the date listed in the course schedule.",
                    "citations": [
                        {
                            "title": "Assignments",
                            "section": "Assignment 1",
                            "source_path": f"{course_id}/assignments.md",
                        }
                    ],
                    "confidence": 0.82,
                    "timestamp": ts(2),
                }
            )

            log_event(
                {
                    "type": "feedback",
                    "question_id": qid1,
                    "helpful": True,
                    "confidence": 0.82,
                    "question": "When is Assignment 1 due? (demo seed)",
                    "course_id": course_id,
                    "timestamp": ts(2),
                }
            )

            log_event(
                {
                    "type": "ask",
                    "question_id": qid2,
                    "question": "What is the late policy? (demo seed)",
                    "confidence": 0.42,
                    "course_id": course_id,
                    "timestamp": ts(1),
                }
            )
            questions.record_answer(
                {
                    "question_id": qid2,
                    "course_id": course_id,
                    "question": "What is the late policy? (demo seed)",
                    "answer": "Demo answer: Late work may be accepted with a penalty; consult the syllabus policy section.",
                    "citations": [
                        {
                            "title": "Course Policy",
                            "section": "Late work",
                            "source_path": f"{course_id}/policy.md",
                        }
                    ],
                    "confidence": 0.42,
                    "timestamp": ts(1),
                }
            )

            log_event(
                {
                    "type": "feedback",
                    "question_id": qid2,
                    "helpful": False,
                    "confidence": 0.42,
                    "question": "What is the late policy? (demo seed)",
                    "course_id": course_id,
                    "timestamp": ts(1),
                }
            )

            # Seed a review queue item (mirrors what happens for not helpful feedback).
            review.append_review_item(
                {
                    "question_id": qid2,
                    "question": "What is the late policy? (demo seed)",
                    "answer": "Demo answer: Late work may be accepted with a penalty; consult the syllabus policy section.",
                    "citations": [
                        {
                            "title": "Course Policy",
                            "section": "Late work",
                            "source_path": f"{course_id}/policy.md",
                        }
                    ],
                    "comment": "Demo feedback: clarify penalty percentage and grace period.",
                    "helpful": False,
                    "course_id": course_id,
                }
            )

    # Seed or top-up escalation requests to at least 20 entries (PII encrypted when key configured).
    if need_escalations:
        try:
            existing = _demo_escalation_count()
            start = existing + 1
            target = 20
            for idx in range(start, target + 1):
                course_id = str(course_list[0].get("id") or "demo")
                if len(course_list) > 1 and idx > 10:
                    course_id = str(course_list[1].get("id"))
                escalations.append_request(
                    {
                        "question_id": f"{course_id}_demo_escalation_{idx}",
                        "question": f"Demo escalation #{idx}: I have a question about assignment {idx}.",
                        "student_name": f"Demo Student {idx}",
                        "student_email": f"student{idx:02d}@example.edu",
                        "course_id": course_id,
                        "submitted_at": utc_timestamp(),
                        "status": "new" if idx <= 6 else ("in_process" if idx <= 12 else "contacted"),
                        "notes": "" if idx <= 12 else "Awaiting student reply",
                        "delivered": idx > 12,
                    }
                )
        except RuntimeError:
            # Encryption key missing; skip seeding escalations to avoid plaintext PII.
            pass

    # Seed a tiny FAQ so the FAQ page shows structure immediately.
    faq_path = storage_path("faq.json")
    if not faq_path.exists():
        demo_course = str(course_list[0].get("id") or "demo")
        write_json(
            faq_path,
            [
                {
                    "question": "Where do I submit assignments? (demo seed)",
                    "answer": "Demo answer: Submit assignments via the LMS link provided in the syllabus.",
                    "source_path": f"{demo_course}/syllabus.md",
                    "updated_at": utc_timestamp(),
                    "course_id": demo_course,
                }
            ],
        )
    else:
        existing = read_json(faq_path, default=[])
        if isinstance(existing, list) and not existing:
            demo_course = str(course_list[0].get("id") or "demo")
            write_json(
                faq_path,
                [
                    {
                        "question": "Where do I submit assignments? (demo seed)",
                        "answer": "Demo answer: Submit assignments via the LMS link provided in the syllabus.",
                        "source_path": f"{demo_course}/syllabus.md",
                        "updated_at": utc_timestamp(),
                        "course_id": demo_course,
                    }
                ],
            )

    write_json(
        storage_path("demo_seed.json"),
        {"seeded": True, "seeded_at": utc_timestamp(), "courses": [c.get("id") for c in course_list]},
    )
