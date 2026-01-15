from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class AskRequest(BaseModel):
    """Request payload for the /ask endpoint."""

    question: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Learner or staff question (3-2000 characters).",
    )
    course_id: Optional[str] = Field(
        default=None,
        max_length=64,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Course context identifier. Defaults to the first available course.",
    )

    @field_validator("question")
    @classmethod
    def sanitize_question(cls, value: str) -> str:
        """Normalize whitespace and strip control characters."""
        sanitized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", value)
        return " ".join(sanitized.split())


class Citation(BaseModel):
    title: str
    section: Optional[str]
    source_path: str


class AskResponse(BaseModel):
    question_id: str
    answer: str
    citations: list[Citation]
    confidence: float
    escalation_suggested: bool
