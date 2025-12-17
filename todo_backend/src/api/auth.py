from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from .settings import get_settings

_security = HTTPBasic(auto_error=False)


# PUBLIC_INTERFACE
def get_basic_auth_dependency():
    """
    Return a FastAPI dependency callable that enforces HTTP Basic Auth only when
    ENABLE_BASIC_AUTH is enabled in settings. When disabled, the dependency is a no-op.

    Behavior:
    - If settings.enable_basic_auth is False (default): returns a dependency that does nothing.
    - If True: validates provided credentials against BASIC_AUTH_USERNAME/BASIC_AUTH_PASSWORD.
      If credentials are missing or invalid, raises 401 with WWW-Authenticate: Basic.

    Usage:
        from .auth import get_basic_auth_dependency
        auth_dep = get_basic_auth_dependency()
        router = APIRouter(dependencies=[Depends(auth_dep)])
        @app.get("/", dependencies=[Depends(auth_dep)]) ...
    """
    settings = get_settings()

    # If basic auth is disabled, return a no-op dependency
    if not settings.enable_basic_auth:
        async def _noop() -> None:  # noqa: D401 - trivial
            """No-op dependency (auth disabled)."""
            return None

        return _noop

    # When enabled, require credentials and verify them
    expected_user: Optional[str] = settings.basic_auth_username
    expected_pass: Optional[str] = settings.basic_auth_password

    async def _enforce(creds: Optional[HTTPBasicCredentials] = Depends(_security)) -> None:
        """
        Enforce HTTP Basic authentication when enabled.

        Raises:
            HTTPException(401) if credentials are missing or invalid.
        """
        # If security scheme didn't parse credentials or none were sent
        if creds is None or creds.username is None or creds.password is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Basic"},
            )

        if expected_user is None or expected_pass is None:
            # Misconfiguration: auth enabled but username/password not provided
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Server authentication not configured",
                headers={"WWW-Authenticate": "Basic"},
            )

        if not (creds.username == expected_user and creds.password == expected_pass):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Basic"},
            )
        # On success, return None (allow request to proceed)

    return _enforce
