from __future__ import annotations

import re
from typing import List, Optional

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
    """A source citation for a generated answer."""

    title: str = Field(..., description="Document or section title.")
    section: Optional[str] = Field(default=None, description="Section heading within the document.")
    source_path: str = Field(..., description="Relative path to the source file.")


class AskResponse(BaseModel):
    """Response payload from the /ask endpoint."""

    question_id: str = Field(..., description="Unique identifier for this Q&A interaction.")
    answer: str = Field(..., description="Generated or extracted answer text.")
    citations: List[Citation] = Field(default_factory=list, description="Sources supporting the answer.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence score (0-1).")
    escalation_suggested: bool = Field(..., description="Whether instructor follow-up is recommended.")
