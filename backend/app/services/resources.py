"""Course resource registry and storage helpers.

Stores metadata about uploaded files and link snapshots in storage/resources.json.
Actual files live under settings.uploads_dir/<course_id>/...
"""

import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx

from ..settings import settings
from .storage import read_json, storage_path, utc_timestamp, write_json

RESOURCE_FILENAME = "resources.json"


def _load_all() -> list[dict[str, Any]]:
    data = read_json(storage_path(RESOURCE_FILENAME), default=[])
    return data if isinstance(data, list) else []


def _save_all(items: list[dict[str, Any]]) -> None:
    write_json(storage_path(RESOURCE_FILENAME), items)


def ensure_course_dir(course_id: str) -> Path:
    root = settings.uploads_dir / course_id
    root.mkdir(parents=True, exist_ok=True)
    (root / "files").mkdir(parents=True, exist_ok=True)
    (root / "links").mkdir(parents=True, exist_ok=True)
    return root


def list_resources(course_id: str) -> list[dict[str, Any]]:
    return [r for r in _load_all() if r.get("course_id") == course_id]


def add_file_resource(course_id: str, resource_id: str, original_name: str, stored_path: str) -> dict[str, Any]:
    items = _load_all()
    record = {
        "id": resource_id,
        "course_id": course_id,
        "type": "file",
        "original_name": original_name,
        "source_path": stored_path,
        "created_at": utc_timestamp(),
    }
    items.append(record)
    _save_all(items)
    return record


def add_link_resource(course_id: str, resource_id: str, url: str, title: str | None, stored_path: str) -> dict[str, Any]:
    items = _load_all()
    record = {
        "id": resource_id,
        "course_id": course_id,
        "type": "link",
        "url": url,
        "title": title,
        "source_path": stored_path,
        "created_at": utc_timestamp(),
    }
    items.append(record)
    _save_all(items)
    return record


def delete_resource(course_id: str, resource_id: str) -> dict[str, Any] | None:
    items = _load_all()
    remaining: list[dict[str, Any]] = []
    removed: dict[str, Any] | None = None
    for item in items:
        if item.get("course_id") == course_id and item.get("id") == resource_id and removed is None:
            removed = item
            continue
        remaining.append(item)
    if removed is None:
        return None
    _save_all(remaining)
    path = removed.get("source_path")
    if isinstance(path, str):
        prefix = f"uploads/{course_id}/"
        subpath = path[len(prefix) :] if path.startswith(prefix) else None
        file_path = ((settings.uploads_dir / course_id / subpath) if subpath else None)
        # Best-effort deletion: only within uploads_dir/course_id (no traversal).
        try:
            if file_path:
                resolved = file_path.resolve()
                if str(resolved).startswith(str((settings.uploads_dir / course_id).resolve())) and resolved.exists():
                    resolved.unlink(missing_ok=True)
        except Exception:
            pass
    return removed


def delete_course_resources(course_id: str) -> None:
    items = _load_all()
    remaining = [item for item in items if item.get("course_id") != course_id]
    _save_all(remaining)
    course_root = settings.uploads_dir / course_id
    if course_root.exists():
        shutil.rmtree(course_root, ignore_errors=True)


def _is_private_host(hostname: str) -> bool:
    # Avoid DNS/network SSRF complexity; implement a conservative blocklist.
    lowered = hostname.lower()
    if lowered in {"localhost"} or lowered.endswith(".local"):
        return True
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", lowered):
        # Block all IPv4 literals in demo to reduce SSRF risk
        return True
    return False


def fetch_link_snapshot(url: str, max_bytes: int = 1_000_000) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only http/https URLs are supported")
    if not parsed.hostname:
        raise ValueError("Invalid URL")
    if _is_private_host(parsed.hostname):
        raise ValueError("Blocked hostname")

    # Optional allowlist by domain.
    allowlist = [d.strip().lower() for d in os.getenv("LENA_ALLOWED_LINK_DOMAINS", "").split(",") if d.strip()]
    if allowlist:
        if not any(parsed.hostname.lower() == d or parsed.hostname.lower().endswith(f".{d}") for d in allowlist):
            raise ValueError("URL domain not allowed")

    with httpx.Client(follow_redirects=True, timeout=10.0) as client:
        resp = client.get(url, headers={"User-Agent": "LENA-DemoFetcher/1.0"})
        resp.raise_for_status()
        content = resp.content[: max_bytes + 1]
        if len(content) > max_bytes:
            raise ValueError("Content too large")

    # Best-effort text extraction
    text = content.decode(resp.encoding or "utf-8", errors="replace")
    text = re.sub(r"(?is)<(script|style).*?>.*?</\\1>", "", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = re.sub(r"[\\t\\r]+", " ", text)
    text = re.sub(r"\\n{3,}", "\\n\\n", text)
    return text.strip()
