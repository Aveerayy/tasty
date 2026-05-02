from __future__ import annotations

import os
from collections.abc import Callable
from typing import Optional

from fastapi import Header, HTTPException


def _auth_enabled() -> bool:
    return os.getenv("AUTH_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}


def authorize(required_roles: set[str]) -> Callable[..., None]:
    def _authorize(
        x_api_key: Optional[str] = Header(default=None),
        x_actor_role: Optional[str] = Header(default=None),
    ) -> None:
        if not _auth_enabled():
            return

        expected_key = os.getenv("CONTROL_PLANE_API_KEY", "").strip()
        if not expected_key:
            raise HTTPException(status_code=500, detail="Auth enabled but CONTROL_PLANE_API_KEY is not configured")

        if not x_api_key or x_api_key != expected_key:
            raise HTTPException(status_code=401, detail="Invalid API key")

        role = (x_actor_role or "").strip().lower()
        if role not in required_roles:
            raise HTTPException(status_code=403, detail=f"Insufficient role; requires one of: {sorted(required_roles)}")

    return _authorize
