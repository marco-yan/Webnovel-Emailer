from __future__ import annotations

import hmac
import os


def require_access_key(provided: str | None) -> None:
    expected = (os.environ.get("APP_ACCESS_KEY") or "").strip()
    if not expected:
        raise RuntimeError("APP_ACCESS_KEY is not configured on this deployment")

    supplied = (provided or "").strip()
    if not supplied or not hmac.compare_digest(supplied, expected):
        raise PermissionError("Invalid access code")
