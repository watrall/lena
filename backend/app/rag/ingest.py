from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from arrow import Arrow

from ics import Calendar
from markdown import markdown
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from qdrant_client.http.exceptions import UnexpectedResponse

from ..models.embeddings import get_embedder
from ..settings import settings
from ..services import courses
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
    course_id: str
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
        chunk_payloads = list(chunk_document(document))
        if not chunk_payloads:
            continue

        texts = [payload[1] for payload in chunk_payloads]
        vectors = embedder.encode(texts)

        delete_document_chunks(client, document.doc_id)

        points: list[qmodels.PointStruct] = []
        for (chunk_idx, chunk_text, section_title), vector in zip(chunk_payloads, vectors):
            metadata = build_metadata(document, section_title)
            points.append(
                qmodels.PointStruct(
                    id=deterministic_chunk_id(document.doc_id, chunk_idx),
                    vector=vector.tolist(),
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
        course_id=detect_course_id(path, root),
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
        course_id=detect_course_id(path, root),
        sections=sections,
    )


def chunk_document(document: ParsedDocument) -> Iterable[tuple[int, str, str]]:
    chunk_index = 0
    for section in document.sections:
        for chunk in chunk_text(section.content):
            yield chunk_index, chunk, section.title
            chunk_index += 1


def chunk_text(text: str, max_tokens: int = MAX_TOKENS, overlap: int = OVERLAP) -> list[str]:
    """Split text into overlapping chunks of approximately max_tokens words.

    Args:
        text: The text to chunk.
        max_tokens: Maximum words per chunk.
        overlap: Number of words to overlap between chunks.

    Returns:
        A list of text chunks.
    """
    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
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


def detect_course_id(path: Path, root: Path) -> str:
    rel_parts = path.relative_to(root).parts
    if len(rel_parts) > 1:
        return rel_parts[0]
    default_course = courses.get_default_course()
    if default_course:
        return default_course["id"]
    if rel_parts:
        return rel_parts[0]
    return "default"


def format_arrow(value: "Arrow | None") -> str:
    """Format an Arrow datetime to ISO 8601 string.

    Args:
        value: An Arrow datetime object, or None.

    Returns:
        ISO 8601 formatted string, or empty string if None.
    """
    if value is None:
        return ""
    dt = value.to("utc").datetime
    return dt.isoformat()


def strip_html(raw: str) -> str:
    text = markdown(raw)
    plain = re.sub("<[^<]+?>", "", text)
    return plain.strip()


def delete_document_chunks(client: "QdrantClient", doc_id: str) -> None:
    """Remove all existing chunks for a document before re-ingestion.

    Args:
        client: The Qdrant client instance.
        doc_id: The document ID whose chunks should be deleted.
    """
    try:
        client.delete(
            collection_name=settings.qdrant_collection,
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="doc_id",
                            match=qmodels.MatchValue(value=doc_id),
                        )
                    ]
                )
            ),
        )
    except UnexpectedResponse:
        pass


def deterministic_chunk_id(doc_id: str, chunk_idx: int) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{doc_id}:{chunk_idx}"))


def build_metadata(document: ParsedDocument, section_title: str) -> dict[str, str]:
    return {
        "doc_id": document.doc_id,
        "version_id": document.version_id,
        "collection": document.collection,
        "title": document.title,
        "section": section_title,
        "source_path": document.source_path,
        "course_id": document.course_id,
        "crawl_ts": datetime.now(timezone.utc).isoformat(),
    }
