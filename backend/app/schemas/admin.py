from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from .chat import Citation


class FAQEntry(BaseModel):
    """A curated FAQ entry promoted from the review queue."""

    question: str
    answer: str
    source_path: Optional[str] = None
    updated_at: Optional[str] = None
    course_id: Optional[str] = None


class ReviewItem(BaseModel):
    """An item in the instructor review queue."""

    id: str
    question_id: str
    question: Optional[str] = None
    answer: Optional[str] = None
    citations: Optional[List[Citation]] = None
    comment: Optional[str] = None
    helpful: Optional[bool] = None
    submitted_at: str
    course_id: Optional[str] = None


class PromoteRequest(BaseModel):
    """Request payload for promoting a review item to the FAQ."""

    queue_id: str = Field(..., max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    answer: Optional[str] = Field(default=None, max_length=10000)
    source_path: Optional[str] = Field(default=None, max_length=500)
    course_id: str = Field(..., max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
