import io
import json
import zipfile
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from cryptography.fernet import Fernet

from backend.app.main import app
from backend.app.settings import settings
from backend.app.services import crypto
from backend.app.services.storage import append_jsonl, storage_path


def _write_event(course_id: str, event_type: str, timestamp: str, **extra):
    append_jsonl(
        storage_path("interactions.jsonl"),
        {"type": event_type, "question_id": "q1", "course_id": course_id, "timestamp": timestamp, **extra},
    )


def _write_escalation(course_id: str, submitted_at: str, **extra):
    append_jsonl(
        storage_path("escalations.jsonl"),
        {
            "id": "e1",
            "question_id": "q1",
            "course_id": course_id,
            "question": "Need help",
            "student": "Plain Student",
            "student_email": "student@example.edu",
            "submitted_at": submitted_at,
            "delivered": False,
            **extra,
        },
    )


@pytest.fixture()
def isolated_client(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "storage_dir", tmp_path)
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(settings, "uploads_dir", uploads_dir)
    monkeypatch.setattr(settings, "enable_export_endpoint", True)
    monkeypatch.setattr(settings, "enable_pii_export", True)
    monkeypatch.setenv("LENA_ENCRYPTION_KEY", Fernet.generate_key().decode("utf-8"))
    crypto._get_fernet.cache_clear()
    return TestClient(app)

@pytest.fixture()
def auth_headers(isolated_client):
    login = isolated_client.post("/instructors/login", json={"username": "demo", "password": "demo"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_export_single_component_single_course_json_no_pii(isolated_client, auth_headers):
    ts = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    _write_escalation("anth101", ts)

    response = isolated_client.get(
        "/admin/export",
        headers=auth_headers,
        params={
            "course_id": "anth101",
            "components": ["raw_escalations"],
            "format": "json",
            "range": "all",
            "include_pii": "false",
            "tz": "UTC",
        },
    )
    assert response.status_code == 200
    payload = json.loads(response.content.decode("utf-8"))
    assert payload and payload[0]["course_id"] == "anth101"
    assert payload[0].get("student") is None
    assert payload[0].get("student_email") is None


def test_export_pii_requires_confirmation(isolated_client, auth_headers):
    ts = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    _write_escalation("anth101", ts)

    response = isolated_client.get(
        "/admin/export",
        headers=auth_headers,
        params={
            "course_id": "anth101",
            "components": ["raw_escalations"],
            "format": "json",
            "range": "all",
            "include_pii": "true",
        },
    )
    assert response.status_code == 400

    ok = isolated_client.get(
        "/admin/export",
        headers=auth_headers,
        params={
            "course_id": "anth101",
            "components": ["raw_escalations"],
            "format": "json",
            "range": "all",
            "include_pii": "true",
            "include_pii_confirm": "INCLUDE",
            "tz": "UTC",
        },
    )
    assert ok.status_code == 200
    payload = json.loads(ok.content.decode("utf-8"))
    assert payload[0]["student"] == "Plain Student"
    assert payload[0]["student_email"] == "student@example.edu"


def test_export_zip_all_courses_split_by_course(isolated_client, auth_headers):
    ts_101 = datetime(2026, 1, 10, 12, 0, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    ts_204 = datetime(2026, 1, 11, 12, 0, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    _write_event("anth101", "ask", ts_101, question="Hello", confidence=0.8)
    _write_event("anth204", "ask", ts_204, question="Hello 204", confidence=0.7)

    response = isolated_client.get(
        "/admin/export",
        headers=auth_headers,
        params={
            "course_id": "all",
            "components": ["insights_totals", "raw_interactions"],
            "format": "csv",
            "range": "all",
            "tz": "UTC",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("application/zip")

    zf = zipfile.ZipFile(io.BytesIO(response.content))
    names = set(zf.namelist())
    assert any(name.endswith("/manifest.json") for name in names)

    # Expect per-course folders.
    assert any("/anth101/" in name for name in names)
    assert any("/anth204/" in name for name in names)

    # Expect requested components.
    assert any(name.endswith("/raw-interactions.csv") for name in names)
    assert any(name.endswith("/insights-totals.csv") for name in names)


def test_export_custom_range_filters_by_local_date(isolated_client, auth_headers):
    # Two events around midnight UTC; in UTC they fall on different days.
    _write_event("anth101", "ask", "2026-01-01T23:30:00Z", question="late", confidence=0.8)
    _write_event("anth101", "ask", "2026-01-02T00:30:00Z", question="early", confidence=0.8)

    response = isolated_client.get(
        "/admin/export",
        headers=auth_headers,
        params={
            "course_id": "anth101",
            "components": ["raw_interactions"],
            "format": "json",
            "range": "custom",
            "start_date": "2026-01-01",
            "end_date": "2026-01-01",
            "tz": "UTC",
        },
    )
    assert response.status_code == 200
    payload = json.loads(response.content.decode("utf-8"))
    questions = {row.get("question") for row in payload}
    assert "late" in questions
    assert "early" not in questions
