"""Demo instructor authentication and course management endpoints."""

import hashlib
import logging
import re
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Body, Depends, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field, HttpUrl

from ...limiting import limiter
from ...services import courses
from ...services import resources
from ...services.instructor_auth import check_credentials, issue_token
from ...settings import settings
from ..deps import require_instructor

router = APIRouter(prefix="/instructors", tags=["instructors"])
logger = logging.getLogger(__name__)


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=128)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_at: str


class CourseCreateRequest(BaseModel):
    id: str = Field(..., min_length=2, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    name: str = Field(..., min_length=2, max_length=200)
    code: str | None = Field(default=None, max_length=64)
    term: str | None = Field(default=None, max_length=64)


@router.post("/login", response_model=LoginResponse)
@limiter.limit("10/minute")
def login(request: Request, payload: LoginRequest = Body(...)) -> LoginResponse:
    if not check_credentials(payload.username, payload.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = issue_token(payload.username)
    return LoginResponse(**token)


@router.get("/courses")
def list_courses(_: dict = Depends(require_instructor)):
    return courses.load_courses()


@router.post("/courses")
def create_course(payload: CourseCreateRequest, _: dict = Depends(require_instructor)):
    catalog = courses.load_courses()
    if any(entry["id"] == payload.id for entry in catalog if entry.get("id")):
        raise HTTPException(status_code=400, detail="Course ID already exists")
    catalog.append(
        {"id": payload.id, "name": payload.name, "code": payload.code, "term": payload.term}
    )
    # Persist
    from ...services.storage import write_json, storage_path

    write_json(storage_path("courses.json"), catalog)
    return {"ok": True}


@router.delete("/courses/{course_id}")
def delete_course(course_id: str, _: dict = Depends(require_instructor)):
    from ...services.storage import read_json, storage_path, write_json
    from ...rag.qdrant_utils import get_qdrant_client
    from qdrant_client.http import models as qmodels

    catalog = read_json(storage_path("courses.json"), default=[])
    if not isinstance(catalog, list):
        catalog = []
    next_catalog = [c for c in catalog if c.get("id") != course_id]
    if len(next_catalog) == len(catalog):
        raise HTTPException(status_code=404, detail="Course not found")
    write_json(storage_path("courses.json"), next_catalog)

    # Delete vectors for the course
    client = get_qdrant_client()
    client.delete(
        collection_name=settings.qdrant_collection,
        points_selector=qmodels.FilterSelector(
            filter=qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="course_id",
                        match=qmodels.MatchValue(value=course_id),
                    )
                ]
            )
        ),
    )

    resources.delete_course_resources(course_id)

    return {"ok": True}


class LinkCreateRequest(BaseModel):
    url: HttpUrl
    title: str | None = Field(default=None, max_length=200)


@router.get("/courses/{course_id}/resources")
def list_course_resources(course_id: str, _: dict = Depends(require_instructor)):
    return {"resources": resources.list_resources(course_id)}


@router.post("/courses/{course_id}/resources/upload")
async def upload_resource(course_id: str, file: UploadFile, _: dict = Depends(require_instructor)):
    if not re.match(r"^[a-zA-Z0-9_-]+$", course_id):
        raise HTTPException(status_code=400, detail="Invalid course_id")
    course = courses.get_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    original_name = file.filename or "upload"
    suffix = Path(original_name).suffix.lower()
    allowed_exts = {
        ext.strip().lower()
        for ext in settings.uploads_allowed_extensions.split(",")
        if ext.strip()
    }
    if allowed_exts and suffix not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(sorted(allowed_exts))}",
        )

    resources.ensure_course_dir(course_id)
    resource_id = uuid4().hex
    safe_name = re.sub(r"[^a-zA-Z0-9._-]+", "_", original_name)[:200]
    dest = settings.uploads_dir / course_id / "files" / f"{resource_id}_{safe_name}"

    bytes_written = 0
    with dest.open("wb") as handle:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            bytes_written += len(chunk)
            if bytes_written > settings.uploads_max_bytes:
                try:
                    dest.unlink(missing_ok=True)
                except OSError as exc:
                    logger.debug("Unable to remove partial upload %s: %s", dest, exc)
                raise HTTPException(status_code=413, detail="File too large")
            handle.write(chunk)

    if suffix in {".md", ".markdown", ".txt", ".ics"}:
        try:
            dest.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                dest.unlink(missing_ok=True)
            except OSError as exc:
                logger.debug("Unable to remove non-UTF8 upload %s: %s", dest, exc)
            raise HTTPException(status_code=400, detail="Uploaded file must be valid UTF-8 text")

    source_path = f"uploads/{course_id}/files/{dest.name}"
    record = resources.add_file_resource(course_id, resource_id, original_name, source_path)
    return {"ok": True, "resource": record}


@router.post("/courses/{course_id}/resources/link")
def add_link(course_id: str, payload: LinkCreateRequest, _: dict = Depends(require_instructor)):
    if not re.match(r"^[a-zA-Z0-9_-]+$", course_id):
        raise HTTPException(status_code=400, detail="Invalid course_id")
    course = courses.get_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    resources.ensure_course_dir(course_id)
    resource_id = uuid4().hex
    try:
        text = resources.fetch_link_snapshot(str(payload.url))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Unable to fetch URL snapshot") from exc

    filename = f"{resource_id}_link.txt"
    dest = settings.uploads_dir / course_id / "links" / filename
    dest.write_text(f"Title: {payload.title or 'Link'}\nURL: {payload.url}\n\n{text}\n", encoding="utf-8")

    source_path = f"uploads/{course_id}/links/{dest.name}"
    record = resources.add_link_resource(course_id, resource_id, str(payload.url), payload.title, source_path)
    return {"ok": True, "resource": record}


@router.delete("/courses/{course_id}/resources/{resource_id}")
def delete_course_resource(course_id: str, resource_id: str, _: dict = Depends(require_instructor)):
    removed = resources.delete_resource(course_id, resource_id)
    if removed is None:
        raise HTTPException(status_code=404, detail="Resource not found")

    # Delete vectors by doc_id (doc_id is sha1 of source_path used during ingestion).
    source_path = removed.get("source_path")
    if isinstance(source_path, str):
        doc_id = hashlib.sha1(source_path.encode("utf-8")).hexdigest()  # nosec B324
        try:
            from ...rag.qdrant_utils import get_qdrant_client
            from ...rag.ingest import delete_document_chunks

            delete_document_chunks(get_qdrant_client(), doc_id)
        except Exception as exc:
            logger.debug("Unable to delete vectors for %s: %s", doc_id, exc)

    return {"ok": True}
