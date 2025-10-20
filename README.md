# LENA – Learning Engagement & Navigation Assistant

[![CI][ci-badge]][ci-workflow]

LENA is our course-aware AI teammate. It sits between students and instructors to answer the routine questions, surface helpful context, and flag the messy threads that still need a human touch. The pilot runs in “no login” mode so we can iterate quickly with real classes.

- **Student view** – Ask a question, get a sourced answer (see the [chat walkthrough](docs/screens/chat.png)).  
  - Each response links back to the syllabus, policy doc, or calendar event it pulled from.  
  - When the bot isn’t confident, it invites the student to escalate to the instructor and collects consented contact info.
- **Instructor view** – Review the course dashboard (peek at [insights](docs/screens/insights.png)).  
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
docs/        Architecture notes, demo script, screenshots
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

[ci-badge]: https://github.com/watrall/lena/actions/workflows/ci.yml/badge.svg
[ci-workflow]: https://github.com/watrall/lena/actions/workflows/ci.yml
