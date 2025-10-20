[![CI][ci-badge]][ci-workflow]

# LENA – Learning Engagement & Navigation Assistant

LENA (Learner Engagement and Needs Assistant) is a lightweight AI chatbot pilot designed to support students in online courses. It helps learners get quick, accurate answers about assignments, schedules, and university policies, reducing instructor burden in high-enrollment classes and accelerating response times so students stay on track and succeed.

LENA isn’t meant to replace instructors. It handles common questions and points students toward resources, then automatically escalates anything it can’t answer to the instructor through Mattermost. Every question and interaction is logged, creating a feedback loop that helps instructors spot confusion early, adjust materials, and improve the course.

Students interact through a simple chat interface that works on desktop and mobile. Instructors and course admins can view real-time insights in an analytics dashboard—tracking trends, top questions, and emerging pain points across multiple courses. The pilot version is fully containerized (FastAPI backend + Next.js frontend + Qdrant vector store) and integrates with GitHub Actions for automated testing and builds.


- **Student view** – Ask a question, get a sourced answer.  
  - Each response links back to the syllabus, policy doc, or calendar event it pulled from.  
  - When the bot isn’t confident, it invites the student to escalate to the instructor and collects consented contact info.
- **Instructor view** – Review the course dashboard.  
  - KPI cards highlight volume, helpfulness, and escalations.  
  - Trend charts and emerging pain points call out what needs syllabus edits or follow-up announcements.
- **Admin / support staff** – Watch aggregate metrics across pilots, tune ingest jobs, and plug alerts into Mattermost or the LMS as needed.

---

## Stack at a Glance

- **Frontend** – Next.js (Pages router) + TypeScript + Tailwind, ships as a standalone Node server.
- **Backend** – FastAPI service that handles ingestion, retrieval, and the `/ask` workflow.
- **Vector store** – Qdrant (running inside Docker by default).
- **Notifications** – Optional Mattermost webhook for escalations/alerts (see env vars below).
- **CI** – GitHub Actions runs backend tests and a frontend build on every push / PR.

Directory map:

```
backend/     FastAPI app, embeddings, ingestion tasks
frontend/    Next.js pilot UI (chat, FAQ, insights)
docker/      Compose file booting qdrant + api + web
data/        Sample markdown + calendar sources for pilots
docs/        Architecture notes and support docs
storage/     Local persisted feedback, cached runs
```

---

## Quickstart (Docker)

```bash
git clone https://github.com/watrall/lena.git
cd lena
docker compose -f docker/docker-compose.yml up --build
```

Once the stack is up:

1. Seed content (optional but handy): `curl -X POST http://localhost:8000/ingest/run`
2. Open the chat: <http://localhost:3000> and ask “When is Assignment 1 due?”
3. Review metrics: <http://localhost:3000/insights>

If you change course data or want a clean slate, stop the stack and remove `storage/` before restarting.

---

## Local Development Notes

### Environment variables

Create a `.env` file at the repo root using `.env.example` as a guide.

| Variable | Description |
| --- | --- |
| `NEXT_PUBLIC_API_BASE` | Base URL the frontend calls (defaults to `http://localhost:8000`). |
| `LENA_QDRANT_HOST` / `LENA_QDRANT_PORT` | Qdrant connection details if you run the vector store elsewhere. |
| `LENA_DATA_DIR` / `LENA_STORAGE_DIR` | Override data or storage paths for ingestion/output. |
| `LENA_MATTERMOST_WEBHOOK` | Optional webhook to post instructor escalations into a Mattermost channel. |
| `LENA_LLM_MODE` | `hf` (default) to call a Hugging Face hosted model, or `off` for deterministic demos. |

The backend reads any `LENA_*` variables via Pydantic settings, while the frontend only needs the `NEXT_PUBLIC_*` keys because Next.js exposes them to the browser build.

### Running without Docker

Frontend:

```bash
cd frontend
npm ci
npm run dev
```

Backend:

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Ensure Qdrant is reachable (either `docker run qdrant/qdrant` or the docker compose stack) before hitting `/ask`.

---

## Docker Images

The LENA pilot publishes both backend and frontend containers for reproducibility and deployment.

| Service | Image | Technology | Description |
|----------|--------|-------------|--------------|
| **Backend** | [![Docker Hub](https://img.shields.io/badge/Docker%20Hub-lena--backend-blue?logo=docker)](https://hub.docker.com/repository/docker/watrall/lena-backend) | FastAPI | FastAPI backend for LENA AI—course Q&A, feedback, and analytics to support online learning. |
| **Frontend** | [![Docker Hub](https://img.shields.io/badge/Docker%20Hub-lena--web-blue?logo=docker)](https://hub.docker.com/repository/docker/watrall/lena-web) | Next.js | Next.js frontend for LENA AI—chat Q&A and learner analytics for online course support. |

### Pull and Run

To pull the latest images directly from Docker Hub:

```bash
# Backend (FastAPI)
docker pull docker.io/watrall/lena-backend:latest
docker run -d -p 8000:8000 docker.io/watrall/lena-backend:latest

# Frontend (Next.js)
docker pull docker.io/watrall/lena-web:latest
docker run -d -p 3000:3000 docker.io/watrall/lena-web:latest

```

Set `NEXT_PUBLIC_API_BASE=http://localhost:8000` (or your backend host) before starting the frontend container so the chat can reach the API.

---

## CORS & Production Considerations

- When deploying the frontend separately (Netlify, Vercel, etc.), set `BACKEND_CORS_ORIGINS` or the equivalent FastAPI middleware to include the web origin (e.g. `https://lena-pilot.example.edu`). The Compose stack already runs both services on the same network so no extra config is required locally.
- Mattermost, Slack, LMS, or email integrations should live behind opt-in environment flags so student data only routes to approved channels. The README keeps the defaults closed off; check `docs/SECURITY-NOTES.md` before rolling into a large cohort.

---

## Helpful Docs

- Architecture overview: `docs/OVERVIEW.md`
- Demo script for pilots: `docs/DEMO-SCRIPT.md`
- Security and guardrails: `docs/SECURITY-NOTES.md`
- Changelog: `CHANGELOG.md`

---

This codebase is released under the MIT License. See `LICENSE` for the fine print.

> Pilot status: ✅ Frontend + infra complete. Ready for instructor onboarding and live cohort trials.

---

## Provenance

This pilot was created inside an institution-wide initiative focused on applying AI responsibly across the curriculum to strengthen student learning and institutional outcomes. It launched within Department of Anthropology online courses, where we paired faculty, instructional designers, and technologists to make sure the guardrails matched pedagogical goals. After the initial run we migrated the codebase from the internal GitLab instance to GitHub to share the work openly and invite collaboration from the broader community.

[ci-badge]: https://github.com/watrall/lena/actions/workflows/ci.yml/badge.svg?branch=main
[ci-workflow]: https://github.com/watrall/lena/actions/workflows/ci.yml
