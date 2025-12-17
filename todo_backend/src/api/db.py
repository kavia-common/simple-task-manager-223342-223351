from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Generator, List, Optional, Tuple

from .models import TodoEntity
from .schemas import TodoCreate, TodoUpdate
from .repositories import ListQuery


@dataclass(frozen=True)
class _Cols:
    table: str = "todos"
    id: str = "id"
    title: str = "title"
    description: str = "description"
    completed: str = "completed"
    due_date: str = "due_date"
    created_at: str = "created_at"
    updated_at: str = "updated_at"


_COLS = _Cols()


class SQLiteRepository:
    """
    Lightweight SQLite repository implementing the Repository interface.
    """

    def __init__(self, db_path: str) -> None:
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self._db_path = db_path
        self._init_db()

    @contextmanager
    def _conn(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self._db_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {_COLS.table} (
                    {_COLS.id} INTEGER PRIMARY KEY AUTOINCREMENT,
                    {_COLS.title} TEXT NOT NULL,
                    {_COLS.description} TEXT NULL,
                    {_COLS.completed} INTEGER NOT NULL DEFAULT 0,
                    {_COLS.due_date} TEXT NULL,
                    {_COLS.created_at} TEXT NOT NULL,
                    {_COLS.updated_at} TEXT NOT NULL
                )
                """
            )
            conn.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{_COLS.table}_completed ON {_COLS.table}({_COLS.completed})"
            )
            conn.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{_COLS.table}_created_at ON {_COLS.table}({_COLS.created_at})"
            )
            conn.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{_COLS.table}_updated_at ON {_COLS.table}({_COLS.updated_at})"
            )

    def _row_to_entity(self, row: sqlite3.Row) -> TodoEntity:
        def parse_dt(s: Optional[str]) -> Optional[datetime]:
            if s is None:
                return None
            return datetime.fromisoformat(s)

        return {
            "id": int(row[_COLS.id]),
            "title": str(row[_COLS.title]),
            "description": row[_COLS.description] if row[_COLS.description] is not None else None,
            "completed": bool(row[_COLS.completed]),
            "due_date": parse_dt(row[_COLS.due_date]),
            "created_at": parse_dt(row[_COLS.created_at]),  # type: ignore
            "updated_at": parse_dt(row[_COLS.updated_at]),  # type: ignore
        }  # type: ignore

    def create(self, data: TodoCreate) -> TodoEntity:
        now = datetime.now().isoformat()
        due = data.due_date.isoformat() if data.due_date else None
        with self._conn() as conn:
            cur = conn.execute(
                f"""
                INSERT INTO {_COLS.table} ({_COLS.title}, {_COLS.description}, {_COLS.completed},
                    {_COLS.due_date}, {_COLS.created_at}, {_COLS.updated_at})
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (data.title, data.description, 1 if data.completed else 0, due, now, now),
            )
            new_id = cur.lastrowid
            row = conn.execute(
                f"SELECT * FROM {_COLS.table} WHERE {_COLS.id} = ?", (new_id,)
            ).fetchone()
            assert row is not None
            return self._row_to_entity(row)

    def get(self, todo_id: int) -> Optional[TodoEntity]:
        with self._conn() as conn:
            row = conn.execute(f"SELECT * FROM {_COLS.table} WHERE {_COLS.id} = ?", (todo_id,)).fetchone()
            return self._row_to_entity(row) if row else None

    def update(self, todo_id: int, data: TodoUpdate) -> Optional[TodoEntity]:
        with self._conn() as conn:
            row = conn.execute(f"SELECT * FROM {_COLS.table} WHERE {_COLS.id} = ?", (todo_id,)).fetchone()
            if not row:
                return None
            current = self._row_to_entity(row)

            title = data.title if data.title is not None else current["title"]
            description = data.description if "description" in data.model_fields_set else current["description"]
            completed = (data.completed if data.completed is not None else current["completed"])
            if "completed" not in data.model_fields_set:
                completed = current["completed"]
            due_date = (
                data.due_date if "due_date" in data.model_fields_set else current["due_date"]
            )
            updated_at = datetime.now().isoformat()
            conn.execute(
                f"""
                UPDATE {_COLS.table}
                SET {_COLS.title} = ?, {_COLS.description} = ?, {_COLS.completed} = ?,
                    {_COLS.due_date} = ?, {_COLS.updated_at} = ?
                WHERE {_COLS.id} = ?
                """,
                (
                    title,
                    description,
                    1 if completed else 0,
                    due_date.isoformat() if due_date else None,
                    updated_at,
                    todo_id,
                ),
            )
            row2 = conn.execute(f"SELECT * FROM {_COLS.table} WHERE {_COLS.id} = ?", (todo_id,)).fetchone()
            assert row2 is not None
            return self._row_to_entity(row2)

    def delete(self, todo_id: int) -> bool:
        with self._conn() as conn:
            cur = conn.execute(f"DELETE FROM {_COLS.table} WHERE {_COLS.id} = ?", (todo_id,))
            return cur.rowcount > 0

    def list(self, query: Optional[ListQuery] = None) -> Tuple[List[TodoEntity], int]:
        q = query or ListQuery()
        clauses = []
        params: list = []

        if q.completed is not None:
            clauses.append(f"{_COLS.completed} = ?")
            params.append(1 if q.completed else 0)

        if q.search:
            # Substring search on title and description
            clauses.append(f"({_COLS.title} LIKE ? OR {_COLS.description} LIKE ?)")
            like = f"%{q.search}%"
            params.extend([like, like])

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        sort = q.sort.strip().lower() if q.sort else "-created_at"
        reverse = sort.startswith("-")
        field = sort[1:] if reverse else sort
        if field not in {"created_at", "updated_at"}:
            field = "created_at"
        order_sql = f"ORDER BY {field} {'DESC' if reverse else 'ASC'}"

        limit = max(q.limit, 0)
        offset = max(q.offset, 0)
        page_sql = "LIMIT ? OFFSET ?"

        with self._conn() as conn:
            # total count
            count_row = conn.execute(
                f"SELECT COUNT(*) as cnt FROM {_COLS.table} {where_sql}", params
            ).fetchone()
            total = int(count_row["cnt"]) if count_row else 0

            rows = conn.execute(
                f"""
                SELECT * FROM {_COLS.table}
                {where_sql}
                {order_sql}
                {page_sql}
                """,
                [*params, limit, offset],
            ).fetchall()
            return [self._row_to_entity(r) for r in rows], total
