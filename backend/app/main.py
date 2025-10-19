from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel, Field

from .models.generate import generate_answer
from .rag.ingest import IngestResult, run_ingest
from .rag.retrieve import RetrievedChunk, retrieve
from .services import analytics, review, storage
from .settings import settings

app = FastAPI(title="LENA Backend", version="0.1.0")
router = APIRouter()

storage.ensure_storage()


@app.get("/healthz")
def healthcheck() -> dict[str, bool]:
    """Basic readiness probe for infrastructure integrations."""
    return {"ok": True}


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, description="Learner or staff question.")


class Citation(BaseModel):
    title: str
    section: str | None
    source_path: str


class AskResponse(BaseModel):
    question_id: str
    answer: str
    citations: list[Citation]
    confidence: float
    escalation_suggested: bool


class FeedbackRequest(BaseModel):
    question_id: str
    helpful: bool
    comment: str | None = None
    question: str | None = None
    answer: str | None = None
    citations: list[Citation] | None = None
    confidence: float | None = None


class FeedbackResponse(BaseModel):
    ok: bool
    review_enqueued: bool = False


class FAQEntry(BaseModel):
    question: str
    answer: str
    source_path: str | None = None
    updated_at: str | None = None


class ReviewItem(BaseModel):
    id: str
    question_id: str
    question: str | None = None
    answer: str | None = None
    citations: list[Citation] | None = None
    comment: str | None = None
    helpful: bool | None = None
    submitted_at: str


class PromoteRequest(BaseModel):
    queue_id: str
    answer: str | None = None
    source_path: str | None = None


class InsightsResponse(BaseModel):
    total_questions: int
    average_confidence: float
    helpful_rate: float
    total_feedback: int
    last_updated: str


@router.post("/ingest/run", response_model=IngestResult)
def ingest_run() -> IngestResult:
    try:
        return run_ingest()
    except Exception as exc:  # pragma: no cover - surfaced to clients
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/ask", response_model=AskResponse)
def ask_question(payload: AskRequest) -> AskResponse:
    chunks = retrieve(payload.question, top_k=settings.retrieval_top_k)
    answer = generate_answer(payload.question, chunks)
    citations = build_citations(chunks)
    confidence = compute_confidence(chunks)
    escalation = confidence < 0.55

    question_id = uuid4().hex
    analytics.log_event(
        {
            "type": "ask",
            "question_id": question_id,
            "question": payload.question,
            "confidence": confidence,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    )

    return AskResponse(
        question_id=question_id,
        answer=answer,
        citations=citations,
        confidence=confidence,
        escalation_suggested=escalation,
    )


@router.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(payload: FeedbackRequest) -> FeedbackResponse:
    analytics.log_event(
        {
            "type": "feedback",
            "question_id": payload.question_id,
            "helpful": payload.helpful,
            "confidence": payload.confidence,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    )

    review_enqueued = False
    if not payload.helpful:
        review.append_review_item(
            {
                "question_id": payload.question_id,
                "question": payload.question,
                "answer": payload.answer,
                "citations": [c.model_dump() for c in payload.citations or []],
                "comment": payload.comment,
                "helpful": payload.helpful,
            }
        )
        review_enqueued = True

    return FeedbackResponse(ok=True, review_enqueued=review_enqueued)


@router.get("/faq", response_model=list[FAQEntry])
def get_faq() -> list[FAQEntry]:
    return [FAQEntry(**entry) for entry in review.load_faq()]


@router.get("/admin/review", response_model=list[ReviewItem])
def get_review_queue() -> list[ReviewItem]:
    return [ReviewItem(**entry) for entry in review.list_review_queue()]


@router.post("/admin/promote", response_model=FAQEntry)
def promote_to_faq(payload: PromoteRequest) -> FAQEntry:
    removed = review.remove_review_item(payload.queue_id)
    if removed is None:
        raise HTTPException(status_code=404, detail="Review item not found")

    faq_entries = review.load_faq()
    question_text = removed.get("question") or "Untitled FAQ"
    answer_text = payload.answer or removed.get("answer") or "No answer provided yet."
    faq_entry = {
        "question": question_text,
        "answer": answer_text,
        "source_path": payload.source_path or removed.get("source_path"),
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }
    faq_entries.append(faq_entry)
    review.save_faq(faq_entries)
    return FAQEntry(**faq_entry)


@router.get("/insights", response_model=InsightsResponse)
def get_insights() -> InsightsResponse:
    summary = analytics.summarize()
    return InsightsResponse(**summary)


def build_citations(chunks: list[RetrievedChunk]) -> list[Citation]:
    seen = set()
    citations: list[Citation] = []
    for idx, chunk in enumerate(chunks, start=1):
        source_path = chunk.metadata.get("source_path")
        if not source_path or source_path in seen:
            continue
        seen.add(source_path)
        citations.append(
            Citation(
                title=chunk.metadata.get("title", f"Source {idx}"),
                section=chunk.metadata.get("section"),
                source_path=source_path,
            )
        )
    return citations


def compute_confidence(chunks: list[RetrievedChunk]) -> float:
    if not chunks:
        return 0.0

    scores = [chunk.score for chunk in chunks if chunk.score is not None]
    if not scores:
        return 0.0

    sorted_scores = sorted(scores, reverse=True)
    max_score = sorted_scores[0]
    second_score = sorted_scores[1] if len(sorted_scores) > 1 else max_score
    spread = max_score - second_score
    min_score = min(scores)

    score_component = normalize(max_score, 0.3, 1.0)
    spread_component = normalize(spread, 0.0, 0.4)
    consistency_component = normalize(max_score - min_score, 0.0, 0.5)
    coverage_component = normalize(len(scores) / settings.retrieval_top_k, 0.3, 1.0)

    combined = (
        0.5 * score_component
        + 0.2 * spread_component
        + 0.2 * consistency_component
        + 0.1 * coverage_component
    )
    return round(max(0.0, min(1.0, combined)), 2)


def normalize(value: float, lower: float, upper: float) -> float:
    if upper - lower == 0:
        return 0.0
    return max(0.0, min(1.0, (value - lower) / (upper - lower)))


app.include_router(router, prefix="")
