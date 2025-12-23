from __future__ import annotations

from fastapi import APIRouter

from ...services import courses
from ...schemas.courses import CourseSummary

router = APIRouter()

@router.get("/courses", response_model=list[CourseSummary])
def list_courses_endpoint() -> list[CourseSummary]:
    return [CourseSummary(**entry) for entry in courses.load_courses()]
