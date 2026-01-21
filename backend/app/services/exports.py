"""Export utilities for analytics and raw pilot data.

Exports are intended for low-friction analysis workflows (pandas, R, Excel).
They support course-scoped and all-course downloads, JSON/CSV formats, and
optional inclusion of PII (explicit opt-in only).
"""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Iterable, Literal, Mapping
from zoneinfo import ZoneInfo

from . import courses
from .crypto import decrypt_pii
from .storage import read_json, storage_path
from ..settings import settings

ExportFormat = Literal["json", "csv"]
RangeKind = Literal["7d", "30d", "custom", "all"]


@dataclass(frozen=True)
class DateRange:
    start: date | None
    end: date | None

    def contains(self, when: datetime | None, tz: ZoneInfo) -> bool:
        if self.start is None or self.end is None:
            return True
        if when is None:
            return False
        local_day = when.astimezone(tz).date()
        return self.start <= local_day <= self.end


def resolve_timezone(tz_name: str | None) -> ZoneInfo:
    if not tz_name:
        return datetime.now().astimezone().tzinfo or ZoneInfo("UTC")
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return datetime.now().astimezone().tzinfo or ZoneInfo("UTC")


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def resolve_range(kind: RangeKind, tz: ZoneInfo, start_date: str | None, end_date: str | None) -> DateRange:
    if kind == "all":
        return DateRange(None, None)

    today = datetime.now(tz).date()
    if kind == "7d":
        return DateRange(today - timedelta(days=6), today)
    if kind == "30d":
        return DateRange(today - timedelta(days=29), today)

    start = parse_date(start_date)
    end = parse_date(end_date) or start
    if start is None or end is None:
        raise ValueError("custom range requires start_date (YYYY-MM-DD)")
    if end < start:
        raise ValueError("end_date must be on/after start_date")
    return DateRange(start, end)


def _parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _read_jsonl_limited(name: str) -> list[dict[str, Any]]:
    path = storage_path(name)
    if not path.exists():
        return []

    try:
        if path.stat().st_size > settings.export_max_file_bytes:
            raise ValueError(f"{name} exceeds export_max_file_bytes")
    except OSError:
        # If we can't stat, fall back to read attempt with record cap.
        pass

    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
            if len(records) >= settings.export_max_records:
                break
    return records


def _filter_by_course_and_range(
    records: Iterable[dict[str, Any]],
    *,
    course_id: str,
    date_range: DateRange,
    tz: ZoneInfo,
    timestamp_fields: tuple[str, ...],
) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    for record in records:
        if record.get("course_id") != course_id:
            continue
        when = None
        for field in timestamp_fields:
            when = _parse_timestamp(record.get(field))
            if when is not None:
                break
        if date_range.contains(when, tz):
            filtered.append(record)
    return filtered


def _redact_escalation_pii(record: dict[str, Any]) -> dict[str, Any]:
    next_record = {**record}
    next_record["student"] = None
    next_record["student_email"] = None
    return next_record


def load_raw_component(
    component: str,
    *,
    course_id: str,
    date_range: DateRange,
    tz: ZoneInfo,
    include_pii: bool,
) -> list[dict[str, Any]] | dict[str, Any]:
    if component == "raw_interactions":
        return _filter_by_course_and_range(
            _read_jsonl_limited("interactions.jsonl"),
            course_id=course_id,
            date_range=date_range,
            tz=tz,
            timestamp_fields=("timestamp",),
        )
    if component == "raw_answers":
        return _filter_by_course_and_range(
            _read_jsonl_limited("answers.jsonl"),
            course_id=course_id,
            date_range=date_range,
            tz=tz,
            timestamp_fields=("timestamp",),
        )
    if component == "raw_review_queue":
        return _filter_by_course_and_range(
            _read_jsonl_limited("review_queue.jsonl"),
            course_id=course_id,
            date_range=date_range,
            tz=tz,
            timestamp_fields=("submitted_at",),
        )
    if component == "raw_faq":
        entries = read_json(storage_path("faq.json"), default=[])
        if not isinstance(entries, list):
            return []
        filtered = []
        for entry in entries:
            if entry.get("course_id") != course_id:
                continue
            when = _parse_timestamp(entry.get("updated_at"))
            if date_range.start is not None and when is None:
                continue
            if date_range.contains(when, tz):
                filtered.append(entry)
        return filtered
    if component == "raw_escalations":
        entries = _filter_by_course_and_range(
            _read_jsonl_limited("escalations.jsonl"),
            course_id=course_id,
            date_range=date_range,
            tz=tz,
            timestamp_fields=("submitted_at",),
        )
        if not include_pii:
            return [_redact_escalation_pii(entry) for entry in entries]
        return [
            {
                **entry,
                "student": decrypt_pii(str(entry.get("student", ""))) if "student" in entry else None,
                "student_email": decrypt_pii(str(entry.get("student_email", "")))
                if "student_email" in entry
                else None,
            }
            for entry in entries
        ]
    raise KeyError(f"Unknown component: {component}")


