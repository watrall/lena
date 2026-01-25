"""Demo instructor authentication utilities.

This is intentionally simple and intended ONLY for demoing authentication and
role-based access flows. It is not a production auth system.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from ..settings import settings


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64url_decode(text: str) -> bytes:
    padding = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode((text + padding).encode("utf-8"))


def _load_or_create_secret() -> str:
    """Use a persisted secret when the default demo value is present."""
    if settings.instructor_auth_secret != "demo-secret-change-me":
        return settings.instructor_auth_secret

    key_path = Path(settings.storage_dir) / "instructor_secret.key"
    try:
        if key_path.exists():
            saved = key_path.read_text(encoding="utf-8").strip()
            if saved:
                return saved
        new_secret = base64.urlsafe_b64encode(os.urandom(32)).decode("utf-8").rstrip("=")
        key_path.write_text(new_secret, encoding="utf-8")
        try:
            os.chmod(key_path, 0o600)
        except OSError:
            pass
        return new_secret
    except Exception:
        return settings.instructor_auth_secret


def _sign(message: bytes) -> str:
    secret = _load_or_create_secret().encode("utf-8")
    return _b64url_encode(hmac.new(secret, message, hashlib.sha256).digest())


def issue_token(username: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(seconds=settings.instructor_token_ttl_seconds)
    payload = {"sub": username, "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
    body = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    sig = _sign(body.encode("utf-8"))
    # token_type is OAuth-style metadata, not a password. (bandit false positive)
    return {
        "access_token": f"{body}.{sig}",
        "token_type": "bearer",  # nosec B105
        "expires_at": exp.isoformat().replace("+00:00", "Z"),
    }


def verify_token(token: str) -> Dict[str, Any] | None:
    try:
        body, sig = token.split(".", 1)
    except ValueError:
        return None
    expected = _sign(body.encode("utf-8"))
    if not hmac.compare_digest(sig, expected):
        return None
    try:
        payload = json.loads(_b64url_decode(body))
    except Exception:
        return None
    exp = payload.get("exp")
    if not isinstance(exp, int):
        return None
    if datetime.now(timezone.utc).timestamp() > exp:
        return None
    return payload


def check_credentials(username: str, password: str) -> bool:
    # Constant-time comparisons to reduce trivial timing differences.
    using_defaults = (
        settings.instructor_username == "demo" and settings.instructor_password == "demo"
    )
    if using_defaults and not settings.allow_default_instructor_creds:
        return False
    return hmac.compare_digest(username, settings.instructor_username) and hmac.compare_digest(
        password, settings.instructor_password
    )
