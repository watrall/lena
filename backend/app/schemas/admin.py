from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel

from .chat import Citation


class FAQEntry(BaseModel):
    question: str
    answer: str
    source_path: Optional[str] = None
    updated_at: Optional[str] = None
    course_id: Optional[str] = None


class ReviewItem(BaseModel):
    id: str
    question_id: str
    question: Optional[str] = None
    answer: Optional[str] = None
    citations: Optional[List[Citation]] = None
    comment: Optional[str] = None
    helpful: Optional[bool] = None
    submitted_at: str


class PromoteRequest(BaseModel):
    queue_id: str
    answer: Optional[str] = None
    source_path: Optional[str] = None
    course_id: str
