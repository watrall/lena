"""Demo instructor authentication and course management endpoints."""

import hashlib
import re
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Body, Depends, HTTPException, UploadFile
from pydantic import BaseModel, Field, HttpUrl

from ...services import courses
from ...services import resources
from ...services.instructor_auth import check_credentials, issue_token
from ...settings import settings
from ..deps import require_instructor

router = APIRouter(prefix="/instructors", tags=["instructors"])


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
def login(payload: LoginRequest = Body(...)) -> LoginResponse:
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

    resources.ensure_course_dir(course_id)
    resource_id = uuid4().hex
    safe_name = re.sub(r"[^a-zA-Z0-9._-]+", "_", file.filename or "upload")
    dest = settings.uploads_dir / course_id / "files" / f"{resource_id}_{safe_name}"

    content = await file.read()
    if len(content) > 25_000_000:
        raise HTTPException(status_code=413, detail="File too large")
    dest.write_bytes(content)

    source_path = f"uploads/{course_id}/files/{dest.name}"
    record = resources.add_file_resource(course_id, resource_id, file.filename or dest.name, source_path)
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
        doc_id = hashlib.sha1(source_path.encode("utf-8")).hexdigest()
        try:
            from ...rag.qdrant_utils import get_qdrant_client
            from ...rag.ingest import delete_document_chunks

            delete_document_chunks(get_qdrant_client(), doc_id)
        except Exception:
            pass

    return {"ok": True}
