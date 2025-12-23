from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from ..settings import settings


def utc_timestamp() -> str:
    """Return current UTC time as ISO 8601 string with Z suffix."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def ensure_storage() -> None:
    settings.storage_dir.mkdir(parents=True, exist_ok=True)


def storage_path(name: str) -> Path:
    ensure_storage()
    return settings.storage_dir / name


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8") or json.dumps(default))


def write_json(path: Path, payload: Any) -> None:
    ensure_storage()
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    ensure_storage()
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=True) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    ensure_storage()
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")
