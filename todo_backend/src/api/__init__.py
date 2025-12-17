"""
FastAPI Todo Backend package.

This module marks the 'src.api' directory as a Python package and exposes
the FastAPI app instance for convenience imports if desired.
"""

# Expose FastAPI app at package level (optional import path: src.api.app)
try:
    from .main import app  # noqa: F401
except Exception:
    # During certain tooling operations (e.g., static analysis) the import
    # path may not be resolvable. We ignore import errors here to avoid
    # side effects at import time.
    pass
