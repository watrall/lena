# Security Notes for LENA Pilot

## Pilot Guardrails
- **No authentication** – The pilot explicitly runs in “Pilot Mode — No login”. All users share the same experience, and no personal data is stored.
- **Sample data only** – Course materials in `data/` are synthetic or sanitized for demonstration. Replace with institution-approved redacted content before expanding.
- **Non-production storage** – Feedback and interactions persist in JSON/JSONL files under `storage/` to simplify audits. For production, migrate to a managed datastore with access controls.

## Data Handling
- **No PII collection** – Chat transcripts are not persisted; only aggregated interaction metadata (question id, confidence, helpfulness) is logged.
- **Escalations require consent** – When a learner opts into escalation, their name and email are written to `storage/escalations.jsonl` for instructor follow-up. Treat this file as sensitive, encrypt or restrict access, and purge it once each pilot wraps up.
- **Citations only** – All answers surface the source path so human reviewers can verify accuracy before acting.
- **Environment variables** – Secrets (e.g., API tokens if swapping LLM providers) should be injected via `.env` or deployment-specific secret managers, never committed to source.

## Deployment Considerations
- **TLS termination** – When hosting on DigitalOcean, place Nginx or a managed load balancer in front of FastAPI to terminate HTTPS.
- **Network segmentation** – Restrict Qdrant to private networking, allowing inbound traffic only from the FastAPI service.
- **Process isolation** – Run Docker services with non-root users where possible; the provided Dockerfiles can be hardened further by adding dedicated users and read-only filesystems.

## Example CORS Policy

When deploying the backend, enable FastAPI CORS middleware to restrict browser access to your approved domains:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://lena-pilot.netlify.app",
        "https://your-college-domain.edu",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    allow_credentials=False,
)
```

## Next Steps Before Production
1. Require SSO or institutional identity provider instead of “no login”.
2. Replace JSON storage with a database that supports access logging and backups.
3. Implement request rate limiting and reCAPTCHA or similar to mitigate automated abuse.
4. Expand CI to include dependency scanning and container image vulnerability checks.
