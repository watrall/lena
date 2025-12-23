from __future__ import annotations

from fastapi import APIRouter, Query

from ...services import analytics
from ..deps import resolve_course
from ...schemas.insights import InsightsResponse

router = APIRouter()

@router.get("/insights", response_model=InsightsResponse)
def get_insights(course_id: str = Query(..., description="Course identifier")) -> InsightsResponse:
    course = resolve_course(course_id)
    summary = analytics.summarize(course_id=course["id"])
    return InsightsResponse(**summary)
