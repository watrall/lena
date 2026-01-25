from __future__ import annotations

import os
from pathlib import Path

from backend.app.services import instructor_auth
from backend.app.settings import settings


def test_check_credentials_blocks_defaults_when_disallowed(monkeypatch):
    monkeypatch.setattr(settings, "allow_default_instructor_creds", False)
    monkeypatch.setattr(settings, "instructor_username", "demo")
    monkeypatch.setattr(settings, "instructor_password", "demo")
    assert instructor_auth.check_credentials("demo", "demo") is False


def test_default_secret_rotated_and_persisted(tmp_path, monkeypatch):
    key_path = tmp_path / "instructor_secret.key"
    monkeypatch.setattr(settings, "storage_dir", tmp_path)
    monkeypatch.setattr(settings, "instructor_auth_secret", "demo-secret-change-me")

    # Remove any existing key file to force creation
    if key_path.exists():
        key_path.unlink()

    token = instructor_auth.issue_token("demo")
    assert key_path.exists()
    saved = key_path.read_text(encoding="utf-8").strip()
    assert saved and saved != "demo-secret-change-me"
    payload = instructor_auth.verify_token(token["access_token"])
    assert payload and payload.get("sub") == "demo"
