"""Chat endpoint for learner question answering.

Provides the primary /ask endpoint that performs retrieval-augmented generation
to answer student questions with grounded, citation-backed responses.
"""

from uuid import uuid4

from fastapi import APIRouter, Body, Request

from ...models.generate import generate_answer
from ...rag.retrieve import RetrievedChunk, retrieve
from ...schemas.chat import AskRequest, AskResponse, Citation
from ...limiting import limiter
from ...services import analytics, questions
from ...services.storage import utc_timestamp
from ...settings import settings
from ..deps import resolve_course

router = APIRouter(tags=["chat"])


def _build_citations(chunks: list[RetrievedChunk]) -> list[Citation]:
    """Extract unique citations from retrieved chunks.

    Deduplicates citations by source path to avoid showing the same
    document multiple times in the response.

    Args:
        chunks: Retrieved document chunks from the vector store.

    Returns:
        A deduplicated list of citation objects.
    """
    seen: set[str] = set()
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


def _normalize(value: float, lower: float, upper: float) -> float:
    """Normalize a value to the 0-1 range."""
    if upper - lower == 0:
        return 0.0
    return max(0.0, min(1.0, (value - lower) / (upper - lower)))


def _compute_confidence(chunks: list[RetrievedChunk]) -> float:
    """Compute a confidence score from retrieval results.

    The score is based on:
    - Maximum similarity score
    - Score spread between top results
    - Consistency across all retrieved chunks
    - Coverage relative to the configured top_k
    """
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

    score_component = _normalize(max_score, 0.3, 1.0)
    spread_component = _normalize(spread, 0.0, 0.4)
    consistency_component = _normalize(max_score - min_score, 0.0, 0.5)
    coverage_component = _normalize(len(scores) / settings.retrieval_top_k, 0.3, 1.0)

    combined = (
        0.5 * score_component
        + 0.2 * spread_component
        + 0.2 * consistency_component
        + 0.1 * coverage_component
    )
    return round(max(0.0, min(1.0, combined)), 2)


@router.post("/ask", response_model=AskResponse)
@limiter.limit("10/minute")
async def ask_question(request: Request, payload: AskRequest = Body(...)) -> AskResponse:
    """Answer a learner's question using retrieval-augmented generation.

    Rate limited to 10 requests per minute per IP address via app-level limiter.

    Args:
        payload: The question and optional course context.

    Returns:
        An answer with citations, confidence score, and escalation flag.
    """
    course = resolve_course(payload.course_id)
    course_id = course["id"]

    chunks = retrieve(
        payload.question,
        top_k=settings.retrieval_top_k,
        course_id=course_id,
    )
    answer = generate_answer(payload.question, chunks)
    citations = _build_citations(chunks)
    confidence = _compute_confidence(chunks)
    escalation = confidence < settings.escalation_confidence_threshold

    question_id = uuid4().hex
    timestamp = utc_timestamp()

    analytics.log_event(
        {
            "type": "ask",
            "question_id": question_id,
            "question": payload.question,
            "confidence": confidence,
            "course_id": course_id,
            "timestamp": timestamp,
        }
    )
    questions.record_answer(
        {
            "question_id": question_id,
            "course_id": course_id,
            "question": payload.question,
            "answer": answer,
            "citations": [citation.model_dump() for citation in citations],
            "confidence": confidence,
            "timestamp": timestamp,
        }
    )

    return AskResponse(
        question_id=question_id,
        answer=answer,
        citations=citations,
        confidence=confidence,
        escalation_suggested=escalation,
    )
