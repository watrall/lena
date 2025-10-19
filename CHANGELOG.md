# Changelog

All notable changes to this project will be documented in this file.

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
- Pilot is shared under MIT License and runs in “Pilot Mode — No login. Sample data only.”
- See `deploy/DEPLOY_NOTES.md` for Netlify + DigitalOcean deployment guidance.

[v0.1.0]: https://github.com/OWNER/lena/releases/tag/v0.1.0
