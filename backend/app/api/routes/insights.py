"""Analytics insights endpoint for the instructor dashboard."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ...schemas.insights import InsightsResponse
from ...services import analytics
from ..deps import resolve_course
from ..deps import require_instructor

router = APIRouter(tags=["insights"])


@router.get("/insights", response_model=InsightsResponse)
def get_insights(
    _: dict = Depends(require_instructor),
    course_id: str = Query(..., description="Course identifier"),
) -> InsightsResponse:
    """Return analytics insights for a course."""
    course = resolve_course(course_id)
    summary = analytics.summarize(course_id=course["id"])
    return InsightsResponse(**summary)
