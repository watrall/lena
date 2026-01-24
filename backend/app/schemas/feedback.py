from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from .chat import Citation


class FeedbackRequest(BaseModel):
    """Request payload for the /feedback endpoint."""

    question_id: str = Field(..., max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    helpful: bool
    comment: Optional[str] = Field(default=None, max_length=2000)
    question: Optional[str] = Field(default=None, max_length=2000)
    answer: Optional[str] = Field(default=None, max_length=10000)
    citations: Optional[List[Citation]] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    course_id: Optional[str] = Field(
        default=None,
        max_length=64,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Course identifier. Required.",
    )

    @field_validator("comment", "question", "answer", mode="before")
    @classmethod
    def strip_strings(cls, value: Optional[str]) -> Optional[str]:
        """Strip leading/trailing whitespace from string fields."""
        return value.strip() if isinstance(value, str) else value


class FeedbackResponse(BaseModel):
    ok: bool
    review_enqueued: bool = False


class EscalationRequest(BaseModel):
    """Request payload for escalation to instructor."""

    question_id: str = Field(..., max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    question: str = Field(..., min_length=1, max_length=2000)
    student_name: str = Field(..., min_length=1, max_length=200)
    student_email: str = Field(..., max_length=320)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    escalation_reason: Optional[str] = Field(default=None, max_length=64)
    course_id: str = Field(..., max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")

    @field_validator("student_email")
    @classmethod
    def validate_student_email(cls, value: str) -> str:
        email = value.strip()
        if "@" not in email or "." not in email.split("@")[-1]:
            raise ValueError("student_email must be a valid email address")
        return email


class EscalationResponse(BaseModel):
    ok: bool
