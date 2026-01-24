# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Stability
- Hardened escalation storage: validate required fields/course existence, coerce invalid statuses, and deduplicate duplicate escalation submissions.
- Documented current quality posture and command results in QUALITY_AUDIT; backend container pytest without tests remains noted.
- Pinned protobuf to 6.33.3 to avoid GHSA-7gcm-g887-7qv7 flagged by pip-audit.
- Added runtime fallbacks for missing optional dependencies (pydantic-settings, slowapi, transformers, sentence-transformers, email-validator, qdrant-client) and Python 3.7 compatibility to prevent startup crashes and empty responses.
- Fixed export endpoint compatibility by removing `.removesuffix` usage on Python 3.7 and guarding rate-limit stubs when SlowAPI is absent.

### Maintainability
- Added QUALITY_AUDIT with repo profile, findings, and scorecard to guide future hardening.
- Escalation input handling simplified and guarded, reducing bad data in storage/insights.
- In-memory Qdrant stub now appends points (no data loss) and retrieval includes course-aware fallbacks with keyword bias; ingestion syncs settings.data_dir for downstream fallbacks.
- Retrieval summarization now surfaces meaningful lines from chunks; generation fallback returns extractive answers when pipelines fail.

### Architecture
- Highlighted demo-only flags and secrets in compose as risks to address before non-demo deployments.

### Testing
- Added pytest coverage for escalation validation/dedup paths (runs via docker compose bind-mount).
- Added tests for embedding/generation fallbacks and py3.7-safe fixtures; cleanup helpers avoid missing_ok on older Python.
- Recorded existing test gap in containerized pytest run for follow-up (no toolchain changes applied).

## [v0.3.0] - 2026-01-21

### Added
- **Instructor tools** - Demo authentication for instructor-only pages, plus an integrated instructors hub for Insights and course management.
- **Course management** - Add/retire courses, upload course documents, and save link snapshots for ingestion without touching the server filesystem.
- **Data export** - Instructor-only export modal and backend export endpoints for JSON/CSV, with multi-course ZIP output and optional PII export controls.
- **Security hardening** - Additional guardrails for uploads and link snapshots (SSRF defenses), plus stronger defaults and rate limits for demo endpoints.

### Changed
- **UI polish** - Updated typography, surfaces, and visual consistency; improved instructor dashboard styling and chart theming.
- **Documentation** - Updated docs for demo auth + course_id requirements, refreshed screenshots, and aligned deployment notes.

### Fixed
- **Export reliability** - Correct file naming, content types, and demo seed data behavior for exports.

## [v0.2.1] - 2026-01-17

### Added
- **One-click start** - `start.sh` for local Docker startup and a README section describing the flow.

## [v0.2.0] - 2026-01-16

### Added
- **Multi-course support** - Course selection modal, persistence across sessions, and course-specific chat context.
- **Insights dashboard** - KPI cards, daily volume charts, confidence trends, escalations table, and pain points list for instructors.
- **Structured API architecture** - Dedicated route modules for chat, ingest, courses, feedback, insights, admin, and health endpoints.
- **Seed data system** - Script and sample data for interactions, escalations, and analytics to bootstrap new deployments.
- **FAQ page revamp** - Course-aware FAQ browsing with search functionality.
- **Docker Hub images** - Published `watrall/lena-backend` and `watrall/lena-web` images with pull count badges in README.

### Changed
- Refactored dependency injection and error handling across backend services.
- Improved course resolution logic with better error messages.
- Enhanced question recording and feedback mechanisms.
- Switched frontend to Tailwind CSS with production build configuration.
- Enabled standalone Next.js output for smaller container images.
- Updated analytics confidence trend calculation and review filtering logic.

### Fixed
- Escalation form accessibility and error handling improvements.
- Chat state now clears properly on course change.
- Type safety improvements across frontend components.

### Removed
- Unused dependencies: starlette, urllib3, filelock.

### Documentation
- Extensive README updates with setup instructions and Docker image references.
- Enhanced security notes on escalation data handling.
- Demo script updated with escalation example.
- Added screenshots directory.

## [v0.1.0] - 2024-03-01

### Added
- FastAPI backend with `/healthz`, `/ingest/run`, `/ask`, `/feedback`, `/faq`, `/insights`, and admin review endpoints.
- Retrieval-augmented ingestion pipeline that parses Markdown and ICS files, embeds with `sentence-transformers`, and stores vectors in Qdrant.
- Hugging Face text-generation pipeline with extractive fallback, citation packaging, and confidence scoring.
- Next.js frontend with chat interface, FAQ browsing, and pilot insights dashboard.
- Docker Compose stack wiring Qdrant, API, and web services with health checks and persistent storage mounts.
- GitHub Actions CI workflow covering backend pytest suite and frontend build.
- Documentation set including architecture overview, demo script, security notes, and screen placeholders.

### Notes
- Pilot is shared under MIT License. Chat and Course FAQ are open; instructor tools use demo authentication. Sample data only.
- See `deploy/DEPLOY_NOTES.md` for Netlify + DigitalOcean deployment guidance.
[v0.3.0]: https://github.com/watrall/lena/releases/tag/v0.3.0
[v0.2.1]: https://github.com/watrall/lena/releases/tag/v0.2.1
[v0.2.0]: https://github.com/watrall/lena/releases/tag/v0.2.0
[v0.1.0]: https://github.com/watrall/lena/releases/tag/v0.1.0
