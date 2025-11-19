import json

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services import courses
from backend.app.services.storage import storage_path


def _course_id() -> str:
    course = courses.get_default_course()
    assert course is not None
    return course["id"]


def test_ask_endpoint_returns_answer_with_citations(ingest_sample_corpus):
    client = TestClient(app)
    response = client.post(
        "/ask",
        json={"question": "When is Assignment 1 due?", "course_id": _course_id()},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["citations"], "Expected at least one citation."
    assert 0.0 <= payload["confidence"] <= 1.0
    assert isinstance(payload["question_id"], str) and payload["question_id"]


def test_ask_endpoint_handles_late_policy(ingest_sample_corpus):
    client = TestClient(app)
    response = client.post(
        "/ask",
        json={"question": "What is the late policy?", "course_id": _course_id()},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["citations"], "Expected citations for late policy response."
    assert payload["escalation_suggested"] in {True, False}


def test_ask_endpoint_defaults_course_context(ingest_sample_corpus):
    client = TestClient(app)
    response = client.post("/ask", json={"question": "When is Assignment 1 due?"})
    assert response.status_code == 200
    assert response.json()["question_id"]


def test_courses_endpoint_returns_seed_data(ingest_sample_corpus):
    client = TestClient(app)
    response = client.get("/courses")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list) and data
    first = data[0]
    assert {"id", "name"}.issubset(first.keys())


def test_escalation_request_is_logged(ingest_sample_corpus):
    client = TestClient(app)
    ask_response = client.post(
        "/ask",
        json={"question": "Where is office hours posted?", "course_id": _course_id()},
    )
    question_id = ask_response.json()["question_id"]

    payload = {
        "question_id": question_id,
        "question": "Where is office hours posted?",
        "student_name": "Test Student",
        "student_email": "student@example.edu",
        "course_id": _course_id(),
    }
    response = client.post("/escalations/request", json=payload)
    assert response.status_code == 200
    assert response.json()["ok"] is True

    path = storage_path("escalations.jsonl")
    records = path.read_text(encoding="utf-8").strip().splitlines()
    assert any(question_id in line for line in records)
    path.unlink(missing_ok=True)


def test_feedback_review_uses_recorded_answer(ingest_sample_corpus):
    client = TestClient(app)
    ask_response = client.post(
        "/ask",
        json={"question": "What is the late policy?", "course_id": _course_id()},
    )
    question_id = ask_response.json()["question_id"]
    client.post(
        "/feedback",
        json={
            "question_id": question_id,
            "helpful": False,
            "course_id": _course_id(),
            "question": "tampered question",
            "answer": "tampered answer",
            "citations": [],
        },
    )
    queue_path = storage_path("review_queue.jsonl")
    entries = [json.loads(line) for line in queue_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert entries, "Expected review queue entry"
    latest = entries[-1]
    assert latest["question"] == "What is the late policy?"
    assert latest["answer"] == ask_response.json()["answer"]
    assert latest["citations"], "Expected citations sourced from stored answer."
    queue_path.unlink(missing_ok=True)


def test_insights_endpoint_structure(ingest_sample_corpus):
    client = TestClient(app)
    response = client.get(f"/insights?course_id={_course_id()}")
    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {
        "totals",
        "top_questions",
        "daily_volume",
        "confidence_trend",
        "escalations",
        "pain_points",
        "last_updated",
    }


def test_course_filter_blocks_cross_course_content(ingest_sample_corpus):
    client = TestClient(app)
    anth204_response = client.post(
        "/ask",
        json={"question": "Unique Anth204 fact?", "course_id": "anth204"},
    )
    assert anth204_response.status_code == 200
    assert "Unique Anth204 fact" in anth204_response.json()["answer"]

    anth101_response = client.post(
        "/ask",
        json={"question": "Unique Anth204 fact?", "course_id": "anth101"},
    )
    assert anth101_response.status_code == 200
    assert "Unique Anth204 fact" not in anth101_response.json()["answer"]
