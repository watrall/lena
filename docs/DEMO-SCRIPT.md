# LENA Pilot Demo Script (2–3 Minutes)

## 0. Setup (pre-demo)
- Terminal 1: `docker compose up --build` to start `api`, `web`, and `qdrant`.
- Terminal 2: `docker compose exec api python -m app.scripts.bootstrap` *(optional later)* or keep ready for ingestion call.
- Browser: Open `http://localhost:3000`.

## 1. Introduce the Pilot (20s)
> “LENA is our learning engagement assistant. This pilot runs in ‘no login’ mode, uses sample course data, and cites every answer so staff can trust but verify.”

Show the banner and navigation links (Chat, FAQ, Insights).

## 2. Ingest Knowledge Base (30s)
- Run `curl -X POST http://localhost:8000/ingest/run`.
- Narrate that Markdown syllabus, policy docs, and ICS calendar events are chunked, embedded, and stored in Qdrant.
- Point to the JSON response showing `{docs, chunks}` counts.

## 3. Ask Course Questions (45s)
- In the chat UI, ask: “When is Assignment 1 due?”
- Highlight the response:
  - The natural-language answer.
  - Confidence indicator.
  - Source list with file paths (e.g., `assignments.md`, `schedule.ics`).
- Follow-up with “What is the late policy?” and note the citation from policy documents.

## 4. Capture Feedback (30s)
- Mark the late-policy answer as “Not helpful”.
- Mention that the backend writes to `storage/review_queue.jsonl` and records the event in `storage/interactions.jsonl`.

## 5. Promote to FAQ (30s)
- Call `curl http://localhost:8000/admin/review` to show the queued feedback item.
- Promote it: `curl -X POST http://localhost:8000/admin/promote -d '{"queue_id":"<id>","answer":"Late submissions lose 10% within 48 hours."}' -H "Content-Type: application/json"`.
- Refresh the `/faq` page and show the newly added entry.

## 6. Share Insights (20s)
- Open `/insights` to display total questions, helpful rate, and average confidence.
- Emphasize that these metrics help the course team identify when to escalate or update content.

## 7. Close (15s)
> “Because everything is Dockerized, we can deploy the frontend to Netlify and the backend with Qdrant to a DigitalOcean VM. The same health checks and CI workflow stay in place, so we’re ready for a scaled pilot.”
