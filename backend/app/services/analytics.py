from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from . import escalations as escalation_service
from .storage import append_jsonl, read_json, read_jsonl, storage_path, write_json

SUMMARY_FILENAME = "analytics_summary.json"
DEFAULT_COURSE_KEY = "__default__"


@dataclass
class InteractionEvent:
    type: str
    question_id: str
    timestamp: str
    confidence: float | None = None
    helpful: bool | None = None
    course_id: str | None = None
    question: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "InteractionEvent":
        return cls(
            type=data.get("type", ""),
            question_id=data.get("question_id", ""),
            timestamp=data.get("timestamp", ""),
            confidence=data.get("confidence"),
            helpful=data.get("helpful"),
            course_id=data.get("course_id"),
            question=data.get("question"),
        )


def log_event(event: dict) -> None:
    append_jsonl(storage_path("interactions.jsonl"), event)
    _apply_event_to_summary(event)


def _course_key(course_id: str | None) -> str:
    return course_id or DEFAULT_COURSE_KEY


def _empty_course_state() -> dict[str, Any]:
    return {
        "questions": 0,
        "confidence_sum": 0.0,
        "confidence_count": 0,
        "helpful_total": 0,
        "feedback_total": 0,
        "question_counts": {},
        "daily_volume": {},
        "confidence_daily": {},
        "feedback_by_question": {},
        "last_updated": None,
    }


def _load_summary() -> dict[str, Any]:
    return read_json(storage_path(SUMMARY_FILENAME), default={})


def _save_summary(summary: dict[str, Any]) -> None:
    write_json(storage_path(SUMMARY_FILENAME), summary)


def _apply_event_to_summary(event: dict) -> None:
    summary = _load_summary()
    key = _course_key(event.get("course_id"))
    state = summary.setdefault(key, _empty_course_state())
    event_ts = _parse_timestamp(event.get("timestamp")) or datetime.now(timezone.utc)
    date_key = event_ts.date().isoformat()

    if event.get("type") == "ask":
        state["questions"] += 1
        confidence = event.get("confidence")
        if isinstance(confidence, (int, float)):
            state["confidence_sum"] += float(confidence)
            state["confidence_count"] += 1
            day_bucket = state["confidence_daily"].setdefault(date_key, {"sum": 0.0, "count": 0})
            day_bucket["sum"] += float(confidence)
            day_bucket["count"] += 1
        if event.get("question"):
            counter = state["question_counts"]
            counter[event["question"]] = counter.get(event["question"], 0) + 1
        daily = state["daily_volume"]
        daily[date_key] = daily.get(date_key, 0) + 1
    elif event.get("type") == "feedback":
        state["feedback_total"] += 1
        if event.get("helpful"):
            state["helpful_total"] += 1
        question = event.get("question")
        if question:
            stats = state["feedback_by_question"].setdefault(question, {"helpful": 0, "total": 0})
            stats["total"] += 1
            if event.get("helpful"):
                stats["helpful"] += 1

    state["last_updated"] = event_ts.isoformat().replace("+00:00", "Z")
    _trim_history(state["daily_volume"])
    _trim_history(state["confidence_daily"])
    _save_summary(summary)


def _trim_history(mapping: dict[str, Any], max_days: int = 90) -> None:
    cutoff = datetime.utcnow().date() - timedelta(days=max_days)
    drop_keys = []
    for key in mapping.keys():
        try:
            key_date = datetime.fromisoformat(key).date()
        except ValueError:
            continue
        if key_date < cutoff:
            drop_keys.append(key)
    for key in drop_keys:
        mapping.pop(key, None)


def _ensure_summary_synced() -> None:
    interactions_path = storage_path("interactions.jsonl")
    summary_path = storage_path(SUMMARY_FILENAME)
    if not interactions_path.exists():
        if not summary_path.exists():
            _save_summary({})
        return
    if not summary_path.exists() or summary_path.stat().st_mtime < interactions_path.stat().st_mtime:
        _save_summary({})
        for event in read_jsonl(interactions_path):
            _apply_event_to_summary(event)


def summarize(course_id: str | None = None) -> dict[str, Any]:
    _ensure_summary_synced()
    summary = _load_summary()
    key = _course_key(course_id)
    state = summary.get(key, _empty_course_state())

    total_questions = state["questions"]
    avg_confidence = (
        state["confidence_sum"] / state["confidence_count"] if state["confidence_count"] else 0.0
    )
    helpful_total = state["helpful_total"]
    feedback_total = state["feedback_total"]
    helpful_rate = helpful_total / feedback_total if feedback_total else 0.0

    question_counter = Counter(state["question_counts"])
    top_questions = [
        {"label": label, "count": count}
        for label, count in question_counter.most_common(5)
    ]

    last_30_days = [
        (datetime.utcnow().date() - timedelta(days=offset)).isoformat()
        for offset in reversed(range(30))
    ]
    daily_volume = [
        {"date": day, "count": state["daily_volume"].get(day, 0)}
        for day in last_30_days
    ]
    confidence_trend = []
    for day in last_30_days:
        bucket = state["confidence_daily"].get(day)
        if bucket and bucket.get("count"):
            confidence_trend.append(
                {"date": day, "confidence": round(bucket["sum"] / bucket["count"], 2)}
            )
        else:
            confidence_trend.append({"date": day, "confidence": 0.0})

    pain_points = []
    for question, stats in state["feedback_by_question"].items():
        total = stats.get("total", 0)
        if not total:
            continue
        helpful_share = stats.get("helpful", 0) / total
        change = round(0.5 - helpful_share, 2)
        pain_points.append({"label": question, "change": change})
    pain_points.sort(key=lambda entry: entry["change"], reverse=True)
    pain_points = pain_points[:5]

    escalation_rows = escalation_service.list_requests(course_id)
    last_updated = state["last_updated"] or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    return {
        "totals": {
            "questions": total_questions,
            "helpful_rate": round(helpful_rate, 2),
            "average_confidence": round(avg_confidence, 2),
            "escalations": len(escalation_rows),
        },
        "top_questions": top_questions,
        "daily_volume": daily_volume,
        "confidence_trend": confidence_trend,
        "escalations": [
            {
                "question": entry.get("question"),
                "student": entry.get("student"),
                "submitted_at": entry.get("submitted_at"),
                "delivered": bool(entry.get("delivered", False)),
            }
            for entry in escalation_rows
        ],
        "pain_points": pain_points,
        "last_updated": last_updated,
    }


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None
