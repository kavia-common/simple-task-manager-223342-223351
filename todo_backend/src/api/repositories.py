from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from threading import RLock
from typing import Iterable, List, Optional, Tuple

from .models import TodoEntity
from .schemas import TodoCreate, TodoUpdate
from .settings import get_settings


@dataclass(frozen=True)
class ListQuery:
    """
    Query parameters for listing todos.
    """
    limit: int = 50
    offset: int = 0
    completed: Optional[bool] = None
    search: Optional[str] = None
    sort: str = "-created_at"  # allowed: created_at, -created_at, updated_at, -updated_at


# PUBLIC_INTERFACE
class Repository(ABC):
    """Abstract repository contract for todo storage backends."""

    @abstractmethod
    def create(self, data: TodoCreate) -> TodoEntity:
        """Create and return a new TodoEntity."""

    @abstractmethod
    def get(self, todo_id: int) -> Optional[TodoEntity]:
        """Return a TodoEntity by id, or None if not found."""

    @abstractmethod
    def update(self, todo_id: int, data: TodoUpdate) -> Optional[TodoEntity]:
        """Update fields of an existing TodoEntity. Return updated entity or None if not found."""

    @abstractmethod
    def delete(self, todo_id: int) -> bool:
        """Delete a TodoEntity by id. Return True if deleted, False if not found."""

    @abstractmethod
    def list(self, query: Optional[ListQuery] = None) -> Tuple[List[TodoEntity], int]:
        """
        Return a slice of TodoEntities and total count matching filters.
        - Supports limit/offset
        - Filter by completed
        - Substring search across title and description (case-insensitive)
        - Sorting by created_at/updated_at (asc/desc)
        """


class InMemoryRepository(Repository):
    """
    Thread-safe in-memory repository suitable for testing and default runtime.
    """

    def __init__(self) -> None:
        self._lock = RLock()
        self._items: dict[int, TodoEntity] = {}
        self._next_id = 1

    def _now(self) -> datetime:
        return datetime.now()

    def _allocate_id(self) -> int:
        with self._lock:
            i = self._next_id
            self._next_id += 1
            return i

    def create(self, data: TodoCreate) -> TodoEntity:
        now = self._now()
        entity: TodoEntity = {
            "id": self._allocate_id(),
            "title": data.title,
            "description": data.description,
            "completed": data.completed,
            "due_date": data.due_date,
            "created_at": now,
            "updated_at": now,
        }
        with self._lock:
            self._items[entity["id"]] = entity
        return entity

    def get(self, todo_id: int) -> Optional[TodoEntity]:
        with self._lock:
            item = self._items.get(todo_id)
            return None if item is None else item.copy()

    def update(self, todo_id: int, data: TodoUpdate) -> Optional[TodoEntity]:
        with self._lock:
            existing = self._items.get(todo_id)
            if existing is None:
                return None

            # Update only provided fields
            updated = existing.copy()
            if data.title is not None:
                updated["title"] = data.title
            if data.description is not None:
                updated["description"] = data.description
            if data.completed is not None:
                updated["completed"] = data.completed
            if data.due_date is not None or data.due_date is None and "due_date" in data.model_fields_set:
                # Respect explicit nulling of due_date
                updated["due_date"] = data.due_date
            updated["updated_at"] = self._now()

            self._items[todo_id] = updated
            return updated.copy()

    def delete(self, todo_id: int) -> bool:
        with self._lock:
            return self._items.pop(todo_id, None) is not None

    def list(self, query: Optional[ListQuery] = None) -> Tuple[List[TodoEntity], int]:
        q = query or ListQuery()
        with self._lock:
            items: Iterable[TodoEntity] = self._items.values()

            # Filtering
            if q.completed is not None:
                items = [t for t in items if t["completed"] == q.completed]

            if q.search:
                s = q.search.lower()
                def matches(t: TodoEntity) -> bool:
                    title_ok = s in (t["title"] or "").lower()
                    desc_ok = s in (t["description"] or "").lower() if t["description"] else False
                    return title_ok or desc_ok
                items = [t for t in items if matches(t)]

            total = len(list(items)) if not isinstance(items, list) else len(items)

            # Sorting
            sort_key = q.sort.strip().lower() if q.sort else "-created_at"
            reverse = sort_key.startswith("-")
            field = sort_key[1:] if reverse else sort_key
            if field not in {"created_at", "updated_at"}:
                field = "created_at"
            items_sorted = sorted(items, key=lambda t: t[field], reverse=reverse)

            # Pagination
            start = max(q.offset, 0)
            end = start + max(q.limit, 0)
            page = items_sorted[start:end]

            # Return copies to avoid external mutation
            return [t.copy() for t in page], total


# PUBLIC_INTERFACE
def get_repository() -> Repository:
    """
    Factory to return the configured repository based on settings.
    - memory: InMemoryRepository
    - sqlite: SQLiteRepository (requires sqlite3 standard library; optional)
    """
    settings = get_settings()
    if settings.persistence_backend == "sqlite":
        try:
            from .db import SQLiteRepository  # type: ignore
        except Exception:
            # Fallback to memory if sqlite backend is not available for any reason
            return InMemoryRepository()
        return SQLiteRepository(settings.sqlite_db_path)
    return InMemoryRepository()
