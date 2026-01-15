"""Answer generation using retrieval-augmented generation.

Supports two modes: Hugging Face pipeline generation for full LLM responses,
or extractive-only mode that stitches together retrieved snippets without
model inference (useful for demos and testing).
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING, Iterable

from transformers import pipeline

from ..rag.prompts import build_prompt
from ..rag.retrieve import RetrievedChunk
from ..settings import settings

if TYPE_CHECKING:
    from transformers import Pipeline

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_generator() -> "Pipeline":
    """Instantiate the Hugging Face generation pipeline lazily.

    Returns:
        A text-generation pipeline configured for CPU inference.
    """
    logger.info("Loading generation model: %s", settings.hf_model)
    return pipeline(
        "text-generation",
        model=settings.hf_model,
        trust_remote_code=False,
        device_map="cpu",
    )


def generate_answer(question: str, chunks: Iterable[RetrievedChunk]) -> str:
    """Produce a grounded answer using the configured generation strategy.

    Args:
        question: The user's question.
        chunks: Retrieved context chunks to ground the answer.

    Returns:
        A string answer, either generated or extractive depending on config.
    """
    chunk_list = list(chunks)

    if settings.llm_mode == "off":
        return _build_extractive_answer(question, chunk_list)

    prompt = build_prompt(question, chunk_list)
    generator = get_generator()
    outputs = generator(
        prompt,
        do_sample=False,
        max_new_tokens=settings.hf_max_new_tokens,
        temperature=0.1,
        top_p=0.95,
        return_full_text=False,
        truncation=True,
    )
    return outputs[0]["generated_text"].strip()


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
        summary = chunk.text.strip().splitlines()[0]
        lines.append(f"- {summary} [{idx}]")

    lines.append("Let me know if you need a deeper dive or additional context.")
    return "\n".join(lines)
