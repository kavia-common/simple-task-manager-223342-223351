#!/usr/bin/env bash
# Simple launcher for the FastAPI app using uvicorn.
# Uses PORT env var if provided, defaults to 3001.

set -euo pipefail

PORT="${PORT:-3001}"

# Exec to replace the shell with the uvicorn process
exec uvicorn src.api.main:app --host 0.0.0.0 --port "${PORT}"
