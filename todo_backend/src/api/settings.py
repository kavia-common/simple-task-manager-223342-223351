from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Settings:
    """
    Application settings loaded from environment variables.

    Env vars:
    - PERSISTENCE_BACKEND: 'memory' (default) or 'sqlite'
    - SQLITE_DB_PATH: path to sqlite db file. Default './data/todos.db'
    - CORS_ALLOW_ORIGINS: comma-separated list of allowed origins; '*' by default
    """

    persistence_backend: str
    sqlite_db_path: str
    cors_allow_origins: List[str]


def _get_env(name: str, default: str) -> str:
    value = os.getenv(name, default)
    if value is None or value == "":
        return default
    return value


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

    return Settings(
        persistence_backend=backend,
        sqlite_db_path=sqlite_path,
        cors_allow_origins=origins,
    )
