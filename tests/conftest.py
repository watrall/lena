"""Shared pytest fixtures for backend tests."""

import os
import shutil
import sys
from pathlib import Path
from typing import Union

import numpy as np
import pytest
from pytest import MonkeyPatch

TEST_ROOT = Path(__file__).resolve().parents[1]
if str(TEST_ROOT) not in sys.path:
    sys.path.insert(0, str(TEST_ROOT))

TEST_STORAGE_DIR = TEST_ROOT / ".pytest-storage"
TEST_STORAGE_DIR.mkdir(exist_ok=True)

# Configure lightweight defaults before importing application modules.
os.environ.setdefault("LENA_QDRANT_LOCATION", ":memory:")
os.environ.setdefault("LENA_LLM_MODE", "off")
os.environ.setdefault("LENA_STORAGE_DIR", str(TEST_STORAGE_DIR))
# Ensure PII encryption is enabled during tests.
os.environ.setdefault("LENA_ENCRYPTION_KEY", "kO7arE5Wdl66iRS0LlwM651c01qmPvvrLpzjAU6Yews=")
os.environ.setdefault("LENA_ALLOW_DEFAULT_INSTRUCTOR_CREDS", "true")

from backend.app.models import embeddings  # noqa: E402
from backend.app.rag.ingest import run_ingest  # noqa: E402
from backend.app.rag.qdrant_utils import get_qdrant_client  # noqa: E402
from backend.app.settings import settings  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def ingest_sample_corpus(tmp_path_factory):
    """Load the sample data set into an in-memory Qdrant instance."""
    data_src = TEST_ROOT / "data"
    temp_dir = tmp_path_factory.mktemp("data")
    try:
        shutil.copytree(data_src, temp_dir, dirs_exist_ok=True)
    except TypeError:
        # Python <3.8 compatibility: recreate destination and copy without dirs_exist_ok.
        shutil.rmtree(temp_dir, ignore_errors=True)
        shutil.copytree(data_src, temp_dir)
    course_dir = temp_dir / "anth101"
    course_dir.mkdir(exist_ok=True)
    for item in list(temp_dir.iterdir()):
        if item == course_dir or item.is_dir():
            continue
        shutil.move(item, course_dir / item.name)
    second_course_dir = temp_dir / "anth204"
    second_course_dir.mkdir(exist_ok=True)
    (second_course_dir / "announcements.md").write_text(
        "# Anth204 Announcements\nUnique Anth204 fact lives here.",
        encoding="utf-8",
    )

    class DummyEmbedder:
        def __init__(self, *_, **__):
            self._dim = 16

        def encode(self, text: Union[str, list]):
            if isinstance(text, list):
                return np.array([self.encode(t) for t in text])
            seed = abs(hash(text)) % (10**6)
            return np.array([((seed + i * 31) % 997) / 997 for i in range(self._dim)], dtype=float)

        def get_sentence_embedding_dimension(self) -> int:
            return self._dim

    monkey = MonkeyPatch()
    monkey.setattr("backend.app.models.embeddings.SentenceTransformer", DummyEmbedder)
    embeddings.get_embedder.cache_clear()

    # Use an isolated storage directory for test interactions.
    if TEST_STORAGE_DIR.exists():
        shutil.rmtree(TEST_STORAGE_DIR)
    TEST_STORAGE_DIR.mkdir(exist_ok=True)
    monkey.setattr(settings, "storage_dir", TEST_STORAGE_DIR)
    uploads_dir = TEST_STORAGE_DIR / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    monkey.setattr(settings, "uploads_dir", uploads_dir)

    # Ensure a clean collection for every test session.
    client = get_qdrant_client()
    try:
        client.delete_collection(settings.qdrant_collection)
    except Exception:
        pass

    result = run_ingest(data_dir=temp_dir)
    assert result.ok
    yield result
    monkey.undo()
