from __future__ import annotations

from datetime import datetime
from typing import Optional, TypedDict


# PUBLIC_INTERFACE
class TodoEntity(TypedDict):
    """
    A lightweight domain model representing a Todo item for non-ORM storage
    backends.

    Fields:
    - id: Unique integer identifier
    - title: Short title (1..200 chars, trimmed on input via schemas)
    - description: Optional detailed description
    - completed: Boolean completion flag
    - due_date: Optional due datetime (normalized to datetime in schemas)
    - created_at: UTC/local creation timestamp (datetime)
    - updated_at: UTC/local last update timestamp (datetime)
    """

    id: int
    title: str
    description: Optional[str]
    completed: bool
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
