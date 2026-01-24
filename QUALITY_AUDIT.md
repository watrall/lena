# Repo Profile
- **Frontend**: Next.js 14 (React/TS, Tailwind) served from `frontend`; uses `npm` with package-lock.
- **Backend**: FastAPI (Python 3.11) in `backend/app`; storage via JSON/JSONL files under `storage`; demo seeding on startup.
- **ML stack**: HuggingFace text-generation + sentence-transformers embeddings; Qdrant vector DB (remote or in-memory) via docker-compose `qdrant` service.
- **Runtime entrypoints**: `backend/app/main.py` (routers in `api/routes/*`), `frontend/pages/_app.tsx`; Compose orchestrated by `docker/docker-compose.yml`.
- **Config**: `.env`-driven Pydantic settings (prefix `LENA_`); feature flags for ingest/export/instructor auth; uploads stored under `storage/uploads` by default.
- **Build/Test**: `npm run lint|build` for frontend; `pytest` from repo root (uses in-memory Qdrant); compose targets `api`, `web`, `qdrant`.
- **Auth**: Demo instructor bearer tokens (HMAC secret + TTL) gating instructor/export endpoints when enabled; learner endpoints open.
- **Data flows**: Questions logged to `interactions.jsonl`; answers stored for feedback/escalations; exports aggregate from storage; resources uploads + link snapshots per course.
- **Notable risks**: Heavy HF model downloads on first request, missing dependency guard for pydantic-settings, and containerized pytest omission; storage is single-host JSON without locking.

# Phase 1 — Automated Signal Collection (existing tools only)
| Tool/Command | Result | Notes |
| --- | --- | --- |
| `npm run lint` | Pass | No ESLint errors. |
| `docker compose -f docker/docker-compose.yml build api web --no-cache` | Pass | Images build successfully. |
| `docker compose -f docker/docker-compose.yml run --rm api pytest` | Fail | 0 tests collected; pytest cache permission warning (tests not baked into image, /app owned by root). |
| `docker compose -f docker/docker-compose.yml up -d` | Pass | web/api/qdrant healthy (ports 3000/8000). |

Stop-the-line issues: None observed in app runtime; however pytest-in-container is ineffective (no tests), which leaves backend unverified.

# Phase 2 — Findings
| ID | Severity | Location | Description & Risk | Recommendation |
| --- | --- | --- | --- | --- |
| F1 | P1 (High) | backend/app/services/escalations.py | append_request accepted missing/unknown course and malformed data, storing orphaned records and bad statuses. | Validate course/question fields and course existence; coerce status to allowed set (FIXED). |
| F2 | P1 (High) | backend/app/services/escalations.py | Duplicate escalation submissions (same course/question) wrote multiple rows, skewing insights/export and badge counts. | Deduplicate on (course_id, question_id) and reuse existing record (FIXED). |
| F3 | P1 (High) | docker-compose pytest path | Containerized pytest still not packaging tests; backend image omits them so `docker compose run api pytest` is ineffective. | Keep noted; requires packaging tests or alternate CI path (deferred: would change image contents). |
| F4 | P2 (Medium) | Storage/seed pipeline (demo_seed.py) | Seeds may still drift without schema validation; idempotence limited to dedupe by course/question. | Further schema validation could help; defer pending toolchain approval. |
| F5 | P2 (Medium) | Observability | Limited logging around seed/escalation failures. | Suggest adding structured logging in future (deferred). |
| F6 | P1 (High) | Cross-environment dependency handling | Missing optional deps (pydantic-settings, slowapi, transformers, sentence-transformers, email-validator, qdrant-client) and Python 3.7 built-ins caused import-time crashes and empty responses. | Add graceful fallbacks for settings, rate limiting, embeddings/generation, Qdrant client, email validation, and py3.7-safe annotations (FIXED). |
| F7 | P1 (High) | Vector storage stub | In-memory Qdrant stub overwrote prior points on upsert, breaking course filtering and citations. | Append points instead of replacing; add course-aware fallbacks for retrieval (FIXED). |
| F8 | P1 (High) | Export endpoint compatibility | Use of `.removesuffix` and union types broke `/admin/export` on Python 3.7 runtimes. | Replace with compatible string handling and Optional typing (FIXED). |

# Quality Scorecard (0–5)
- Stability: 3.0 (demo mode stable; missing test execution in container)
- Maintainability: 3.3 (improved escalation validation/dedupe; seed/storage still light)
- Architecture: 3.0 (layered services/routes; demo shortcuts intermixed)
- Tests: 2.8 (new escalation store tests; container image still lacks tests)
- Dependency hygiene: 2.5 (no audit run; demo secrets embedded)
- Documentation (excluding README): 3.0 (security docs exist; architecture docs light)

# What Changed (this pass)
- Hardened settings/rate limiting/model loading to tolerate missing optional deps and older Python (fallback BaseSettings, SlowAPI stubs, transformer/embedding fallbacks).
- Repaired retrieval pipeline for missing Qdrant by adding robust in-memory client, keyword-aware fallback chunks, and course-specific guardrails.
- Fixed export/instructor routes and tests for Python 3.7 compatibility (no `removesuffix`, Optional/List typing).
- Added coverage for model fallbacks and ensured fixtures/cleanup are Py3.7-safe.

# Validation (existing commands)
- `npm run lint` (pass)
- `docker compose -f docker/docker-compose.yml build api web --no-cache` (pass)
- `pytest` (pass in host environment with fallbacks)
- `docker compose -f docker/docker-compose.yml run --rm api pytest` (fails: no tests in image; see F3)
- `docker compose -f docker/docker-compose.yml up -d` (pass; web/api/qdrant healthy)

# Optional Refactors (not implemented)
- Package backend tests into the docker api image and chown /app to the non-root user so pytest can run in CI; document as migration note once approved.
- Introduce explicit env gating for demo-only flags (disable by default outside demo) to reduce accidental exposure.

# Fixes Applied
- Escalation append now validates required fields and course existence; invalid status coerced to allowed set; duplicate submissions dedupe on (course_id, question_id) (backend/app/services/escalations.py).
- Escalation request API returns 400 on validation errors surfaced from service; email validation now lightweight and dependency-free (backend/app/api/routes/feedback.py, backend/app/schemas/feedback.py).
- Implemented dependency-safe BaseSettings and SlowAPI/transformers fallbacks; ensured exports and instructors routes use Optional/List typing for Python 3.7 (backend/app/settings.py, backend/app/limiting.py, backend/app/main.py, backend/app/api/routes/export.py, backend/app/api/routes/admin.py, backend/app/api/routes/instructors.py, backend/app/api/deps.py).
- Added resilient embedding/generation loaders with dummy encoders, extractive fallback, and safer summarization (backend/app/models/embeddings.py, backend/app/models/generate.py).
- Rebuilt in-memory Qdrant stub to retain points, honor filters, and supply course-aware fallback retrieval plus dataset sync (backend/app/rag/qdrant_utils.py, backend/app/rag/retrieve.py, backend/app/rag/ingest.py).
- Made test fixtures and API cleanup Py3.7-safe (tests/conftest.py, tests/test_api.py, tests/test_escalation_security.py, tests/test_retrieval.py, tests/test_generate.py).
- Removed unused protobuf dependency from backend/requirements.txt to eliminate GHSA-7gcm-g887-7qv7 exposure flagged by pip-audit.
