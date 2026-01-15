"""Shared API dependencies.

Provides dependency injection functions used across API routes,
including course resolution and validation.
"""

from __future__ import annotations

from fastapi import HTTPException

from ..services import courses


def resolve_course(course_id: str | None) -> dict[str, str | None]:
    """Resolve and validate a course identifier.

    Args:
        course_id: The course ID to resolve, or None for the default.

    Returns:
        The course record dictionary.

    Raises:
        HTTPException: If no courses are configured or the course is not found.
    """
    available = courses.load_courses()
    if not available:
        raise HTTPException(
            status_code=400,
            detail="No courses configured. Seed storage/courses.json.",
        )

    if not course_id:
        default_course = courses.get_default_course()
        if default_course:
            return default_course
        raise HTTPException(status_code=400, detail="course_id is required")

    course = courses.get_course(course_id)
    if course:
        return course

    raise HTTPException(
        status_code=404,
        detail="Course not found. Check storage/courses.json.",
    )
