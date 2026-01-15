"""Analytics insights endpoint for the instructor dashboard."""

from __future__ import annotations

from fastapi import APIRouter, Query

from ...schemas.insights import InsightsResponse
from ...services import analytics
from ..deps import resolve_course

router = APIRouter(tags=["insights"])


@router.get("/insights", response_model=InsightsResponse)
def get_insights(
    course_id: str = Query(..., description="Course identifier"),
) -> InsightsResponse:
    """Retrieve analytics insights for a specific course.

    Args:
        course_id: The course to retrieve insights for.

    Returns:
        Aggregated metrics including question volume, confidence trends,
        and escalation data.
    """
    course = resolve_course(course_id)
    summary = analytics.summarize(course_id=course["id"])
    return InsightsResponse(**summary)
