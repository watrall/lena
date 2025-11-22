from typing import Optional
from pydantic import BaseModel

class InsightsTotals(BaseModel):
    questions: int
    helpful_rate: float
    average_confidence: float
    escalations: int

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
    top_questions: list[TopQuestion]
    daily_volume: list[DailyVolumePoint]
    confidence_trend: list[ConfidencePoint]
    escalations: list[EscalationRow]
    pain_points: list[PainPoint]
    last_updated: str
