"""Course listing endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from ...schemas.courses import CourseSummary
from ...services import courses

router = APIRouter(tags=["courses"])


@router.get("/courses", response_model=list[CourseSummary])
def list_courses_endpoint() -> list[CourseSummary]:
    """List all available courses.

    Returns:
        A list of course summaries with id, name, code, and term.
    """
    return [CourseSummary(**entry) for entry in courses.load_courses()]
