"""Feedback and escalation endpoints."""

from fastapi import APIRouter, Body, HTTPException, Request

from ...schemas.feedback import (
    EscalationRequest,
    EscalationResponse,
    FeedbackRequest,
    FeedbackResponse,
)
from ...limiting import limiter
from ...services import analytics, escalations, questions, review
from ...services.storage import utc_timestamp
from ..deps import resolve_course

router = APIRouter(tags=["feedback"])


@router.post("/feedback", response_model=FeedbackResponse)
@limiter.limit("30/minute")
async def submit_feedback(request: Request, payload: FeedbackRequest = Body(...)) -> FeedbackResponse:
    """Record learner feedback; unhelpful answers are queued for review."""
    if not payload.course_id:
        raise HTTPException(status_code=400, detail="course_id is required")

    course = resolve_course(payload.course_id)
    course_id = course["id"]

    analytics.log_event(
        {
            "type": "feedback",
            "question_id": payload.question_id,
            "helpful": payload.helpful,
            "confidence": payload.confidence,
            "question": payload.question,
            "course_id": course_id,
            "timestamp": utc_timestamp(),
        }
    )

    review_enqueued = False
    if not payload.helpful:
        recorded = questions.lookup_answer(payload.question_id)
        question_text = (recorded or {}).get("question") or payload.question
        answer_text = (recorded or {}).get("answer") or payload.answer
        recorded_citations = (recorded or {}).get("citations")
        citations_payload = recorded_citations or [
            c.model_dump() for c in payload.citations or []
        ]
        review.append_review_item(
            {
                "question_id": payload.question_id,
                "question": question_text,
                "answer": answer_text,
                "citations": citations_payload,
                "comment": payload.comment,
                "helpful": payload.helpful,
                "course_id": course_id,
            }
        )
        review_enqueued = True

    return FeedbackResponse(ok=True, review_enqueued=review_enqueued)


@router.post("/escalations/request", response_model=EscalationResponse)
@limiter.limit("10/minute")
async def request_escalation(request: Request, payload: EscalationRequest = Body(...)) -> EscalationResponse:
    """Submit an escalation request for instructor follow-up."""
    course = resolve_course(payload.course_id)
    record = escalations.append_request(
        {
            "question_id": payload.question_id,
            "question": payload.question,
            "student_name": payload.student_name,
            "student_email": payload.student_email,
            "course_id": course["id"],
        }
    )
    analytics.log_event(
        {
            "type": "escalation",
            "question_id": payload.question_id,
            "question": payload.question,
            "course_id": course["id"],
            "timestamp": record["submitted_at"],
        }
    )
    return EscalationResponse(ok=True)
