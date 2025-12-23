from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

from .chat import Citation


class FeedbackRequest(BaseModel):
    question_id: str
    helpful: bool
    comment: Optional[str] = None
    question: Optional[str] = None
    answer: Optional[str] = None
    citations: Optional[List[Citation]] = None
    confidence: Optional[float] = None
    course_id: Optional[str] = Field(default=None, description="Course identifier. Required.")


class FeedbackResponse(BaseModel):
    ok: bool
    review_enqueued: bool = False


class EscalationRequest(BaseModel):
    question_id: str
    question: str
    student_name: str
    student_email: EmailStr
    course_id: str


class EscalationResponse(BaseModel):
    ok: bool
