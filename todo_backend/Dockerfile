# Minimal Dockerfile for the Todo Backend (FastAPI)
# Base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies (if any are needed later, keep minimal)
# No extra system packages are required for this project; keep the image slim.

# Copy dependency manifest and install first to leverage Docker layer caching
COPY requirements.txt /app/requirements.txt

# Upgrade pip and install Python dependencies without cache
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

# Copy source code
COPY src /app/src
COPY uvicorn_start.sh /app/uvicorn_start.sh

# Ensure start script is executable
RUN chmod +x /app/uvicorn_start.sh

# Expose application port
EXPOSE 3001

# Default environment (can be overridden at runtime)
# ENV PERSISTENCE_BACKEND=memory
# ENV SQLITE_DB_PATH=./data/todos.db
# ENV CORS_ALLOW_ORIGINS=*

# Command to start the server
CMD ["/app/uvicorn_start.sh"]
