from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends

from ...models.generate import generate_answer
from ...rag.retrieve import RetrievedChunk, retrieve
from ...services import analytics, questions
from ...settings import settings
from ..deps import resolve_course
from ...schemas.chat import AskRequest, AskResponse, Citation

router = APIRouter()

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

def normalize(value: float, lower: float, upper: float) -> float:
    if upper - lower == 0:
        return 0.0
    return max(0.0, min(1.0, (value - lower) / (upper - lower)))

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

@router.post("/ask", response_model=AskResponse)
def ask_question(payload: AskRequest) -> AskResponse:
    course = resolve_course(payload.course_id)
    course_id = course["id"]

    chunks = retrieve(payload.question, top_k=settings.retrieval_top_k, course_id=course_id)
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
            "course_id": course_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
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
