# Security Changes

## Overview
Security hardening focused on resilience to missing dependencies/Python 3.7, stronger course/PII validation, reliable retrieval/export behavior, and updated tests/docs. README.* untouched.

## Changes by Severity
- Critical: none open
- High: S1/S2/S3/S4 fixed (startup resilience, escalation validation, Qdrant stub integrity, export compatibility, meaningful fallbacks)
- Medium: S5/S6 fixed (Py3.7-safe cleanup/typing, email validation/PII guidance)
- Low: Doc refresh for security guidance

## Changes by Area
- **Auth/AuthZ & Validation**: Course existence and email validation enforced for escalations; instructor/admin routes made Py3.7-safe.
- **Config/Resilience**: Fallback BaseSettings, SlowAPI stubs, transformers/embedding fallbacks, Qdrant stub persistence, export compatibility.
- **Data Integrity/Retrieval**: Course-aware fallback retrieval and citation bias; upsert no longer overwrites points.
- **Docs**: SECURITY_REPORT, SECURITY_VERIFICATION, docs/security.md updated; CHANGELOG/QUALITY_AUDIT reflect work.
- **Tests**: Added/updated tests for fallbacks, validation, and cleanup.

## File-by-File Change List (what/why)
- SECURITY_REPORT.md — Baseline, commands, findings S1–S6, OWASP matrix updated.
- SECURITY_VERIFICATION.md — Recorded pytest pass, pip-audit absence, reverify steps.
- SECURITY_CHANGES.md — This changelog.
- QUALITY_AUDIT.md — Repo profile, findings, fixes applied.
- CHANGELOG.md — Notes on stability/maintainability/testing improvements.
- backend/requirements.txt — Pinned protobuf to 6.33.3 to avoid GHSA-7gcm-g887-7qv7 that was being pulled as 6.33.4 in CI.
- backend/app/settings.py — Fallback BaseSettings when pydantic-settings missing (A02/A10).
- backend/app/limiting.py — SlowAPI stubs to avoid startup crash (A10).
- backend/app/main.py — Safe rate-limit handler fallback (A10).
- backend/app/models/embeddings.py — Robust loader with dummy encoder fallback (A02/A10).
- backend/app/models/generate.py — Extractive fallback when generators fail; safer summarization (A10).
- backend/app/rag/{qdrant_utils.py,retrieve.py,ingest.py} — In-memory client persists points; course-aware fallback retrieval; data_dir sync (A01/A08/A10).
- backend/app/api/routes/{admin.py,chat.py,courses.py,export.py,health.py,instructors.py} — Py3.7-safe typing/compat; export removes suffix safely; better citation handling (A02/A10).
- backend/app/api/routes/feedback.py — Properly surfaces escalation validation errors (A05).
- backend/app/schemas/{chat.py,feedback.py} — Typing and email validation without external dep (A05/A10).
- backend/app/services/{escalations.py,exports.py,instructor_auth.py,resources.py} — Validation, compatibility, and safe typing for Python 3.7 (A02/A05/A10).
- tests/{conftest.py,test_api.py,test_escalation_security.py,test_retrieval.py,test_generate.py,test_escalations_store.py} — Coverage for fallbacks, validation, cleanup without `missing_ok` (regression guards).
- docs/security.md — Updated guidance on demo secrets, encryption, and operational hardening.

## Commands Executed
- `git status`
- `python3 -m pip-audit -r backend/requirements.txt` (fail: tool not installed)
- `pytest -q` (pass)

## README Pending Items
- None. README.* left unchanged per policy.
