from uuid import uuid4

from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel, Field

from .models.generate import generate_answer
from .rag.ingest import IngestResult, run_ingest
from .rag.retrieve import RetrievedChunk, retrieve
from .settings import settings

app = FastAPI(title="LENA Backend", version="0.1.0")
router = APIRouter()


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

    return AskResponse(
        question_id=uuid4().hex,
        answer=answer,
        citations=citations,
        confidence=confidence,
        escalation_suggested=escalation,
    )


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
