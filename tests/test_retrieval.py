from backend.app.rag.retrieve import retrieve
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
    assert [chunk for chunk in anth101_chunks if chunk.metadata.get("course_id") == "anth101"] == []
