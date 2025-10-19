from __future__ import annotations

from functools import lru_cache
from typing import Iterable

from transformers import pipeline

from ..settings import settings
from ..rag.prompts import build_prompt
from ..rag.retrieve import RetrievedChunk


@lru_cache(maxsize=1)
def get_generator():
    """Instantiate the Hugging Face generation pipeline lazily."""
    return pipeline(
        "text-generation",
        model=settings.hf_model,
        trust_remote_code=False,
        device_map="cpu",
    )


def generate_answer(question: str, chunks: Iterable[RetrievedChunk]) -> str:
    """Produce a grounded answer using the configured generation strategy."""
    chunk_list = list(chunks)

    if settings.llm_mode == "off":
        return build_extractive_answer(question, chunk_list)

    prompt = build_prompt(question, chunk_list)
    generator = get_generator()
    outputs = generator(
        prompt,
        do_sample=False,
        max_new_tokens=settings.hf_max_new_tokens,
        temperature=0.1,
        top_p=0.95,
        return_full_text=False,
    )
    return outputs[0]["generated_text"].strip()


def build_extractive_answer(question: str, chunks: list[RetrievedChunk]) -> str:
    """Fallback extractive answer that stitches together top snippets."""
    if not chunks:
        return (
            "I couldn't find supporting context for that question in the current knowledge base. "
            "You may need to consult the course team."
        )

    lines = [
        "Here is what I found in the course materials:",
    ]

    for idx, chunk in enumerate(chunks, start=1):
        summary = chunk.text.strip().splitlines()[0]
        lines.append(f"- {summary} [{idx}]")

    lines.append("Let me know if you need a deeper dive or additional context.")
    return "\n".join(lines)
