# Security Posture and Operational Guidance

- **PII protection**: Escalation storage now *requires* `LENA_ENCRYPTION_KEY`. Without it, requests fail to prevent plaintext writes. Generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.
- **Instructor auth**: Demo-only bearer tokens; operators must set strong `LENA_INSTRUCTOR_AUTH_SECRET` (and credentials) in production.
- **Data at rest**: Runtime artifacts (interactions, escalations, FAQs, review queue) are no longer tracked in Git. `storage/.gitkeep` keeps the directory only.
- **Exports**: PII exports remain opt-in and require encryption to be configured.
- **Rate limiting & headers**: SlowAPI limits are enabled; basic security headers and request-size guardrails are set in `backend/app/main.py`.
- **Allowed origins/hosts**: Configure `LENA_CORS_ORIGINS` and `LENA_TRUSTED_HOSTS` for your deployment.
- **Verification**: See `SECURITY_VERIFICATION.md` for commands (bandit, pip_audit, npm audit, security tests).
- **Known gaps**: Centralized logging/alerting and SIEM integration are not yet implemented; demo auth should be replaced for production.
