from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class Settings:
    """
    Application settings loaded from environment variables.

    Env vars:
    - PERSISTENCE_BACKEND: 'memory' (default) or 'sqlite'
    - SQLITE_DB_PATH: path to sqlite db file. Default './data/todos.db'
    - CORS_ALLOW_ORIGINS: comma-separated list of allowed origins; '*' by default
    - ENABLE_BASIC_AUTH: 'true' to enable optional HTTP Basic Auth (default: false)
    - BASIC_AUTH_USERNAME: username for basic auth (required when ENABLE_BASIC_AUTH=true)
    - BASIC_AUTH_PASSWORD: password for basic auth (required when ENABLE_BASIC_AUTH=true)
    """

    persistence_backend: str
    sqlite_db_path: str
    cors_allow_origins: List[str]
    enable_basic_auth: bool
    basic_auth_username: Optional[str]
    basic_auth_password: Optional[str]


def _get_env(name: str, default: str) -> str:
    value = os.getenv(name, default)
    if value is None or value == "":
        return default
    return value


def _parse_bool(value: str, default: bool = False) -> bool:
    v = value.strip().lower()
    if v in {"1", "true", "yes", "on"}:
        return True
    if v in {"0", "false", "no", "off"}:
        return False
    return default


def _parse_origins(origins_value: str) -> List[str]:
    """
    Parse CORS origins from env. Supports:
    - '*' to allow all origins
    - Comma-separated list of origins
    """
    value = origins_value.strip()
    if value == "*":
        # Star will be handled in main via allow_origins=["*"]
        return ["*"]
    return [o.strip() for o in value.split(",") if o.strip()]


# PUBLIC_INTERFACE
def get_settings() -> Settings:
    """Return application settings loaded from environment variables."""
    backend = _get_env("PERSISTENCE_BACKEND", "memory").strip().lower()
    if backend not in {"memory", "sqlite"}:
        # Fallback to memory if unsupported
        backend = "memory"

    sqlite_path = _get_env("SQLITE_DB_PATH", "./data/todos.db").strip()
    cors_raw = _get_env("CORS_ALLOW_ORIGINS", "*")
    origins = _parse_origins(cors_raw)

    enable_basic_auth = _parse_bool(_get_env("ENABLE_BASIC_AUTH", "false"), False)
    basic_user = os.getenv("BASIC_AUTH_USERNAME") if enable_basic_auth else None
    basic_pass = os.getenv("BASIC_AUTH_PASSWORD") if enable_basic_auth else None

    return Settings(
        persistence_backend=backend,
        sqlite_db_path=sqlite_path,
        cors_allow_origins=origins,
        enable_basic_auth=enable_basic_auth,
        basic_auth_username=basic_user,
        basic_auth_password=basic_pass,
    )
