import os
import shutil
from pathlib import Path

import pytest

TEST_ROOT = Path(__file__).resolve().parents[1]
TEST_STORAGE_DIR = TEST_ROOT / ".pytest-storage"
TEST_STORAGE_DIR.mkdir(exist_ok=True)

# Configure lightweight defaults before importing application modules.
os.environ.setdefault("LENA_QDRANT_LOCATION", ":memory:")
os.environ.setdefault("LENA_LLM_MODE", "off")
os.environ.setdefault("LENA_STORAGE_DIR", str(TEST_STORAGE_DIR))

from backend.app.models import embeddings  # noqa: E402
from backend.app.rag.ingest import run_ingest  # noqa: E402
from backend.app.rag.qdrant_utils import get_qdrant_client  # noqa: E402
from backend.app.settings import settings  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def ingest_sample_corpus(tmp_path_factory, monkeypatch):
    """Load the sample data set into an in-memory Qdrant instance once per test run."""
    data_src = TEST_ROOT / "data"
    temp_dir = tmp_path_factory.mktemp("data")
    shutil.copytree(data_src, temp_dir, dirs_exist_ok=True)

    class DummyEmbedder:
        def __init__(self, *_, **__):
            self._dim = 16

        def encode(self, text: str):
            seed = abs(hash(text)) % (10**6)
            return [((seed + i * 31) % 997) / 997 for i in range(self._dim)]

        def get_sentence_embedding_dimension(self) -> int:
            return self._dim

    monkeypatch.setattr("backend.app.models.embeddings.SentenceTransformer", DummyEmbedder)
    embeddings.get_embedder.cache_clear()

    # Use an isolated storage directory for test interactions.
    if TEST_STORAGE_DIR.exists():
        shutil.rmtree(TEST_STORAGE_DIR)
    TEST_STORAGE_DIR.mkdir(exist_ok=True)
    monkeypatch.setattr(settings, "storage_dir", TEST_STORAGE_DIR)

    # Ensure a clean collection for every test session.
    client = get_qdrant_client()
    try:
        client.delete_collection(settings.qdrant_collection)
    except Exception:
        pass

    result = run_ingest(data_dir=temp_dir)
    assert result.ok
    return result
