from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .settings import get_settings
from .routers import todos as todos_router

openapi_tags = [
    {"name": "health", "description": "Service health and status endpoints."},
    {
        "name": "todos",
        "description": "CRUD operations for Todo items with filtering, sorting, and pagination.",
    },
]

app = FastAPI(
    title="Todo Backend",
    description="Backend API service for managing todos with pluggable storage backends.",
    version="0.1.0",
    openapi_tags=openapi_tags,
)

_settings = get_settings()

# Configure CORS based on settings
allow_all = _settings.cors_allow_origins == ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all else _settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PUBLIC_INTERFACE
@app.get("/", summary="Health Check", tags=["health"])
def health_check():
    """
    Health check endpoint.

    Returns:
        A JSON object indicating service health.
    """
    return {"message": "Healthy", "backend": _settings.persistence_backend}


# Include routers
app.include_router(todos_router.router)