def compute_insights_components(
    *,
    course_id: str,
    date_range: DateRange,
    tz: ZoneInfo,
    include_pii: bool,
) -> dict[str, Any]:
    interactions = load_raw_component(
        "raw_interactions",
        course_id=course_id,
        date_range=date_range,
        tz=tz,
        include_pii=False,
    )
    if not isinstance(interactions, list):
        interactions = []

    totals_questions = 0
    confidence_sum = 0.0
    confidence_count = 0
    helpful_total = 0
    feedback_total = 0
    question_counts: dict[str, int] = {}
    daily_volume: dict[str, int] = {}
    confidence_daily: dict[str, dict[str, float | int]] = {}
    feedback_by_question: dict[str, dict[str, int]] = {}

    for event in interactions:
        event_type = event.get("type")
        event_ts = _parse_timestamp(event.get("timestamp"))
        if event_ts is None:
            continue
        day_key = event_ts.astimezone(tz).date().isoformat()

        if event_type == "ask":
            totals_questions += 1
            daily_volume[day_key] = daily_volume.get(day_key, 0) + 1
            confidence = event.get("confidence")
            if isinstance(confidence, (int, float)):
                confidence_sum += float(confidence)
                confidence_count += 1
                bucket = confidence_daily.setdefault(day_key, {"sum": 0.0, "count": 0})
                bucket["sum"] = float(bucket["sum"]) + float(confidence)
                bucket["count"] = int(bucket["count"]) + 1
            question = event.get("question")
            if question:
                question_counts[str(question)] = question_counts.get(str(question), 0) + 1
        elif event_type == "feedback":
            feedback_total += 1
            if bool(event.get("helpful")):
                helpful_total += 1
            question = event.get("question")
            if question:
                stats = feedback_by_question.setdefault(str(question), {"helpful": 0, "total": 0})
                stats["total"] += 1
                if bool(event.get("helpful")):
                    stats["helpful"] += 1

    avg_confidence = confidence_sum / confidence_count if confidence_count else 0.0
    helpful_rate = helpful_total / feedback_total if feedback_total else 0.0

    top_questions = sorted(
        ({"label": label, "count": count} for label, count in question_counts.items()),
        key=lambda item: item["count"],
        reverse=True,
    )[:5]

    escalations = load_raw_component(
        "raw_escalations",
        course_id=course_id,
        date_range=date_range,
        tz=tz,
        include_pii=include_pii,
    )
    if not isinstance(escalations, list):
        escalations = []

    pain_points = []
    for question, stats in feedback_by_question.items():
        total = stats.get("total", 0)
        if not total:
            continue
        helpful_share = stats.get("helpful", 0) / total
        change = round(0.5 - helpful_share, 2)
        pain_points.append({"label": question, "change": change})
    pain_points.sort(key=lambda entry: entry["change"], reverse=True)
    pain_points = pain_points[:5]

    # Ensure continuous date series for charts (last 30 days in selected tz).
    last_30_days = [
        (datetime.now(tz).date() - timedelta(days=offset)).isoformat()
        for offset in reversed(range(30))
    ]
    daily_volume_rows = [{"date": day, "count": daily_volume.get(day, 0)} for day in last_30_days]
    confidence_rows = []
    for day in last_30_days:
        bucket = confidence_daily.get(day)
        if bucket and bucket.get("count"):
            confidence_rows.append({"date": day, "confidence": round(float(bucket["sum"]) / int(bucket["count"]), 2)})
        else:
            confidence_rows.append({"date": day, "confidence": 0.0})

    insights_escalations = [
        {
            "question": entry.get("question"),
            "student": entry.get("student"),
            "submitted_at": entry.get("submitted_at"),
            "delivered": bool(entry.get("delivered", False)),
        }
        for entry in escalations
    ]

    return {
        "insights_totals": {
            "questions": totals_questions,
            "helpful_rate": round(helpful_rate, 2),
            "average_confidence": round(avg_confidence, 2),
            "escalations": len(insights_escalations),
        },
        "insights_top_questions": top_questions,
        "insights_daily_volume": daily_volume_rows,
        "insights_confidence_trend": confidence_rows,
        "insights_pain_points": pain_points,
        "insights_escalations": insights_escalations,
    }


def list_available_courses(course_id: str) -> list[dict[str, str | None]]:
    if course_id == "all":
        return courses.load_courses()
    course = courses.get_course(course_id)
    if course is None:
        raise ValueError("Unknown course_id")
    return [course]


def component_to_filename(component: str, fmt: ExportFormat) -> str:
    base = component.replace("_", "-")
    return f"{base}.{fmt}"


def _json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, indent=2, ensure_ascii=True).encode("utf-8")


def _csv_bytes(records: Any) -> bytes:
    output = io.StringIO()
    writer: csv.DictWriter | None = None

    if isinstance(records, Mapping):
        rows = [records]
    elif isinstance(records, list):
        rows = records
    else:
        rows = [{"value": records}]

    # Normalize values to scalars for CSV.
    normalized: list[dict[str, Any]] = []
    fieldnames: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            row = {"value": row}
        next_row = {}
        for key, value in row.items():
            if isinstance(value, (dict, list)):
                next_row[key] = json.dumps(value, ensure_ascii=True)
            else:
                next_row[key] = value
        normalized.append(next_row)
        fieldnames.update(next_row.keys())

    ordered_fields = sorted(fieldnames)
    writer = csv.DictWriter(output, fieldnames=ordered_fields)
    writer.writeheader()
    for row in normalized:
        writer.writerow({key: row.get(key) for key in ordered_fields})
    return output.getvalue().encode("utf-8")


def component_bytes(component_payload: Any, fmt: ExportFormat) -> bytes:
    if fmt == "json":
        return _json_bytes(component_payload)
    if fmt == "csv":
        return _csv_bytes(component_payload)
    raise ValueError("Unsupported export format")
