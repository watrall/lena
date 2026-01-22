# Security Verification Guide

## Prerequisites
- Python ≥3.10 recommended (required for `typing.Literal` and project deps).
- Node.js ≥18 for frontend tooling.
- Set environment secrets before running tests:  
  - `LENA_ENCRYPTION_KEY` (Fernet key)  
  - `LENA_INSTRUCTOR_AUTH_SECRET` (non-default secret)

## Commands
Run from repo root unless noted.

1) Python SAST  
   `bandit -r backend/app -q`

2) Python dependency audit (offline collection, no installs)  
   `python3 -m pip_audit -r backend/requirements.txt --disable-pip --no-deps -s osv`

3) Frontend dependency audit  
   `cd frontend && npm audit --omit=dev`

4) Security regression tests (encryption enforcement)  
   ```
   export LENA_INSTRUCTOR_AUTH_SECRET=changeme-super-secret
   export LENA_ENCRYPTION_KEY=$(python3 - <<'PY'
   from cryptography.fernet import Fernet
   print(Fernet.generate_key().decode())
   PY
   )
   python3 -m pip install -r backend/requirements.txt  # installs test deps
   python3 -m pytest tests/test_escalation_security.py -q
   ```
   Note: requires Python ≥3.10; on Python 3.7 the current environment lacks `pydantic_settings`.

## Current Status
- bandit: pass
- pip_audit: pass
- npm audit (omit dev): pass
- pytest (security): **blocked in this environment** — missing Python deps; expected to pass once deps installed on supported Python version.
