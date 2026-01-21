"""Shared API dependencies."""

from __future__ import annotations

from fastapi import HTTPException, Request
from fastapi.security.utils import get_authorization_scheme_param

from ..services import courses
from ..services.instructor_auth import verify_token
from ..settings import settings


def resolve_course(course_id: str | None) -> dict[str, str | None]:
    """Resolve and validate a course identifier."""
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


def require_instructor(request: Request) -> dict:
    """Require a valid demo instructor bearer token."""
    if not settings.enable_instructor_auth:
        return {"sub": "disabled"}
    auth = request.headers.get("authorization") or ""
    scheme, param = get_authorization_scheme_param(auth)
    if scheme.lower() != "bearer" or not param:
        raise HTTPException(status_code=401, detail="Instructor authentication required")
    payload = verify_token(param)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload
