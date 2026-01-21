# Security Notes for LENA Pilot

## Security Features

### Rate Limiting
The `/ask` endpoint is rate-limited to **10 requests per minute per IP address** to prevent denial-of-service attacks and resource exhaustion from model inference.

Global default limit: 100 requests/minute per IP address.

### PII Encryption
Student PII (name, email) in escalation requests is encrypted at rest using Fernet symmetric encryption.

To enable encryption, generate and set a key:

```bash
# Generate a key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Set in environment
export LENA_ENCRYPTION_KEY="your-generated-key-here"

# Or add to .env file
echo "LENA_ENCRYPTION_KEY=your-generated-key-here" >> .env
```

**Note:** Without `LENA_ENCRYPTION_KEY`, PII is stored in plaintext with a warning logged.

PII export is disabled by default. To allow PII export, set both:
- `LENA_ENABLE_PII_EXPORT=true`
- `LENA_ENCRYPTION_KEY=...`

### API Documentation
OpenAPI docs (`/docs`, `/redoc`) are **disabled by default** for security. To enable for development:

```bash
export LENA_ENABLE_DOCS=true
```

## Pilot Guardrails
- **Student view is open** - Chat and Course FAQ do not require login in this pilot.
- **Instructor tools use demo authentication** - Insights, course management, ingest, review queue, and exports require a demo-only login. This is not production authentication or role-based access control.
- **Sample data only** - Course materials in `data/` are synthetic or sanitized for demonstration.
- **Non-production storage** - Feedback and interactions persist in JSON/JSONL files under `storage/`.

## Endpoint Hardening (Demo Pilots)
Even with the demo login, treat this as a no-auth pilot for deployment planning. The backend keeps higher-risk endpoints behind feature flags so operators can disable them by default and only enable them in controlled environments.

| Variable | Purpose | Default |
|----------|---------|---------|
| `LENA_ENABLE_INSTRUCTOR_AUTH` | Require demo instructor auth for instructor-only endpoints | `true` |
| `LENA_ENABLE_INGEST_ENDPOINT` | Enable `POST /ingest/run` | `false` |
| `LENA_ENABLE_ADMIN_ENDPOINTS` | Enable `GET /admin/review` + `POST /admin/promote` | `false` |
| `LENA_ENABLE_EXPORT_ENDPOINT` | Enable `GET /admin/export` | `false` |
| `LENA_ENABLE_PII_EXPORT` | Allow `include_pii=true` exports (requires encryption key) | `false` |

If you enable these endpoints, use additional deployment controls (VPN, IP allowlists, reverse-proxy gating).

## Data Handling
- **No PII in chat logs** - Chat transcripts are not persisted; only aggregated interaction metadata is logged.
- **Escalations require consent** - When a learner opts into escalation, their encrypted name and email are written to `storage/escalations.jsonl`.
- **Citations only** - All answers surface the source path for human verification.
- **Environment variables** - Secrets should be injected via `.env` or deployment-specific secret managers.

## Prompt Injection Mitigation

The RAG pipeline includes basic prompt injection defenses:
- Model instructions explicitly say to ignore override attempts
- User input is scanned for common injection patterns
- Suspicious inputs are wrapped with a `[User question]:` prefix

## Deployment Considerations
- **TLS termination** - Place Nginx or a managed load balancer in front of FastAPI for HTTPS.
- **Network segmentation** - Qdrant is configured with `expose` (internal only) in docker-compose.yml.
- **Process isolation** - Docker services run with `security_opt: no-new-privileges`.
- **Pinned versions** - All Docker images and Python packages use pinned versions.

## Example CORS Policy

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

## Dependency Security

Run regular security audits with pip-audit:

```bash
pip-audit -r backend/requirements.txt
```

All dependencies have been updated to address known CVEs as of January 2026.

## Environment Variables Reference

| Variable | Purpose | Default |
|----------|---------|---------|
| `LENA_ENCRYPTION_KEY` | Fernet key for PII encryption | None (plaintext) |
| `LENA_ENABLE_INSTRUCTOR_AUTH` | Require demo instructor auth for instructor-only endpoints | `true` |
| `LENA_ENABLE_INGEST_ENDPOINT` | Enable `POST /ingest/run` | `false` |
| `LENA_ENABLE_ADMIN_ENDPOINTS` | Enable admin endpoints | `false` |
| `LENA_ENABLE_EXPORT_ENDPOINT` | Enable `GET /admin/export` | `false` |
| `LENA_ENABLE_PII_EXPORT` | Allow PII export | `false` |
| `LENA_ENABLE_DOCS` | Enable OpenAPI documentation | `false` |
| `LENA_CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |

## Next Steps Before Production
1. Implement authentication via SSO or institutional identity provider.
2. Replace JSON storage with a database supporting access logging and backups.
3. Add CAPTCHA on the escalation form to prevent spam.
4. Enable structured logging and forward to a centralized log aggregator.
5. Set up automated dependency scanning in CI/CD pipeline.
