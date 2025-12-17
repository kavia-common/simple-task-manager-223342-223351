# Todo Backend (FastAPI)

FastAPI-based Todo backend providing CRUD endpoints with pluggable storage backends (in-memory or SQLite), pagination, filtering, and sorting.

## Quick start

Prerequisites:
- Python 3.11+
- Pip

Install dependencies:
```bash
pip install -r requirements.txt
```

Run the API (development) on port 3001:
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 3001 --reload
```

The API will be available at:
- OpenAPI/Swagger UI: http://localhost:3001/docs
- ReDoc: http://localhost:3001/redoc
- OpenAPI JSON: http://localhost:3001/openapi.json

Health check:
```bash
curl http://localhost:3001/
```

## Environment configuration

Configuration is driven by environment variables. See `.env.example` in this directory for a reference and copy it to `.env` if needed:
```bash
cp .env.example .env
```

Supported variables:
- PERSISTENCE_BACKEND: memory (default) or sqlite
- SQLITE_DB_PATH: path to SQLite file (default: ./data/todos.db)
- CORS_ALLOW_ORIGINS: comma-separated list of allowed origins or "*" to allow all (default: *)
- ENABLE_BASIC_AUTH (optional): "true" to enable simple HTTP Basic authentication (default: false)
- BASIC_AUTH_USERNAME (optional): username for basic auth when enabled
- BASIC_AUTH_PASSWORD (optional): password for basic auth when enabled

Example to use SQLite:
```env
PERSISTENCE_BACKEND=sqlite
SQLITE_DB_PATH=./data/todos.db
```

Note: When using SQLite, the database file and tables will be created automatically on first run.

## Optional HTTP Basic Authentication

You can enable a lightweight HTTP Basic Auth guard across the health endpoint and the entire Todos API.
- When ENABLE_BASIC_AUTH is not set or set to "false", there is no auth (default behavior).
- When set to "true", both BASIC_AUTH_USERNAME and BASIC_AUTH_PASSWORD must be provided. Requests without valid Basic credentials receive 401 with `WWW-Authenticate: Basic`.

Example `.env`:
```env
ENABLE_BASIC_AUTH=true
BASIC_AUTH_USERNAME=admin
BASIC_AUTH_PASSWORD=secret
```

Example request with credentials:
```bash
curl -u admin:secret http://localhost:3001/
curl -u admin:secret http://localhost:3001/api/v1/todos
```

Implementation details:
- Reusable dependency: `src/api/auth.py` provides `get_basic_auth_dependency()` which becomes a no-op unless auth is enabled.
- Wired in `src/api/main.py`:
  - Applied to `GET /` (health).
  - Applied to all routes of the Todos router via `app.include_router(..., dependencies=[Depends(dep)])`.

## Running with Docker

Build and run:
```bash
docker build -t todo-backend .
docker run --rm -p 3001:3001 --env-file .env todo-backend
```

Entrypoint script respects PORT env var (defaults to 3001):
```bash
PORT=3001 docker run --rm -p 3001:3001 todo-backend
```

## API overview

Base URL: http://localhost:3001

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

## Development notes

- App entrypoint: `src/api/main.py`
- Routers: `src/api/routers/`
- Schemas: `src/api/schemas.py`
- Repositories/backends:
  - In-memory: `src/api/repositories.py` (InMemoryRepository)
  - SQLite: `src/api/db.py` (SQLiteRepository)
- Settings (env): `src/api/settings.py`

## Testing

Pytest config is provided. To run tests from the `todo_backend` directory:
```bash
pytest
```

By default, tests use the in-memory backend (`PERSISTENCE_BACKEND=memory`).
