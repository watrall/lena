# LENA Pilot Architecture Overview

```
                    +----------------------+
                    |      Learners &      |
                    |   Student Support    |
                    +----------+-----------+
                               |
                        HTTPS (Netlify)
                               |
                +--------------v--------------+
                |      Next.js Frontend       |
                |  (Chat UI, FAQ, Insights)   |
                +--------------+--------------+
                               |
                        HTTPS / JSON
                               |
                +--------------v--------------+
                |        FastAPI Backend      |
                |  - /ask, /ingest, /feedback |
                |  - Hugging Face pipeline    |
                +--------------+--------------+
                               |
                +--------------v--------------+
                |        Qdrant Vector DB     |
                |  - Collection: lena_pilot   |
                |  - Semantic + metadata      |
                +--------------+--------------+
                               |
                +--------------v--------------+
                |        Data Storage         |
                |  - Markdown + ICS (data/)   |
                |  - Feedback queue (storage/)|
                +-----------------------------+
```

## Component Rationale

- **Next.js on Netlify** – Rapidly deployable static assets with serverless-friendly API proxying, giving the pilot a polished feel while remaining low maintenance.
- **FastAPI on DigitalOcean** – Python-first stack that pairs clean async APIs with rich ML ecosystem access (sentence-transformers, Hugging Face, Qdrant client).
- **Qdrant** – Lightweight vector database with cosine search, metadata filters, and CPU-only deployments; ideal for institution-managed VMs.
- **Sentence-Transformers** – `all-MiniLM-L6-v2` offers fast CPU embeddings that balance recall and latency, keeping pilot costs low.
- **Hugging Face Pipeline** – CPU text-generation pipeline (`zephyr-7b-beta`) can be toggled off for extractive-only mode while retaining consistent API responses.
- **Storage Layer** – Plain JSON/JSONL files simplify auditability during the pilot, and can be swapped for Postgres or S3 when scaling.

### Key API Routes

- `GET /courses` – feeds the course picker so every interaction has an explicit `course_id`.
- `POST /ask` – runs retrieval + generation for a question scoped to the chosen course.
- `POST /feedback` – records helpfulness along with the originating course and question text.
- `POST /escalations/request` – stores instructor follow-ups (learner name/email + question) in `storage/escalations.jsonl`.
- `GET /faq`, `GET /insights` – return course-filtered FAQ entries and the dashboard payload used by the frontend.

## Swapping Language Models

1. **Update environment variables**
   - Set `LENA_LLM_MODE=hf` to enable generative answers, or `LENA_LLM_MODE=off` for extractive-only responses.
   - Provide a new Hugging Face model via `LENA_HF_MODEL` (e.g., `Llama-2-7b-chat-hf`) and, if needed, adjust `LENA_HF_MAX_NEW_TOKENS`.
2. **Adjust hardware or inference backend**
   - For GPU-backed inference, mount the proper device into the Docker container or point `LENA_HF_MODEL` to an API endpoint (e.g., Hugging Face Inference Endpoints) and wrap it in `generate.py`.
3. **Validate prompt fit**
   - Update `backend/app/rag/prompts.py` to fine-tune instructions for the new model, ensuring it honors citation formatting.
4. **Regression test**
   - Run `POST /ask` against the smoke queries in `scripts/smoke_eval.py` (coming later in the roadmap) to confirm citation accuracy and confidence scoring.
