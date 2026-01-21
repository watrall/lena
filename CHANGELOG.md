# Changelog

All notable changes to this project will be documented in this file.

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
- Pilot is shared under MIT License and runs in "Pilot Mode - No login. Sample data only."
- See `deploy/DEPLOY_NOTES.md` for Netlify + DigitalOcean deployment guidance.
[v0.2.0]: https://github.com/watrall/lena/releases/tag/v0.2.0[v0.1.0]: https://github.com/watrall/lena/releases/tag/v0.1.0
