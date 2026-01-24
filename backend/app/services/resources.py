"""Course resource registry and storage helpers.

Stores metadata about uploaded files and link snapshots in storage/resources.json.
Actual files live under settings.uploads_dir/<course_id>/...
"""

from __future__ import annotations

import json
import os
import re
import shutil
import socket
from datetime import datetime, timezone
from ipaddress import ip_address
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

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
        except OSError:
            # Best-effort deletion; resource metadata already removed.
            return removed
    return removed


def delete_course_resources(course_id: str) -> None:
    items = _load_all()
    remaining = [item for item in items if item.get("course_id") != course_id]
    _save_all(remaining)
    course_root = settings.uploads_dir / course_id
    if course_root.exists():
        shutil.rmtree(course_root, ignore_errors=True)


def _is_private_host(hostname: str) -> bool:
    # Conservative hostname blocklist; DNS resolution checks happen separately.
    lowered = hostname.lower()
    if lowered in {"localhost"} or lowered.endswith(".local"):
        return True
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", lowered):
        # Block all IPv4 literals in demo to reduce SSRF risk
        return True
    if ":" in lowered:
        # Block obvious IPv6 literals
        return True
    return False


def _is_blocked_ip(ip: str) -> bool:
    addr = ip_address(ip)
    return (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_multicast
        or addr.is_reserved
        or addr.is_unspecified
    )


def _hostname_resolves_to_blocked_ip(hostname: str) -> bool:
    try:
        infos = socket.getaddrinfo(hostname, None)
    except Exception:
        return True
    for info in infos:
        ip = info[4][0]
        try:
            if _is_blocked_ip(ip):
                return True
        except Exception:
            return True
    return False


def _validate_snapshot_url(raw_url: str) -> str:
    parsed = urlparse(raw_url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only http/https URLs are supported")
    if parsed.username or parsed.password:
        raise ValueError("Userinfo in URL is not allowed")
    if not parsed.hostname:
        raise ValueError("Invalid URL")
    if _is_private_host(parsed.hostname):
        raise ValueError("Blocked hostname")
    if _hostname_resolves_to_blocked_ip(parsed.hostname):
        raise ValueError("Blocked hostname")

    allowed_ports = {
        int(p.strip())
        for p in settings.link_snapshot_allowed_ports.split(",")
        if p.strip().isdigit()
    }
    port = parsed.port
    if port is not None and allowed_ports and port not in allowed_ports:
        raise ValueError("Blocked port")

    return parsed.geturl()


def fetch_link_snapshot(url: str, max_bytes: int = 1_000_000) -> str:
    current_url = _validate_snapshot_url(url)

    # Optional allowlist by domain.
    allowlist = [d.strip().lower() for d in os.getenv("LENA_ALLOWED_LINK_DOMAINS", "").split(",") if d.strip()]
    if allowlist:
        hostname = urlparse(current_url).hostname or ""
        if not any(hostname.lower() == d or hostname.lower().endswith(f".{d}") for d in allowlist):
            raise ValueError("URL domain not allowed")

    visited: set[str] = set()
    redirects = 0
    timeout = httpx.Timeout(settings.link_snapshot_timeout_seconds)
    limits = httpx.Limits(max_connections=5, max_keepalive_connections=0)

    with httpx.Client(follow_redirects=False, timeout=timeout, limits=limits) as client:
        while True:
            if current_url in visited:
                raise ValueError("Redirect loop")
            visited.add(current_url)

            with client.stream("GET", current_url, headers={"User-Agent": "LENA-DemoFetcher/1.0"}) as resp:
                # Handle redirects manually so we can re-validate each hop.
                if resp.status_code in {301, 302, 303, 307, 308}:
                    location = resp.headers.get("location")
                    if not location:
                        raise ValueError("Redirect missing location")
                    redirects += 1
                    if redirects > settings.link_snapshot_max_redirects:
                        raise ValueError("Too many redirects")
                    next_url = urljoin(current_url, location)
                    current_url = _validate_snapshot_url(next_url)
                    if allowlist:
                        hostname = urlparse(current_url).hostname or ""
                        if not any(hostname.lower() == d or hostname.lower().endswith(f".{d}") for d in allowlist):
                            raise ValueError("URL domain not allowed")
                    continue

                resp.raise_for_status()
                ctype = (resp.headers.get("content-type") or "").lower()
                if ctype and not (ctype.startswith("text/") or "application/xhtml+xml" in ctype):
                    raise ValueError("Unsupported content type")

                buf = bytearray()
                for chunk in resp.iter_bytes():
                    if not chunk:
                        continue
                    buf.extend(chunk)
                    if len(buf) > max_bytes:
                        raise ValueError("Content too large")
                content = bytes(buf)
                break

    # Best-effort text extraction
    text = content.decode(resp.encoding or "utf-8", errors="replace")
    text = re.sub(r"(?is)<(script|style).*?>.*?</\\1>", "", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = re.sub(r"[\\t\\r]+", " ", text)
    text = re.sub(r"\\n{3,}", "\\n\\n", text)
    return text.strip()
