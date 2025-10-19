from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List

from ..settings import settings
from .storage import append_jsonl, read_jsonl, storage_path


@dataclass
class InteractionEvent:
    type: str
    question_id: str
    timestamp: str
    confidence: float | None = None
    helpful: bool | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "InteractionEvent":
        return cls(
            type=data.get("type", ""),
            question_id=data.get("question_id", ""),
            timestamp=data.get("timestamp", ""),
            confidence=data.get("confidence"),
            helpful=data.get("helpful"),
        )


def log_event(event: dict) -> None:
    append_jsonl(storage_path("interactions.jsonl"), event)


def summarize() -> dict[str, float | int]:
    events = [InteractionEvent.from_dict(item) for item in read_jsonl(storage_path("interactions.jsonl"))]
    asks = [event for event in events if event.type == "ask"]
    feedback_events = [event for event in events if event.type == "feedback"]

    total_questions = len(asks)
    avg_confidence = (
        sum(event.confidence or 0.0 for event in asks) / total_questions if total_questions else 0.0
    )

    helpful_votes = sum(1 for event in feedback_events if event.helpful)
    total_feedback = len(feedback_events)
    helpful_rate = helpful_votes / total_feedback if total_feedback else 0.0

    return {
        "total_questions": total_questions,
        "average_confidence": round(avg_confidence, 2),
        "helpful_rate": round(helpful_rate, 2),
        "total_feedback": total_feedback,
        "last_updated": datetime.utcnow().isoformat() + "Z",
    }
