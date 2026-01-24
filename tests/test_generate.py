from backend.app.models import generate as generate_module
from backend.app.rag.retrieve import RetrievedChunk
from backend.app.settings import settings


def test_generate_fallback_to_extractive(monkeypatch):
    """Generation should fall back to extractive output when pipeline fails."""
    previous_mode = settings.llm_mode
    settings.llm_mode = "hf"
    generate_module.get_generator.cache_clear()

    def failing_pipeline(*_args, **_kwargs):
        raise RuntimeError("pipeline boom")

    monkeypatch.setattr(generate_module, "pipeline", failing_pipeline)

    chunks = [
        RetrievedChunk(id="1", text="Assignment 1 is due next week.", score=0.9, metadata={})
    ]
    answer = generate_module.generate_answer("When is Assignment 1 due?", chunks)

    assert "Here is what I found" in answer

    settings.llm_mode = previous_mode
