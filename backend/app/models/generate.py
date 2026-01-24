"""Answer generation (model-backed or extractive-only)."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING, Iterable

try:
    from transformers import pipeline  # type: ignore
except ImportError:  # pragma: no cover - offline/test fallback
    pipeline = None  # type: ignore

from ..rag.prompts import build_prompt
from ..rag.retrieve import RetrievedChunk
from ..settings import settings

if TYPE_CHECKING:
    from transformers import Pipeline

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_generator() -> "Pipeline":
    """Instantiate the Hugging Face generation pipeline lazily."""
    logger.info("Loading generation model: %s", settings.hf_model)
    try:
        if pipeline is None:
            raise ImportError("transformers is not installed")
        return pipeline(
            "text-generation",
            model=settings.hf_model,
            trust_remote_code=False,
            device_map="cpu",
        )
    except Exception as exc:  # pragma: no cover - fallback exercised at runtime
        logger.error("Generation model load failed (%s); switching to extractive mode", exc)
        # Force extractive mode for subsequent calls to avoid repeated failures.
        from .. import settings as _settings

        try:
            _settings.settings.llm_mode = "off"  # type: ignore[attr-defined]
        except Exception:
            pass

        class NullGenerator:
            def __call__(self, *_, **__):
                return [{"generated_text": ""}]

        return NullGenerator()


def generate_answer(question: str, chunks: Iterable[RetrievedChunk]) -> str:
    """Produce a grounded answer using the configured generation strategy."""
    chunk_list = list(chunks)

    if settings.llm_mode == "off":
        return _build_extractive_answer(question, chunk_list)

    prompt = build_prompt(question, chunk_list)
    generator = get_generator()
    try:
        outputs = generator(
            prompt,
            do_sample=False,
            max_new_tokens=settings.hf_max_new_tokens,
            temperature=0.1,
            top_p=0.95,
            return_full_text=False,
            truncation=True,
        )
        text = outputs[0].get("generated_text", "").strip()
        if not text:
            return _build_extractive_answer(question, chunk_list)
        return text
    except Exception as exc:  # pragma: no cover - runtime fallback
        logger.error("Generation failed (%s); using extractive answer", exc)
        return _build_extractive_answer(question, chunk_list)


def _build_extractive_answer(question: str, chunks: list[RetrievedChunk]) -> str:
    """Build an extractive answer by stitching together top snippets.

    Used as a fallback when LLM generation is disabled.
    """
    if not chunks:
        return (
            "I couldn't find supporting context for that question in the current "
            "knowledge base. You may need to consult the course team."
        )

    lines = ["Here is what I found in the course materials:"]
    for idx, chunk in enumerate(chunks, start=1):
        lines_in_chunk = [line.strip() for line in chunk.text.splitlines() if line.strip()]
        summary_line = next(
            (line.lstrip("# ").strip() for line in lines_in_chunk if not line.startswith("#")),
            lines_in_chunk[0] if lines_in_chunk else "",
        )
        summary = summary_line or chunk.text.strip()[:120]
        lines.append(f"- {summary} [{idx}]")

    lines.append("Let me know if you need a deeper dive or additional context.")
    return "\n".join(lines)
