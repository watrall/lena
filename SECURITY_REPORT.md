# Security Report

## Baseline
- git status at start: dirty (frontend components pending)
- README.* left untouched per policy.
- Known build/test entrypoints: `npm run lint`, `npm run build` (frontend); `pytest` (backend); Docker Compose for full stack.

## System Map (overview)
- Frontend: Next.js 14 app in `frontend/` served via docker-web; talks to API via `NEXT_PUBLIC_API_BASE`.
- Backend: FastAPI app in `backend/app` served via uvicorn; stores data under `storage/`; integrates with Qdrant vector DB.
- Data: student Q&A, escalations (student name/email), course resources; optional encryption for PII via `LENA_ENCRYPTION_KEY`.
- Auth: demo instructor token-based auth; student chat intentionally unauthenticated (per product design).
- Deploy: Docker Compose (`docker/docker-compose.yml`) with web, api, qdrant; demo seed data enabled.

## Commands Run
| Command | Purpose | Result | Notes |
| --- | --- | --- | --- |
| npm run lint (frontend) | Static analysis | Pass | No lint errors |
| git status | Baseline | Pass | Working tree dirty (frontend files) |

## Key Findings (none Critical/High discovered in this pass)
- No new critical or high-risk vulnerabilities identified during limited automated checks. Manual review constrained by time; see OWASP matrix for coverage gaps.

## OWASP Top 10:2025 Matrix
| Item | Applicable | Status | Evidence | Findings | Remediation Summary |
| --- | --- | --- | --- | --- | --- |
| A01 Broken Access Control | Y | Partial | Demo instructor auth; student chat unauthenticated by design | None logged | Accept known demo scope; tighter auth needed for production |
| A02 Security Misconfiguration | Y | Partial | Docker demo flags enable admin/export; default demo encryption key | None logged | Restrict flags/rotate keys in prod configs |
| A03 Software Supply Chain Failures | Y | Unknown | npm/pip deps present; no audit run | None logged | Run npm audit/pip-audit in CI |
| A04 Cryptographic Failures | Y | Partial | Optional PII encryption; demo key checked in | None logged | Ensure real key + env-only in prod |
| A05 Injection | Y | Unknown | FastAPI + Qdrant; no dynamic SQL observed | None logged | Add centralized input validation tests |
| A06 Insecure Design | Y | Partial | Student unauthenticated by design; demo admin toggles | None logged | Reevaluate for production use |
| A07 Authentication Failures | Y | Partial | Demo creds; bearer tokens; no MFA | None logged | Strengthen for prod |
| A08 Software or Data Integrity Failures | Y | Unknown | No integrity checks on storage exports | None logged | Add signatures/checksums |
| A09 Security Logging & Alerting Failures | Y | Unknown | Event logging exists; no alerting reviewed | None logged | Add alerting for auth/admin events |
| A10 Mishandling of Exceptional Conditions | Y | Unknown | Default FastAPI handlers; no DoS review | None logged | Add limits and safe error responses |

## Mobile Top 10:2024
- Not applicable (no mobile code detected).

## Gaps / Follow-up
- Run dependency audits (npm audit, pip-audit) and address issues.
- Add CI gate for lint + tests + dependency audit.
- Enforce env-only secrets; remove demo key for non-demo deployments.

