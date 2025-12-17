# simple-task-manager-223342-223351

FastAPI-based Todo backend providing CRUD endpoints with pluggable storage backends (in-memory or SQLite).

## Quick start

Prerequisites:
- Python 3.11+
- Pip

Install dependencies:
```bash
cd todo_backend
pip install -r requirements.txt
```

Run the API (development):
```bash
uvicorn src.api.main:app --port 3001 --reload
```

The API will be available at:
- OpenAPI/Swagger UI: http://localhost:3001/docs
- ReDoc: http://localhost:3001/redoc

## Environment configuration

Configuration is driven by environment variables (see `.env.example`). Create a `.env` in the `todo_backend` folder if needed.

- PERSISTENCE_BACKEND: memory (default) or sqlite
- SQLITE_DB_PATH: path to SQLite file (default: ./data/todos.db)
- CORS_ALLOW_ORIGINS: comma-separated list of allowed origins or "*" to allow all (default: *)

Example:
```bash
cp .env.example .env
# Optionally edit .env to use SQLite:
# PERSISTENCE_BACKEND=sqlite
# SQLITE_DB_PATH=./data/todos.db
```

## API overview

Base URL: http://localhost:3001

Key endpoints:
- Health
  - GET `/` — Health check and backend mode.
- Todos (tag: todos, base path `/api/v1/todos`)
  - POST `/api/v1/todos/` — Create a todo (201)
  - GET `/api/v1/todos/` — List todos with pagination and filters
      - Query params: limit, offset, completed, q (search), sort (created_at, -created_at, updated_at, -updated_at), order (asc|desc)
  - GET `/api/v1/todos/{todo_id}` — Get a todo by ID
  - PUT `/api/v1/todos/{todo_id}` — Replace a todo
  - PATCH `/api/v1/todos/{todo_id}` — Partially update a todo
  - DELETE `/api/v1/todos/{todo_id}` — Delete a todo (204)

OpenAPI spec is available at `/openapi.json` while the server is running.

## Generate OpenAPI JSON (offline)

If you have a script entrypoint that generates OpenAPI, run:
```bash
python -m src.api.generate_openapi
```
Otherwise, you can fetch the live spec from a running server:
```bash
curl http://localhost:3001/openapi.json -o interfaces/openapi.json
```

The repository includes a reference OpenAPI at `todo_backend/interfaces/openapi.json`.

## Storage backends

- memory (default): Thread-safe in-memory store; data is not persisted across restarts.
- sqlite: Lightweight file-based persistence via SQLite.

Configure via `.env`:
```env
# Use SQLite
PERSISTENCE_BACKEND=sqlite
SQLITE_DB_PATH=./data/todos.db
```

On first run with SQLite, the database and required tables are created automatically.

## CORS

By default, all origins are allowed (`CORS_ALLOW_ORIGINS="*"`). To restrict:
```env
CORS_ALLOW_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

## Development notes

- App entrypoint: `src/api/main.py`
- Routers: `src/api/routers/`
- Schemas: `src/api/schemas.py`
- Repositories/backends:
  - In-memory: `src/api/repositories.py` (InMemoryRepository)
  - SQLite: `src/api/db.py` (SQLiteRepository)
- Settings (env): `src/api/settings.py`