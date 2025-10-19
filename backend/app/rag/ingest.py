from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from ics import Calendar
from markdown import markdown
from pydantic import BaseModel
from qdrant_client.http import models as qmodels

from ..models.embeddings import get_embedder
from ..settings import settings
from .qdrant_utils import ensure_collection, get_qdrant_client

MAX_TOKENS = 700
OVERLAP = 120


class IngestCounts(BaseModel):
    docs: int
    chunks: int


class IngestResult(BaseModel):
    ok: bool
    counts: IngestCounts


@dataclass
class Section:
    title: str
    content: str


@dataclass
class ParsedDocument:
    doc_id: str
    version_id: str
    collection: str
    title: str
    source_path: str
    sections: list[Section]


def run_ingest(data_dir: Path | None = None) -> IngestResult:
    """Main ingestion entry point for FastAPI endpoint and CLI usage."""
    data_path = data_dir or settings.data_dir
    docs_processed = 0
    chunk_count = 0

    if not data_path.exists():
        return IngestResult(ok=True, counts=IngestCounts(docs=0, chunks=0))

    embedder = get_embedder()
    ensure_collection()
    client = get_qdrant_client()

    for document in iter_documents(data_path):
        docs_processed += 1
        points = []
        for chunk_text, section_title in chunk_document(document):
            vector = embedder.encode(chunk_text).tolist()
            metadata = {
                "doc_id": document.doc_id,
                "version_id": document.version_id,
                "collection": document.collection,
                "title": document.title,
                "section": section_title,
                "source_path": document.source_path,
                "crawl_ts": datetime.now(timezone.utc).isoformat(),
            }
            points.append(
                qmodels.PointStruct(
                    id=uuid4().hex,
                    vector=vector,
                    payload={"text": chunk_text, **metadata},
                )
            )
        if points:
            client.upsert(collection_name=settings.qdrant_collection, points=points)
            chunk_count += len(points)

    return IngestResult(ok=True, counts=IngestCounts(docs=docs_processed, chunks=chunk_count))


def iter_documents(data_path: Path) -> Iterable[ParsedDocument]:
    for path in sorted(data_path.rglob("*")):
        if path.is_dir():
            continue
        if path.suffix.lower() in {".md", ".markdown"}:
            yield parse_markdown(path, data_path)
        elif path.suffix.lower() == ".ics":
            yield parse_calendar(path, data_path)


def parse_markdown(path: Path, root: Path) -> ParsedDocument:
    text = path.read_text(encoding="utf-8")
    rel_path = str(path.relative_to(root))
    doc_id = hashlib.sha1(rel_path.encode("utf-8")).hexdigest()
    version_id = str(int(path.stat().st_mtime))
    collection = detect_collection(path)

    sections: list[Section] = []
    current_title = path.stem.replace("-", " ").strip().title()
    buffer: list[str] = []

    for line in text.splitlines():
        heading_match = re.match(r"^(#{1,6})\s+(.*)", line)
        if heading_match:
            if buffer:
                sections.append(Section(title=current_title, content="\n".join(buffer).strip()))
                buffer = []
            current_title = heading_match.group(2).strip()
        else:
            buffer.append(line)

    if buffer:
        sections.append(Section(title=current_title, content="\n".join(buffer).strip()))

    if not sections:
        sections.append(Section(title=current_title, content=text))

    first_heading = sections[0].title if sections else current_title
    title = first_heading or path.stem

    return ParsedDocument(
        doc_id=doc_id,
        version_id=version_id,
        collection=collection,
        title=title,
        source_path=rel_path,
        sections=sections,
    )


def parse_calendar(path: Path, root: Path) -> ParsedDocument:
    content = path.read_text(encoding="utf-8")
    rel_path = str(path.relative_to(root))
    doc_id = hashlib.sha1(rel_path.encode("utf-8")).hexdigest()
    version_id = str(int(path.stat().st_mtime))
    calendar = Calendar(content)

    sections: list[Section] = []

    for event in sorted(calendar.events, key=lambda e: e.begin.timestamp() if e.begin else 0):
        start = format_arrow(event.begin)
        end = format_arrow(event.end)
        lines = [
            f"Event: {event.name or 'Untitled'}",
            f"Starts: {start}",
            f"Ends: {end}",
        ]
        if event.location:
            lines.append(f"Location: {event.location}")
        if event.description:
            lines.append(f"Details: {strip_html(event.description)}")

        section_title = event.name or start or "Calendar Event"
        sections.append(Section(title=section_title, content="\n".join(lines)))

    if not sections:
        sections.append(Section(title="Calendar", content="No events found."))

    return ParsedDocument(
        doc_id=doc_id,
        version_id=version_id,
        collection="calendar",
        title=path.stem.replace("_", " ").title(),
        source_path=rel_path,
        sections=sections,
    )


def chunk_document(document: ParsedDocument) -> Iterable[tuple[str, str]]:
    for section in document.sections:
        for chunk in chunk_text(section.content):
            yield chunk, section.title


def chunk_text(text: str, max_tokens: int = MAX_TOKENS, overlap: int = OVERLAP) -> Iterable[str]:
    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    while start < len(words):
        end = min(start + max_tokens, len(words))
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))
        if end == len(words):
            break
        start = max(0, end - overlap)

    return chunks


def detect_collection(path: Path) -> str:
    lowered = path.stem.lower()
    if "policy" in lowered:
        return "policy"
    if "syllabus" in lowered:
        return "policy"
    return "course"


def format_arrow(value) -> str:
    if value is None:
        return ""
    dt = value.to("utc").datetime
    return dt.isoformat()


def strip_html(raw: str) -> str:
    text = markdown(raw)
    plain = re.sub("<[^<]+?>", "", text)
    return plain.strip()
