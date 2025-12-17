from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .settings import get_settings

app = FastAPI(
    title="Todo Backend",
    description="Backend API service for managing todos with pluggable storage backends.",
    version="0.1.0",
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
