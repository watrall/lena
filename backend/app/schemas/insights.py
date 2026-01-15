from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class InsightsTotals(BaseModel):
    """Aggregate metrics for a course."""

    questions: int = Field(..., description="Total questions asked.")
    helpful_rate: float = Field(..., ge=0.0, le=1.0, description="Proportion of helpful feedback.")
    average_confidence: float = Field(..., ge=0.0, le=1.0, description="Mean confidence score.")
    escalations: int = Field(..., description="Number of escalation requests.")


class TopQuestion(BaseModel):
    label: str
    count: int


class DailyVolumePoint(BaseModel):
    date: str
    count: int


class ConfidencePoint(BaseModel):
    date: str
    confidence: float


class EscalationRow(BaseModel):
    question: Optional[str]
    student: Optional[str]
    submitted_at: Optional[str]
    delivered: bool


class PainPoint(BaseModel):
    label: str
    change: float


class InsightsResponse(BaseModel):
    totals: InsightsTotals
    top_questions: List[TopQuestion]
    daily_volume: List[DailyVolumePoint]
    confidence_trend: List[ConfidencePoint]
    escalations: List[EscalationRow]
    pain_points: List[PainPoint]
    last_updated: str
