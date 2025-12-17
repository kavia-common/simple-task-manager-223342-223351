from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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

# Configure CORS based on settings (.env -> CORS_ALLOW_ORIGINS), with '*' fallback
allow_all = (_settings.cors_allow_origins == ["*"]) or (len(_settings.cors_allow_origins) == 0)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all else _settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handlers for consistent JSON on validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Return a consistent JSON structure for request validation errors.

    Response format:
        {
            "error": "ValidationError",
            "detail": [... pydantic/fastapi error details ...],
            "message": "Request validation failed"
        }
    """
    return JSONResponse(
        status_code=422,
        content={
            "error": "ValidationError",
            "message": "Request validation failed",
            "detail": exc.errors(),
        },
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
