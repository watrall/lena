# LENA Pilot Demo Script (2–3 Minutes)

## 0. Setup (pre-demo)
- Terminal 1: `docker compose up --build` to start `api`, `web`, and `qdrant`.
- Terminal 2: Keep a shell ready to run `curl -X POST http://localhost:8000/ingest/run` whenever you want to refresh the corpus.
- Browser: Open `http://localhost:3000`.

## 1. Introduce the Pilot (20s)
> “LENA is our learning engagement assistant. This pilot runs in ‘no login’ mode, uses sample course data, and cites every answer so staff can trust but verify.”

Show the banner and navigation links (Chat, FAQ, Insights).

## 2. Ingest Knowledge Base (30s)
- Run `curl -X POST http://localhost:8000/ingest/run`.
- Narrate that Markdown syllabus, policy docs, and ICS calendar events are chunked, embedded, and stored in Qdrant.
- Point to the JSON response showing `{docs, chunks}` counts.

## 3. Ask Course Questions (45s)
- Select “ANTH 101 · Cultural Anthropology” (or your custom entry) when prompted to choose a course. Mention that every backend endpoint now enforces the `course_id`, keeping analytics aligned with the chat transcripts.
- In the chat UI, ask: “When is Assignment 1 due?”
- Highlight the response:
  - The natural-language answer.
  - Confidence indicator.
  - Source list with file paths (e.g., `assignments.md`, `schedule.ics`).
- Follow-up with “What is the late policy?” and note the citation from policy documents.
- If the answer flags an escalation opportunity, open the follow-up form, submit the student details, and call out that it POSTs to `/escalations/request`, writing to `storage/escalations.jsonl` for instructor handoff. You can mirror it via terminal too:

```bash
curl -X POST http://localhost:8000/escalations/request \
  -H "Content-Type: application/json" \
  -d '{"question_id":"<id>","question":"Need clarification on Assignment 2","student_name":"Jordan","student_email":"jordan@example.edu","course_id":"anth101"}'
```

## 4. Capture Feedback (30s)
- Mark the late-policy answer as “Not helpful”.
- Mention that the backend writes to `storage/review_queue.jsonl` and records the event in `storage/interactions.jsonl`.

- Call `curl http://localhost:8000/admin/review` to show the queued feedback item.
- Promote it: `curl -X POST http://localhost:8000/admin/promote -d '{"queue_id":"<id>","answer":"Late submissions lose 10% within 48 hours."}' -H "Content-Type: application/json"`.
- Refresh the `/faq` page and show the newly added entry.

## 6. Share Insights (20s)
- Open `/insights` to display total questions, helpful rate, and average confidence.
- Emphasize that these metrics help the course team identify when to escalate or update content.

## 7. Close (15s)
> “Because everything is Dockerized, we can deploy the frontend to Netlify and the backend with Qdrant to a DigitalOcean VM. The same health checks and CI workflow stay in place, so we’re ready for a scaled pilot.”
