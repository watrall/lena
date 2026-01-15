"""Course-related Pydantic schemas."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CourseSummary(BaseModel):
    """Summary representation of a course for listings and selection."""

    id: str = Field(..., description="Unique course identifier.")
    name: str = Field(..., description="Display name for the course.")
    code: Optional[str] = Field(default=None, description="Course code (e.g., ANTH 101).")
    term: Optional[str] = Field(default=None, description="Academic term (e.g., Fall 2024).")
