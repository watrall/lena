"""Course listing endpoint."""

from __future__ import annotations

from fastapi import APIRouter
from typing import List

from ...schemas.courses import CourseSummary
from ...services import courses

router = APIRouter(tags=["courses"])


@router.get("/courses", response_model=List[CourseSummary])
def list_courses_endpoint() -> List[CourseSummary]:
    """List all available courses."""
    return [CourseSummary(**entry) for entry in courses.load_courses()]
