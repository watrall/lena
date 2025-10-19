# LENA (Learning Engagement and Navigation Assistant)

[![CI][ci-badge]][ci-workflow]

_Pilot Mode — No login. Sample data only._

**Note:** This public repository is a cleaned and adapted version of the original *LENA* project, initially developed and hosted on my institution’s internal GitLab instance as part of an AI-enabled learner support pilot.  
This GitHub version is shared for demonstration and discussion purposes in the context of professional applications related to AI-driven education, learner support, and responsible innovation.

LENA (Learning Engagement and Navigation Assistant) is a retrieval-augmented chatbot that helps learners and academic staff navigate course policies, schedules, and support resources with grounded citations, feedback workflows, and lightweight insights suitable for pilot deployments.

## Run in 60 seconds

1. Clone the repo and ensure Docker Desktop is running.
2. `docker compose up --build` – starts FastAPI, Qdrant, and the Next.js web UI.
3. `curl -X POST http://localhost:8000/ingest/run` – loads sample markdown and calendar data into Qdrant.
4. Visit `http://localhost:3000` – ask “When is Assignment 1 due?” and verify the cited answer.

## Deployment

- **Local pilot** – use the Docker Compose stack (`docker/docker-compose.yml`) for development. Storage lives under `storage/` so feedback survives restarts.
- **Netlify + DigitalOcean** – follow `deploy/DEPLOY_NOTES.md` to host the frontend on Netlify and the FastAPI + Qdrant stack on a DigitalOcean Droplet.
- **CORS & Security** – see `docs/SECURITY-NOTES.md` for pilot guardrails, CORS middleware example, and next steps before production.

## Repository layout

- `backend/` – FastAPI application and RAG services.
- `frontend/` – Next.js chat interface.
- `docker/` – Docker Compose and container helpers.
- `data/` – Sample markdown and calendar content for ingestion.
- `docs/` – Project documentation and diagrams.
- `.github/workflows/` – Continuous integration pipelines.

## License

This project is licensed under the MIT License. See `LICENSE` for details.

---

- Architecture deep dive: `docs/OVERVIEW.md`
- Demo flow and script: `docs/DEMO-SCRIPT.md`
- Changelog: `CHANGELOG.md`

[ci-badge]: https://github.com/OWNER/lena/actions/workflows/ci.yml/badge.svg
[ci-workflow]: https://github.com/OWNER/lena/actions/workflows/ci.yml
