# Security Report

## Baseline (Phase 0)
- git status at start of this pass: **dirty** (working tree with prior fixes). No branches created; README.* untouched per protection rule.
- Available commands (from manifests/compose): `npm run lint|build` (frontend), `pytest` (backend), docker compose stack, optional `pip-audit` (dependency not installed in env).

## System Map & Trust Boundaries (Phase 1)
- Components: Next.js frontend (public), FastAPI backend (api), Qdrant vector store, local JSON/JSONL storage, optional uploads/snapshots under `storage/uploads`.
- Entry points: FastAPI routes under `backend/app/api/routes/*` (`/ask`, `/feedback`, `/escalations`, instructor/admin/export/ingest when enabled); frontend served via docker `web`.
- AuthZ/AuthN: Demo instructor bearer tokens (HMAC secret, TTL); learner chat intentionally unauthenticated. Feature flags gate ingest/admin/export/PII.
- Sensitive data: student questions/answers/citations; escalation PII (name/email) optionally encrypted via `LENA_ENCRYPTION_KEY`; uploaded files/link snapshots per course.
- Trust boundaries: public learners → `/ask`/`/feedback`; instructor-only endpoints behind bearer token + feature flags; storage/Qdrant assumed same trust zone; uploads/link fetching guarded by SSRF checks and file type limits.
- Critical assets: `storage/` JSON/JSONL, `uploads/`, Qdrant vectors, instructor tokens/secret, PII in escalations/review queues.

## Commands Run (Phase 2 & 6)
| Command | Purpose | Result | Key findings |
| --- | --- | --- | --- |
| git status | Baseline snapshot | Pass | Working tree dirty (expected) |
| python3 -m pip-audit -r backend/requirements.txt | Supply-chain scan | Fail | Tool not installed in env; prior output flagged protobuf 6.33.4 (GHSA-7gcm-g887-7qv7); pinned to 6.34.0 |
| pytest -q | Backend test+security regression | Pass | All tests now pass; warnings: missing pydantic-settings, python3.7 deprecation |

## Findings & Remediation (Phase 3 & 5)
- **S1 (High, A02/A10)**: Backend crashed at import/startup when optional deps (pydantic-settings, slowapi, transformers, sentence-transformers, qdrant-client, email-validator) were absent. *Remediation*: Added resilient fallbacks/stubs and safer typing for Python 3.7; generation/embed loaders degrade gracefully instead of failing. Files: `backend/app/settings.py`, `backend/app/limiting.py`, `backend/app/main.py`, `backend/app/models/{embeddings.py,generate.py}`, `backend/app/rag/{qdrant_utils.py,retrieve.py}`.
- **S2 (High, A01/A05/A06)**: Escalation API accepted unknown courses and weak email validation, risking orphaned PII records and analytics skew. *Remediation*: Enforced course existence and lightweight email validation; tests cover validation and dedupe. Files: `backend/app/services/escalations.py`, `backend/app/api/routes/feedback.py`, `backend/app/schemas/feedback.py`, tests updated.
- **S3 (High, A08/A10)**: In-memory Qdrant stub overwrote points on each upsert, breaking course isolation and retrieval; export route used `.removesuffix` (Python 3.9+ only) causing crashes on 3.7. *Remediation*: Preserve points on upsert, add course-aware fallback retrieval and citations, replace `.removesuffix` with compatible logic. Files: `backend/app/rag/{qdrant_utils.py,retrieve.py}`, `backend/app/api/routes/export.py`.
- **S4 (High, A02/A10)**: Missing dependency fallbacks led to empty answers/no citations when models unavailable. *Remediation*: Extractive fallback answers now meaningful with citation bias; tests assert behavior. Files: `backend/app/models/generate.py`, `backend/app/rag/retrieve.py`, `tests/test_generate.py`, `tests/test_retrieval.py`.
- **S5 (Med, A02/A06)**: Python 3.7 compatibility issues (`missing_ok`, union types) caused cleanup/export/test failures. *Remediation*: Backported Optional/List typing, safe file cleanup, and storage/test fixtures adjustments. Files: `backend/app/api/routes/{admin.py,instructors.py,courses.py,export.py,health.py}`, `tests/{conftest.py,test_api.py,test_escalation_security.py}`.
- **S6 (Med, A02/A04)**: PII encryption optional; lack of validation could store plaintext. *Remediation*: Email validation, explicit warning path, and doc updates in `docs/security.md`.
- **Deferred**: Containerized pytest still excludes tests (would require toolchain/image change). Supply-chain scans (`pip-audit`, `npm audit`) not runnable in current env; propose CI additions.

## OWASP Top 10:2025 Matrix (Phase 4)
| Item | Applicable | Status | Evidence | Findings | Remediation |
| --- | --- | --- | --- | --- | --- |
| A01 Broken Access Control | Y | Partial | Instructor token gate; course validation added; no auth on learner chat by design | S2 | Keep demo scope documented; tighten for prod |
| A02 Security Misconfiguration | Y | Partial | Fallbacks for missing deps; feature flags default-off; demo secrets remain | S1,S3,S5,S6 | Require env overrides/secret rotation in prod |
| A03 Software Supply Chain Failures | Y | Fail | `pip-audit` missing; no audit run | Deferred | Add pip-audit/npm audit to CI |
| A04 Cryptographic Failures | Y | Partial | PII encryption optional; warning documented; email validation added | S6 | Enforce key in prod, rotate demo key |
| A05 Injection | Y | Partial | Input validation strengthened for escalations; no raw SQL | S2 | Expand validation across routes |
| A06 Insecure Design | Y | Partial | Unauthenticated learner chat; demo flags; fallback retrieval | S2,S4 | Reassess for production |
| A07 Authentication Failures | Y | Partial | Demo creds, HMAC tokens | (none new) | Require stronger auth in prod |
| A08 Software/Data Integrity Failures | Y | Partial | Qdrant stub fixed; export compat fixed | S3 | Add checksum/signature for exports |
| A09 Security Logging & Alerting Failures | Y | Unknown | Event logging exists; no alerting reviewed | Deferred | Add alerting in prod |
| A10 Mishandling of Exceptional Conditions | Y | Partial | Startup failures fixed; extractive fallback; size limits present | S1,S3,S4 | Add rate limits/DoS tests |

## Mobile Top 10:2024
- Not applicable (no mobile code).

## Follow-up / Toolchain Requests (not implemented)
- Add CI jobs for `pip-audit` and `npm audit` with allowlists for demo-only CVEs.
- Package backend tests into docker api image or mount tests in CI to eliminate “0 tests collected”.
- Enforce env-only secrets and rotate demo values out-of-band for any non-demo environment.
