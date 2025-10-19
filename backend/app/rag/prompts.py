"""Prompt templates for grounded answer generation."""

from __future__ import annotations

from typing import Iterable

from .retrieve import RetrievedChunk


SYSTEM_PROMPT = (
    "You are LENA, an academic support assistant. Respond with clear, grounded answers "
    "that cite the supporting sources provided. If the context is insufficient, say so."
)


def build_prompt(question: str, chunks: Iterable[RetrievedChunk]) -> str:
    """Construct a prompt that places citations before the user question."""
    context_blocks = []
    for idx, chunk in enumerate(chunks, start=1):
        meta = chunk.metadata
        source = meta.get("source_path", "unknown")
        section = meta.get("section") or meta.get("title", "Untitled")
        block = "\n".join(
            [
                f"[{idx}] Title: {meta.get('title', 'Untitled')}",
                f"Section: {section}",
                f"Source: {source}",
                "Excerpt:",
                chunk.text.strip(),
            ]
        )
        context_blocks.append(block)

    context_text = "\n\n".join(context_blocks) if context_blocks else "No supporting passages."

    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        "Sources:\n"
        f"{context_text}\n\n"
        "Instructions:\n"
        "- Ground every statement in the provided sources.\n"
        "- Always cite sources using the bracket numbers, e.g., [1].\n"
        "- If information is missing, acknowledge the gap and suggest next steps.\n\n"
        f"Question: {question}\n"
        "Answer:"
    )
    return prompt
