from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from . import escalations as escalation_service
from .storage import append_jsonl, read_jsonl, storage_path


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


def _parse_timestamp(value: str) -> datetime | None:
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def summarize(course_id: str | None = None) -> dict:
    events = [InteractionEvent.from_dict(item) for item in read_jsonl(storage_path("interactions.jsonl"))]
    if course_id:
        events = [event for event in events if event.course_id == course_id]

    asks = [event for event in events if event.type == "ask"]
    feedback_events = [event for event in events if event.type == "feedback"]

    total_questions = len(asks)
    avg_confidence = (
        sum(event.confidence or 0.0 for event in asks) / total_questions if total_questions else 0.0
    )

    helpful_votes = sum(1 for event in feedback_events if event.helpful)
    total_feedback = len(feedback_events)
    helpful_rate = helpful_votes / total_feedback if total_feedback else 0.0

    question_counter = Counter(event.question for event in asks if event.question)
    top_questions = [
        {"label": label, "count": count}
        for label, count in question_counter.most_common(5)
    ]

    daily_volume_map: dict[str, int] = defaultdict(int)
    confidence_map: dict[str, list[float]] = defaultdict(list)
    for event in asks:
        parsed = _parse_timestamp(event.timestamp)
        if not parsed:
            continue
        date_key = parsed.date().isoformat()
        daily_volume_map[date_key] += 1
        if event.confidence is not None:
            confidence_map[date_key].append(event.confidence)

    last_30_days = [
        (datetime.utcnow().date() - timedelta(days=offset)).isoformat()
        for offset in reversed(range(30))
    ]
    daily_volume = [
        {"date": key, "count": daily_volume_map.get(key, 0)}
        for key in last_30_days
    ]
    confidence_trend = [
        {
            "date": key,
            "confidence": round(sum(values) / len(values), 2) if values else 0.0,
        }
        for key in last_30_days
        if key in confidence_map or daily_volume_map.get(key)
    ]

    feedback_by_question: dict[str, dict[str, int]] = defaultdict(lambda: {"helpful": 0, "total": 0})
    for event in feedback_events:
        if not event.question:
            continue
        bucket = feedback_by_question[event.question]
        bucket["total"] += 1
        if event.helpful:
            bucket["helpful"] += 1
    pain_points = []
    for question, stats in feedback_by_question.items():
        if stats["total"] == 0:
            continue
        helpful_share = stats["helpful"] / stats["total"]
        change = round(0.5 - helpful_share, 2)
        pain_points.append({"label": question, "change": change})
    pain_points.sort(key=lambda entry: entry["change"], reverse=True)
    pain_points = pain_points[:5]

    escalation_rows = escalation_service.list_requests(course_id)
    escalations_total = len(escalation_rows)

    timestamps = [
        _parse_timestamp(event.timestamp)
        for event in events
        if event.timestamp
    ]
    last_updated = max([ts for ts in timestamps if ts], default=datetime.now(timezone.utc))

    return {
        "totals": {
            "questions": total_questions,
            "helpful_rate": round(helpful_rate, 2),
            "average_confidence": round(avg_confidence, 2),
            "escalations": escalations_total,
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
        "last_updated": last_updated.isoformat().replace("+00:00", "Z"),
    }
