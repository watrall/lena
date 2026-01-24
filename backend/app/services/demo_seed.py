"""Seed synthetic interaction data for demo environments.

The pilot ships with demo course materials, but exports are based on interaction
logs under storage/. In a fresh demo, those logs are empty until someone uses
the chat UI. This module optionally seeds a small, clearly synthetic dataset so
export users can see the data structure immediately.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from itertools import cycle

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


def _already_seeded() -> dict:
    marker = storage_path("demo_seed.json")
    if not marker.exists():
        return {}
    try:
        payload = read_json(marker, default={})
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _demo_escalation_count() -> int:
    try:
        entries = escalations.list_requests()
    except Exception:
        return 0
    return sum(1 for e in entries if "demo_escalation" in str(e.get("question_id") or ""))


def _count_escalations_by_course() -> dict[str, int]:
    counts: dict[str, int] = {}
    try:
        entries = escalations.list_requests()
    except Exception:
        return counts
    for e in entries:
        cid = str(e.get("course_id") or "")
        counts[cid] = counts.get(cid, 0) + 1
    return counts


def _load_demo_file(course_id: str) -> dict:
    path = Path("data/demo") / f"{course_id}.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _existing_interaction_ids(course_id: str) -> set[str]:
    path = storage_path("interactions.jsonl")
    ids: set[str] = set()
    if not path.exists():
        return ids
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if str(obj.get("course_id") or "") == course_id and obj.get("question_id"):
                ids.add(str(obj["question_id"]))
    except Exception:
        return ids
    return ids


def _ensure_faq(course_list: list[dict[str, str | None]], target_per_course: int = 15) -> None:
    """Ensure each course has a minimum number of FAQ entries for the demo."""
    faq_path = storage_path("faq.json")
    existing = read_json(faq_path, default=[])
    entries = existing if isinstance(existing, list) else []
    now = utc_timestamp()

    base_questions = [
        ("How do I ask LENA about assignment dates?", "Ask natural questions like “When is Assignment 1 due?” and LENA will cite the relevant policy or schedule.", "syllabus.md"),
        ("Where do I find office hours?", "Office hours are listed in the syllabus and weekly announcements; LENA can surface them by course.", "syllabus.md"),
        ("What is the late work policy?", "Late submissions incur the penalty noted in the syllabus; extensions must be requested before the deadline.", "policy.md"),
        ("How do I submit assignments?", "Submit via the LMS Assignments page; include PDFs unless otherwise instructed.", "assignments.md"),
        ("Can I resubmit work?", "Resubmissions are allowed only when the instructor enables it in the LMS; check the assignment details.", "assignments.md"),
        ("How is participation graded?", "Participation is graded weekly based on discussion posts and in-class engagement.", "grading.md"),
        ("How do I cite readings?", "Use the course-required style (often APA). Include author, year, and page for quotes.", "citation-guide.md"),
        ("Where are lecture slides posted?", "Slides are uploaded to the LMS within 24 hours after each class.", "lectures.md"),
        ("Who do I contact for accommodations?", "Contact the accessibility office and copy the instructor with your accommodation letter.", "policy.md"),
        ("Can I collaborate on homework?", "Follow the collaboration rules in the syllabus; when unsure, ask before sharing work.", "policy.md"),
        ("How do I reach the TA?", "TA email and office hours are listed on the syllabus and LMS course page.", "staff.md"),
        ("What goes in field notes?", "Separate observation from interpretation, include timestamps, and keep entries concise.", "field-notes.md"),
        ("How are grades curved?", "Grades are not curved by default; adjustments are announced if applied.", "grading.md"),
        ("Where is the reading list?", "All required and optional readings are in the LMS modules for each week.", "readings.md"),
        ("How do I prepare for the exam?", "Review lecture summaries, key terms, and practice questions provided in the study guide.", "exams.md"),
    ]

    keyset = {
        (str(e.get("course_id") or ""), str(e.get("question") or ""))
        for e in entries
        if isinstance(e, dict)
    }

    added = 0
    for course in course_list:
        cid = str(course.get("id") or "demo")
        current = sum(1 for e in entries if isinstance(e, dict) and str(e.get("course_id") or "") == cid)
        if current >= target_per_course:
            continue
        needed = target_per_course - current
        for idx, (question, answer, source) in enumerate(base_questions):
            if needed <= 0:
                break
            q_text = f"{question} (course {cid}, demo #{idx+1})"
            key = (cid, q_text)
            if key in keyset:
                continue
            entries.append(
                {
                    "question": q_text,
                    "answer": answer,
                    "source_path": source,
                    "updated_at": now,
                    "course_id": cid,
                }
            )
            keyset.add(key)
            added += 1
            needed -= 1

    write_json(faq_path, entries)
    if added:
        pass  # silent; demo helper


def maybe_seed() -> None:
    """Seed demo logs if enabled and storage is empty."""
    if not getattr(settings, "demo_seed_data", False):
        return

    seeded_marker = _already_seeded()

    now = datetime.now(timezone.utc)
    course_list = courses.load_courses()
    if not course_list:
        return

    # Ensure FAQs are present and reasonably dense for each course
    _ensure_faq(course_list, target_per_course=15)

    def ts(days_ago: int) -> str:
        return (now - timedelta(days=days_ago)).isoformat().replace("+00:00", "Z")

    # Seed Q&A, feedback, and FAQs using external demo files (per course) to simplify removal in prod.
    for idx, course in enumerate(course_list, start=1):
        course_id = str(course.get("id") or f"course{idx}")
        data = _load_demo_file(course_id)

        # FAQs from file (fallback to ensure minimum)
        faqs = data.get("faqs") or []
        if faqs:
            faq_path = storage_path("faq.json")
            existing = read_json(faq_path, default=[])
            entries = existing if isinstance(existing, list) else []
            keyset = {(str(e.get("course_id") or ""), str(e.get("question") or "")) for e in entries if isinstance(e, dict)}
            added = 0
            now_iso = utc_timestamp()
            for entry in faqs:
                q = str(entry.get("question") or "").strip()
                if not q:
                    continue
                key = (course_id, q)
                if key in keyset:
                    continue
                entries.append(
                    {
                        "question": q,
                        "answer": entry.get("answer") or "Demo answer pending.",
                        "source_path": entry.get("source_path") or "syllabus.md",
                        "updated_at": entry.get("updated_at") or now_iso,
                        "course_id": course_id,
                    }
                )
                keyset.add(key)
                added += 1
            if added:
                write_json(faq_path, entries)

        # Interactions (ask + feedback) across 14 weeks
        interactions = data.get("interactions") or []
        if interactions:
            existing_ids = _existing_interaction_ids(course_id)
            for idx_int, item in enumerate(interactions, start=1):
                week = int(item.get("week") or idx_int)
                days_ago = max(0, (14 - week) * 7 + 1)
                ts_label = ts(days_ago)
                qid = item.get("question_id") or f"demo_{course_id}_q{idx_int}"
                if qid in existing_ids:
                    continue
                question = item.get("question") or f"Demo question #{idx_int} for {course_id}"
                conf = float(item.get("confidence") or 0.6)
                helpful_flag = bool(item.get("helpful", conf >= 0.6))

                log_event(
                    {
                        "type": "ask",
                        "question_id": qid,
                        "question": question,
                        "confidence": conf,
                        "course_id": course_id,
                        "timestamp": ts_label,
                    }
                )
                questions.record_answer(
                    {
                        "question_id": qid,
                        "course_id": course_id,
                        "question": question,
                        "answer": item.get("answer") or f"Demo answer for: {question}",
                        "citations": item.get("citations")
                        or [
                            {
                                "title": "Course material",
                                "section": question.split('?')[0],
                                "source_path": f"{course_id}/{item.get('source_path') or 'syllabus.md'}",
                            }
                        ],
                        "confidence": conf,
                        "timestamp": ts_label,
                    }
                )
                log_event(
                    {
                        "type": "feedback",
                        "question_id": qid,
                        "helpful": helpful_flag,
                        "confidence": conf,
                        "question": question,
                        "course_id": course_id,
                        "timestamp": ts(max(days_ago - 1, 0)),
                    }
                )

            # Seed a review queue item (mirrors not-helpful feedback).
            review.append_review_item(
                {
                    "question_id": f"demo_{course_id}_q_review",
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

    # Seed or top-up escalation requests to at least target_per_course per course (PII encrypted when key configured).
    try:
        existing_counts = _count_escalations_by_course()
        target_per_course = 15
        status_cycle = cycle(
            ["new"] * 5 + ["contacted"] * 4 + ["in_process"] * 3 + ["resolved"] * 3
        )
        for course in course_list:
            cid = str(course.get("id") or "demo")
            current = existing_counts.get(cid, 0)
            data = _load_demo_file(cid)
            esc_items = data.get("escalations") or []
            idx = 0
            for esc in esc_items:
                if current + idx >= target_per_course:
                    break
                idx += 1
                status = esc.get("status") or next(status_cycle)
                week = int(esc.get("week") or idx)
                submitted_at = ts(max(0, (14 - week) * 7 + 2))
                escalations.append_request(
                    {
                        "question_id": esc.get("question_id") or f"{cid}_demo_escalation_{current + idx}",
                        "question": esc.get("question") or f"Demo escalation #{current + idx} for {cid}",
                        "student_name": esc.get("student_name") or f"Demo Student {current + idx}",
                        "student_email": esc.get("student_email") or f"student{current+idx:02d}@example.edu",
                        "course_id": cid,
                        "submitted_at": submitted_at,
                        "status": status,
                        "notes": esc.get("notes") or ("Awaiting follow-up" if status in ("contacted", "in_process") else ""),
                        "delivered": status in ("contacted", "in_process", "resolved"),
                    }
                )

            for idx in range(current + 1, target_per_course + 1):
                status = next(status_cycle)
                escalations.append_request(
                    {
                        "question_id": f"{cid}_demo_escalation_{idx}",
                        "question": f"Demo escalation #{idx} for {cid}: I have a question about assignment {idx}.",
                        "student_name": f"Demo Student {idx}",
                        "student_email": f"student{idx:02d}@example.edu",
                        "course_id": cid,
                        "submitted_at": utc_timestamp(),
                        "status": status,
                        "notes": "Awaiting follow-up" if status in ("contacted", "in_process") else "",
                        "delivered": status in ("contacted", "in_process", "resolved"),
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
