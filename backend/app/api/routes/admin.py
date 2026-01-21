"""Admin endpoints for FAQ management and review queue.

Provides instructor-facing endpoints for reviewing low-confidence answers,
promoting vetted responses to the FAQ, and managing the review queue.
"""

from fastapi import APIRouter, Body, HTTPException, Query, Request

from ...schemas.admin import FAQEntry, PromoteRequest, ReviewItem
from ...limiting import limiter
from ...services import analytics
from ...services import review
from ...services.storage import utc_timestamp
from ...settings import settings
from ..deps import resolve_course

router = APIRouter(tags=["admin"])


@router.get("/faq", response_model=list[FAQEntry])
def get_faq(
    course_id: str = Query(..., description="Course identifier"),
) -> list[FAQEntry]:
    """Retrieve FAQ entries for a course.

    Args:
        course_id: The course to retrieve FAQs for.

    Returns:
        A list of curated FAQ entries.
    """
    course = resolve_course(course_id)
    return [FAQEntry(**entry) for entry in review.load_faq(course_id=course["id"])]


@router.get("/admin/review", response_model=list[ReviewItem])
@limiter.limit("30/minute")
async def get_review_queue(
    request: Request,
    course_id: str = Query(..., description="Course identifier"),
) -> list[ReviewItem]:
    """Retrieve the instructor review queue for a course.

    Args:
        course_id: The course to retrieve review items for.

    Returns:
        A list of items awaiting instructor review.
    """
    if not settings.enable_admin_endpoints:
        raise HTTPException(status_code=404, detail="Not found")
    analytics.log_event(
        {
            "type": "admin_review_list",
            "question_id": "n/a",
            "course_id": course_id,
            "timestamp": utc_timestamp(),
        }
    )
    return [
        ReviewItem(**entry)
        for entry in review.list_review_queue()
        if entry.get("course_id") == course_id
    ]


@router.post("/admin/promote", response_model=FAQEntry)
@limiter.limit("10/minute")
async def promote_to_faq(request: Request, payload: PromoteRequest = Body(...)) -> FAQEntry:
    """Promote a review queue item to the FAQ.

    Args:
        payload: The promotion request with queue item ID and answer.

    Returns:
        The newly created FAQ entry.

    Raises:
        HTTPException: If the review item is not found or belongs to
            a different course.
    """
    if not settings.enable_admin_endpoints:
        raise HTTPException(status_code=404, detail="Not found")
    removed = review.remove_review_item(payload.queue_id)
    if removed is None:
        raise HTTPException(status_code=404, detail="Review item not found")

    queue_course_id = removed.get("course_id")
    if queue_course_id and queue_course_id != payload.course_id:
        raise HTTPException(
            status_code=400,
            detail="Review item belongs to a different course",
        )

    course = resolve_course(payload.course_id)
    faq_entries = review.load_faq()

    question_text = removed.get("question") or "Untitled FAQ"
    answer_text = payload.answer or removed.get("answer") or "No answer provided yet."

    faq_entry = {
        "question": question_text,
        "answer": answer_text,
        "source_path": payload.source_path or removed.get("source_path"),
        "updated_at": utc_timestamp(),
        "course_id": course["id"],
    }
    faq_entries.append(faq_entry)
    review.save_faq(faq_entries)
    analytics.log_event(
        {
            "type": "admin_promote",
            "question_id": str(payload.queue_id),
            "course_id": course["id"],
            "timestamp": utc_timestamp(),
        }
    )

    return FAQEntry(**faq_entry)
