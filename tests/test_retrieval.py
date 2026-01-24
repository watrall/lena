import sys

import numpy as np

from backend.app.rag.retrieve import retrieve
from backend.app.models import embeddings as embeddings_module
from backend.app.services import courses


def _course_id() -> str:
    course = courses.get_default_course()
    assert course is not None
    return course["id"]


def test_late_policy_returns_citation(ingest_sample_corpus):
    chunks = retrieve("What is the late policy for assignments?", course_id=_course_id())
    assert chunks, "Expected at least one retrieval result."
    paths = {chunk.metadata.get("source_path", "") for chunk in chunks}
    assert any("late" in path for path in paths), f"Missing late policy citation in paths: {paths}"


def test_assignment_due_returns_citation(ingest_sample_corpus):
    chunks = retrieve("When is Assignment 1 due?", course_id=_course_id())
    assert chunks, "Expected assignment retrieval results."
    paths = {chunk.metadata.get("source_path", "") for chunk in chunks}
    assert any("assignment" in path or "schedule" in path for path in paths), (
        f"Missing assignment citation, found: {paths}"
    )


def test_course_filter_excludes_other_materials(ingest_sample_corpus):
    anth204_chunks = retrieve("Unique Anth204 fact", course_id="anth204")
    assert anth204_chunks, "Expected Anth204 content to be retrievable."
    anth101_chunks = retrieve("Unique Anth204 fact", course_id="anth101")
    assert anth101_chunks, "Expected some results from Anth101 even if irrelevant."
    assert not any("Unique Anth204 fact" in chunk.text for chunk in anth101_chunks), "Should not retrieve Anth204 content in Anth101 context."


def test_embedding_fallback_dummy_encoder(monkeypatch):
    """Ensure we still embed when the primary model class fails to load."""
    embeddings_module.get_embedder.cache_clear()

    class FailingTransformer:
        def __init__(self, *_args, **_kwargs):
            raise RuntimeError("boom")

    def failing_import(_path: str):
        raise RuntimeError("import fail")

    monkeypatch.setattr(embeddings_module, "SentenceTransformer", FailingTransformer)
    monkeypatch.setattr(embeddings_module, "import_from_string", failing_import)

    embedder = embeddings_module.get_embedder()
    vec = embedder.encode("hello world")
    assert hasattr(embedder, "get_sentence_embedding_dimension")
    assert len(vec) == embedder.get_sentence_embedding_dimension()
    assert isinstance(vec, np.ndarray)
