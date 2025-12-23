from __future__ import annotations

from fastapi import HTTPException

from ..services import courses


def resolve_course(course_id: str | None) -> dict[str, str | None]:
    available = courses.load_courses()
    if not available:
        raise HTTPException(status_code=400, detail="No courses configured. Seed storage/courses.json.")
    target_id = course_id
    if not target_id:
        default_course = courses.get_default_course()
        if default_course:
            return default_course
        raise HTTPException(status_code=400, detail="course_id is required")
    course = courses.get_course(target_id)
    if course:
        return course
    raise HTTPException(status_code=404, detail="Course not found. Check storage/courses.json.")
