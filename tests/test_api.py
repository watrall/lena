from fastapi.testclient import TestClient

from backend.app.main import app


def test_ask_endpoint_returns_answer_with_citations(ingest_sample_corpus):
    client = TestClient(app)
    response = client.post("/ask", json={"question": "When is Assignment 1 due?"})

    assert response.status_code == 200
    payload = response.json()

    assert payload["citations"], "Expected at least one citation."
    assert 0.0 <= payload["confidence"] <= 1.0
    assert isinstance(payload["question_id"], str) and payload["question_id"]


def test_ask_endpoint_handles_late_policy(ingest_sample_corpus):
    client = TestClient(app)
    response = client.post("/ask", json={"question": "What is the late policy?"})

    assert response.status_code == 200
    payload = response.json()

    assert payload["citations"], "Expected citations for late policy response."
    assert payload["escalation_suggested"] in {True, False}
