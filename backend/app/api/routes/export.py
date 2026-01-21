"""Export endpoints for pilot data downloads.

These endpoints support JSON/CSV exports of raw logs and insights components.
They are intentionally lightweight for pilot workflows (no auth in demo mode).
"""

import io
import zipfile
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import Response, StreamingResponse

from ...services import exports
from ...settings import settings
from ...services.crypto import is_encryption_enabled
from ...limiting import limiter
from ...services import analytics
from ...services.storage import utc_timestamp

router = APIRouter(tags=["export"])

ALLOWED_FORMATS = {"json", "csv"}
ALLOWED_RANGES = {"7d", "30d", "custom", "all"}

KNOWN_COMPONENTS = {
    "insights_totals",
    "insights_top_questions",
    "insights_daily_volume",
    "insights_confidence_trend",
    "insights_pain_points",
    "insights_escalations",
    "raw_interactions",
    "raw_answers",
    "raw_review_queue",
    "raw_faq",
    "raw_escalations",
}


def _timestamp_suffix() -> str:
    return datetime.utcnow().strftime("%Y%m%d-%H%M%SZ")


def _range_token(kind: str, start_date: str | None, end_date: str | None) -> str:
    if kind in {"7d", "30d", "all"}:
        return f"range-{kind}"
    start = start_date or "custom"
    end = end_date or start
    return f"range-{start}-{end}"


@router.get("/admin/export")
@limiter.limit("5/minute")
async def export_data(
    request: Request,
    course_id: str = Query(..., description="Course identifier or 'all'"),
    components: list[str] = Query(..., description="Export component keys (repeatable)"),
    format: str = Query("json", description="Export format (json|csv)"),
    range: str = Query("30d", description="Date range selector (7d|30d|custom|all)"),
    start_date: str | None = Query(None, description="Custom range start (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="Custom range end (YYYY-MM-DD)"),
    tz: str | None = Query(None, description="IANA timezone name (e.g., America/Detroit)"),
    include_pii: bool = Query(False, description="Include student PII fields (explicit opt-in)"),
    include_pii_confirm: str | None = Query(None, description="Must equal 'INCLUDE' when include_pii=true"),
) -> Response:
    if not settings.enable_export_endpoint:
        raise HTTPException(status_code=404, detail="Not found")
    if len(components) > settings.export_max_components:
        raise HTTPException(status_code=400, detail="Too many components requested")
    if not components:
        raise HTTPException(status_code=400, detail="At least one component is required")
    if format not in ALLOWED_FORMATS:
        raise HTTPException(status_code=400, detail="format must be json or csv")
    if range not in ALLOWED_RANGES:
        raise HTTPException(status_code=400, detail="range must be one of 7d, 30d, custom, all")

    unknown = sorted(set(components) - KNOWN_COMPONENTS)
    if unknown:
        raise HTTPException(status_code=400, detail=f"Unknown components: {', '.join(unknown)}")

    if include_pii and not settings.enable_pii_export:
        raise HTTPException(status_code=400, detail="PII export is disabled on this server")
    if include_pii and not is_encryption_enabled():
        raise HTTPException(status_code=400, detail="PII export requires LENA_ENCRYPTION_KEY to be configured")
    if include_pii and include_pii_confirm != "INCLUDE":
        raise HTTPException(
            status_code=400,
            detail="PII export requires include_pii_confirm=INCLUDE",
        )
    analytics.log_event(
        {
            "type": "admin_export",
            "question_id": "n/a",
            "course_id": course_id,
            "timestamp": utc_timestamp(),
        }
    )

    timezone = exports.resolve_timezone(tz)
    try:
        date_range = exports.resolve_range(range, timezone, start_date, end_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        course_entries = exports.list_available_courses(course_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    ts = _timestamp_suffix()
    pii_token = "pii" if include_pii else "no-pii"
    range_token = _range_token(range, start_date, end_date)

    # If the request results in a single file, return it directly.
    single_course = len(course_entries) == 1
    single_component = len(components) == 1
    if single_course and single_component:
        selected_course = course_entries[0]
        selected_course_id = str(selected_course.get("id") or course_id)
        component = components[0]

        payload = None
        if component.startswith("insights_"):
            insights = exports.compute_insights_components(
                course_id=selected_course_id,
                date_range=date_range,
                tz=timezone,
                include_pii=include_pii,
            )
            payload = insights[component]
        else:
            payload = exports.load_raw_component(
                component,
                course_id=selected_course_id,
                date_range=date_range,
                tz=timezone,
                include_pii=include_pii,
            )

        content = exports.component_bytes(payload, format)
        filename = f"lena_export-course-{selected_course_id}-{range_token}-{pii_token}-{component}-{ts}.{format}"
        return Response(
            content=content,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    zip_buffer = io.BytesIO()
    zip_name = f"lena_export-course-{course_id}-{range_token}-{pii_token}-multi-{ts}.zip"
    root_folder = zip_name.removesuffix(".zip")

    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        manifest = {
            "generated_at": ts,
            "course_id": course_id,
            "courses": [entry.get("id") for entry in course_entries],
            "format": format,
            "range": {"kind": range, "start_date": start_date, "end_date": end_date, "timezone": tz},
            "components": components,
            "include_pii": include_pii,
        }
        zf.writestr(f"{root_folder}/manifest.json", exports.component_bytes(manifest, "json"))

        for course in course_entries:
            cid = str(course.get("id") or "")
            course_folder = f"{root_folder}/{cid}"

            insights_payload = None
            if any(component.startswith("insights_") for component in components):
                insights_payload = exports.compute_insights_components(
                    course_id=cid,
                    date_range=date_range,
                    tz=timezone,
                    include_pii=include_pii,
                )

            for component in components:
                if component.startswith("insights_"):
                    assert insights_payload is not None
                    payload = insights_payload[component]
                else:
                    payload = exports.load_raw_component(
                        component,
                        course_id=cid,
                        date_range=date_range,
                        tz=timezone,
                        include_pii=include_pii,
                    )
                name = exports.component_to_filename(component, format)
                zf.writestr(f"{course_folder}/{name}", exports.component_bytes(payload, format))

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{zip_name}"'},
    )
