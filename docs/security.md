# Security Guide

## Deployment Posture
- Demo Docker compose exposes web on 3000 and api on 8000; qdrant internal only. Demo flags enable ingest/export/admin and seed data; disable in production.
- Store secrets (e.g., `LENA_ENCRYPTION_KEY`, instructor credentials) in environment variables or secret manager; do not hardcode.

## Data Protection
- Escalations include student name/email; set `LENA_ENCRYPTION_KEY` for at-rest encryption in `storage/`.
- Avoid enabling `LENA_ENABLE_PII_EXPORT` unless required and access-controlled.

## Access Control
- Instructor tools use demo bearer tokens; replace with real auth (MFA/SSO) before production.
- Student chat is intentionally unauthenticated in demo; gate it behind course/session auth for real deployments.

## Recommended CI Gates
1. `npm run lint && npm run build` (frontend)
2. `pytest` (backend)
3. Dependency audits: `npm audit --production`, `pip-audit`
4. Secrets scan (e.g., gitleaks)

## Operational Checklist (Prod)
- Disable demo seed flags and admin/export endpoints unless needed.
- Provide unique per-env encryption key via env var.
- Rotate any demo/shared credentials; enforce strong password/MFA.
- Enable HTTPS termination and security headers at the ingress.
- Monitor auth/admin endpoints; alert on failures and privilege changes.

