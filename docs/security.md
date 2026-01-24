# Security Guide

## Deployment Posture
- Demo Docker compose exposes web on 3000 and api on 8000; qdrant internal only. Demo flags enable ingest/export/admin and seed data; disable in production.
- Store secrets (e.g., `LENA_ENCRYPTION_KEY`, instructor credentials) in environment variables or secret manager; do not hardcode. Rotate any demo values before non-demo use.
- Install optional dependencies (pydantic-settings, slowapi, transformers, sentence-transformers, qdrant-client) in production images to avoid relying on minimal fallbacks.

## Data Protection
- Escalations include student name/email; set `LENA_ENCRYPTION_KEY` for at-rest encryption in `storage/`.
- Avoid enabling `LENA_ENABLE_PII_EXPORT` unless required and access-controlled.
- Validate course IDs and emails at the API boundary (already enforced in code); reject unknown courses to prevent orphaned PII.

## Access Control
- Instructor tools use demo bearer tokens; replace with real auth (MFA/SSO) before production.
- Student chat is intentionally unauthenticated in demo; gate it behind course/session auth for real deployments.

## Recommended CI Gates
1. `npm run lint && npm run build` (frontend)
2. `pytest` (backend) — ensure tests are present in the container or mounted in CI.
3. Dependency audits: `npm audit --production`, `pip-audit` (install tool in CI runner)
4. Secrets scan (e.g., gitleaks)

## Operational Checklist (Prod)
- Disable demo seed flags and admin/export endpoints unless needed.
- Provide unique per-env encryption key via env var.
- Rotate any demo/shared credentials; enforce strong password/MFA.
- Enable HTTPS termination and security headers at the ingress.
- Monitor auth/admin endpoints; alert on failures and privilege changes.
- Run CI audits and tests on the same Python/Node versions you ship; avoid Python 3.7 in production (supported only for compatibility testing).
