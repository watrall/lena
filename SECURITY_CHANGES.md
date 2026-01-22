# Security Changes

## Overview
Security remediation focused on eliminating stored PII, enforcing encryption for escalations, and adding regression coverage and guidance. README files were not modified.

## Changes by Severity
- **High**  
  - Removed tracked PII/runtime artifacts from `storage/`.  
  - Made PII encryption mandatory for escalation storage; clear error when key missing.
- **Medium**  
  - Added Python 3.7 compatibility shim for `Literal` import to allow local tooling.  
  - Added regression tests for escalation encryption requirement.

## Changes by Area
- **Crypto / Data Protection**: Encryption required for student PII in escalations; legacy plaintext artifacts removed.  
- **Config / Misconfiguration**: Runtime now refuses to write PII without `LENA_ENCRYPTION_KEY`.  
- **Tests / Regression Guards**: Added pytest coverage for encryption enforcement.  
- **Docs**: Added security reports and verification guides (non-README).

## File-by-File Change List
- `backend/app/services/crypto.py` — encryption now mandatory; raises if key missing (OWASP A04).  
- `backend/app/api/routes/feedback.py` — escalations endpoint surfaces clear error when encryption key absent (A10/A04).  
- `backend/app/settings.py` — typing import shim for Python 3.7 tooling (compatibility).  
- `storage/*.json*` — removed tracked PII/runtime data; added `storage/.gitkeep` (A01/A02).  
- `tests/test_escalation_security.py` — new regression tests enforcing encryption requirement (A04/A01).  
- `SECURITY_REPORT.md`, `SECURITY_VERIFICATION.md`, `SECURITY_CHANGES.md`, `docs/security.md` — added security posture, verification steps, and change log (A02/A06).

## Commands Executed
- `git status --porcelain`
- `bandit -r backend/app -q`
- `python3 -m pip_audit -r backend/requirements.txt --disable-pip --no-deps -s osv`
- `npm audit --omit=dev`
- `python3 -m pytest tests/test_escalation_security.py -q` (failed: missing deps in local Python 3.7)

## README Pending Items
- None. README files remain unchanged. No README_CHANGE_PROPOSAL.md needed.
