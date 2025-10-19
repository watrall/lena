from backend.app.rag.retrieve import retrieve


def test_late_policy_returns_citation(ingest_sample_corpus):
    chunks = retrieve("What is the late policy for assignments?")
    assert chunks, "Expected at least one retrieval result."
    paths = {chunk.metadata.get("source_path", "") for chunk in chunks}
    assert any("late" in path for path in paths), f"Missing late policy citation in paths: {paths}"


def test_assignment_due_returns_citation(ingest_sample_corpus):
    chunks = retrieve("When is Assignment 1 due?")
    assert chunks, "Expected assignment retrieval results."
    paths = {chunk.metadata.get("source_path", "") for chunk in chunks}
    assert any("assignment" in path or "schedule" in path for path in paths), (
        f"Missing assignment citation, found: {paths}"
    )
