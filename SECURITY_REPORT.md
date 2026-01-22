# Security Report

## Baseline
- Baseline `git status`: clean before changes (22 Jan 2026, current branch).
- README files were **not modified** (protected).

## System Map
- **Components**: FastAPI backend (LLM/RAG, instructor admin, escalations); Next.js frontend (student chat, instructor UI); supporting scripts; Docker compose for Qdrant.
- **Trust boundaries**: Browser ↔ Next.js; Next.js ↔ FastAPI (JSON, CORS); FastAPI ↔ storage (JSON/JSONL on disk) and Qdrant; instructor endpoints require demo bearer auth; student chat intentionally unauthenticated.
- **Sensitive data**: Student names/emails in escalations; course content; interaction logs; exports with optional PII.

## Commands Run
| Command | Purpose | Result | Key findings |
| --- | --- | --- | --- |
| `bandit -r backend/app -q` | Python SAST | Pass (no findings after fixes) | Previously flagged SHA1; resolved. |
| `python3 -m pip_audit -r backend/requirements.txt --disable-pip --no-deps -s osv` | Python dependency CVEs | Pass | No known vulns. |
| `npm audit --omit=dev` (frontend) | JS dependency CVEs | Pass | 0 vulnerabilities. |
| `python3 -m pytest tests/test_escalation_security.py -q` | Security regression tests | Fail (env) | Missing Python deps in env (pydantic_settings); see Verification. |

## Findings and Status
- **F-01 High (A01/A02)**: Tracked PII/runtime data in `storage/*.json*` exposed student emails. **Fixed** (files removed; `.gitkeep` only).
- **F-02 High (A04/A01)**: Escalations stored PII unencrypted when `LENA_ENCRYPTION_KEY` absent. **Fixed** (encryption now mandatory; clear error if unset; tests added).
- **F-03 Medium (A07/A02)**: Demo instructor secret default is weak; requires operator override. **Documented**; not enforced here to avoid breaking current flows. Mitigate by setting `LENA_INSTRUCTOR_AUTH_SECRET`. 
- **F-04 Medium (A02)**: Test environment on Python 3.7 missing deps; security test could not run. Documented; install deps or use Python ≥3.10 to run full suite.

## OWASP Top 10:2025 Matrix
| Category | Applicable | Status | Evidence / Findings | Remediation |
| --- | --- | --- | --- | --- |
| A01 Broken Access Control | Y | Partial | Instructor endpoints gated; student chat open by design. F-01 data exposure. | Removed tracked PII; instructor auth reminder. |
| A02 Security Misconfiguration | Y | Partial | CORS configured; hardening headers; storage had tracked PII; env key missing blocked tests. | Cleanup storage; enforce encryption. |
| A03 Software Supply Chain Failures | Y | Pass | `npm audit`, `pip_audit` clean; lockfiles present. | Continue routine audits. |
| A04 Cryptographic Failures | Y | Partial→Improved | PII encryption previously optional. | Encryption now mandatory for escalations. |
| A05 Injection | Y | Pass | No dynamic SQL; Pydantic validation; no findings. | Monitor. |
| A06 Insecure Design | Y | Partial | Demo auth/PII storage design noted. | Mandatory encryption; doc guidance. |
| A07 Authentication Failures | Y | Partial | Demo instructor auth; weak default secret noted. | Require strong secret operationally. |
| A08 Software or Data Integrity Failures | Y | Pass | No unsigned updates; exports guarded. | N/A |
| A09 Security Logging & Alerting Failures | Y | Partial | Analytics events exist; no central alerting. | Recommend SIEM hookup (not implemented). |
| A10 Mishandling of Exceptional Conditions | Y | Partial | New explicit error on missing encryption key; general error handling adequate. | Continue to guard large uploads/timeouts. |

## Verification Summary
- Security tests added; could not run locally due to missing Python deps (pydantic_settings) on Python 3.7. See SECURITY_VERIFICATION.md for steps.
- All automated security scans listed above currently pass.
