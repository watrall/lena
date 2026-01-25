from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services import resources
from backend.app.settings import settings


@pytest.fixture(autouse=True)
def _isolate_uploads(tmp_path):
    # Point uploads_dir to a temp path for safety.
    orig = settings.uploads_dir
    tmp = tmp_path / "uploads"
    tmp.mkdir(parents=True, exist_ok=True)
    settings.uploads_dir = tmp
    try:
        yield tmp
    finally:
        settings.uploads_dir = orig
        shutil.rmtree(tmp, ignore_errors=True)


def test_delete_course_resources_blocks_traversal():
    # Ensure traversal attempts are rejected.
    with pytest.raises(ValueError):
        resources.delete_course_resources("../etc")


def test_delete_course_resources_removes_only_course_dir(_isolate_uploads):
    course_id = "safe123"
    root = resources.ensure_course_dir(course_id)
    nested = root / "files" / "note.txt"
    nested.write_text("hello", encoding="utf-8")

    other = resources.ensure_course_dir("other")
    (other / "files" / "keep.txt").write_text("stay", encoding="utf-8")

    resources.delete_course_resources(course_id)
    assert not root.exists()
    assert (other / "files" / "keep.txt").exists()


def test_instructor_delete_course_rejects_bad_id(monkeypatch):
    client = TestClient(app)
    login = client.post("/instructors/login", json={"username": "demo", "password": "demo"})
    assert login.status_code == 200
    token = login.json()["access_token"]

    bad_id = "bad!id"
    resp = client.delete(f"/instructors/courses/{bad_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400
    assert "Invalid course_id" in resp.text


def test_fallback_retrieve_ignores_invalid_course(monkeypatch):
    # Ensure invalid course ids don't cause traversal and still return empty list.
    from backend.app.rag import retrieve

    result = retrieve._fallback_local_chunks("test query", "../evil")
    assert result == []
