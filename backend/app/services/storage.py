"""JSON/JSONL storage helpers with basic path safety."""

from __future__ import annotations

import json
import logging
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from ..settings import settings

logger = logging.getLogger(__name__)


def utc_timestamp() -> str:
    """Return current UTC time as ISO 8601 string with Z suffix."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def ensure_storage() -> None:
    """Create the storage directory if it does not exist."""
    settings.storage_dir.mkdir(parents=True, exist_ok=True)


def storage_path(name: str) -> Path:
    """Return the full path for a storage file name (no traversal)."""
    # Prevent path traversal attacks
    if ".." in name or "/" in name or "\\" in name or name.startswith("."):
        raise ValueError(f"Invalid storage filename: {name}")
    ensure_storage()
    resolved = (settings.storage_dir / name).resolve()
    # Ensure the resolved path is within the storage directory
    if not str(resolved).startswith(str(settings.storage_dir.resolve())):
        raise ValueError(f"Path traversal detected: {name}")
    return resolved


def read_json(path: Path, default: Any) -> Any:
    """Read JSON from a file, returning a default if missing or invalid."""
    if not path.exists():
        return default
    try:
        content = path.read_text(encoding="utf-8")
        return json.loads(content) if content.strip() else default
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to read JSON from %s: %s", path, exc)
        return default


def write_json(path: Path, payload: Any) -> None:
    """Write JSON to a file atomically."""
    ensure_storage()
    content = json.dumps(payload, indent=2, ensure_ascii=True)
    _atomic_write(path, content)


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    """Append a single JSON record to a JSONL file."""
    ensure_storage()
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=True) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read all records from a JSONL file."""
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line_num, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            logger.warning("Skipped malformed JSON at %s:%d: %s", path, line_num, exc)
    return records


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    """Write records to a JSONL file atomically."""
    ensure_storage()
    lines = [json.dumps(record, ensure_ascii=True) for record in records]
    _atomic_write(path, "\n".join(lines) + "\n" if lines else "")


def _atomic_write(path: Path, content: str) -> None:
    """Write content to a file atomically using a temporary file."""
    ensure_storage()
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        delete=False,
        suffix=".tmp",
    ) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)
