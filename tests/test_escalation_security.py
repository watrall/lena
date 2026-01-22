from pathlib import Path

import pytest
from cryptography.fernet import Fernet

from backend.app.services import crypto, escalations
from backend.app.settings import settings as app_settings


@pytest.fixture(autouse=True)
def clear_fernet_cache():
    crypto._get_fernet.cache_clear()
    yield
    crypto._get_fernet.cache_clear()


def test_encrypt_pii_requires_key(monkeypatch):
    monkeypatch.delenv("LENA_ENCRYPTION_KEY", raising=False)
    with pytest.raises(RuntimeError):
        crypto.encrypt_pii("secret")


def test_escalation_append_requires_encryption(monkeypatch, tmp_path: Path):
    monkeypatch.delenv("LENA_ENCRYPTION_KEY", raising=False)
    monkeypatch.setattr(app_settings, "storage_dir", tmp_path)
    with pytest.raises(RuntimeError):
        escalations.append_request(
            {
                "question_id": "q1",
                "question": "What time is class?",
                "student_name": "Alice",
                "student_email": "alice@example.edu",
                "course_id": "c1",
            }
        )


def test_escalation_append_with_encryption(monkeypatch, tmp_path: Path):
    key = Fernet.generate_key().decode()
    monkeypatch.setenv("LENA_ENCRYPTION_KEY", key)
    monkeypatch.setattr(app_settings, "storage_dir", tmp_path)
    record = escalations.append_request(
        {
            "question_id": "q2",
            "question": "What is the late policy?",
            "student_name": "Bob",
            "student_email": "bob@example.edu",
            "course_id": "c1",
        }
    )
    assert record["student"] != "Bob"
    assert (tmp_path / "escalations.jsonl").exists()
