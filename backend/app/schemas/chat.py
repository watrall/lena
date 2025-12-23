from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, description="Learner or staff question.")
    course_id: Optional[str] = Field(
        default=None, description="Course context identifier. Defaults to the first available course."
    )


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
