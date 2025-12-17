"""
Utility script to generate and write the OpenAPI schema for the FastAPI app.

This script imports the FastAPI application instance and serializes its OpenAPI
schema to the interfaces/openapi.json file so that API clients and documentation
tools can consume a stable spec without running the server.

Usage:
    python -m src.api.generate_openapi

Notes:
- The script ensures the 'todos' tag is present in the OpenAPI tags metadata.
- Output file path is relative to the container root: interfaces/openapi.json
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List

# Import the FastAPI app from the main module
# This ensures we reuse the same app configuration, routes, and tags.
from .main import app, openapi_tags  # type: ignore


def _ensure_tags(schema: Dict[str, Any]) -> None:
    """
    Ensure the OpenAPI schema contains the expected tags metadata, particularly
    the 'todos' tag with its description. This does not override existing tag
    definitions unless missing.
    """
    existing_tags: List[Dict[str, Any]] = schema.get("tags", []) or []
    existing_names = {t.get("name") for t in existing_tags if isinstance(t, dict)}
    # Ensure tags from openapi_tags exist in schema
    for tag in openapi_tags:
        if tag.get("name") not in existing_names:
            existing_tags.append(tag)
    if existing_tags:
        schema["tags"] = existing_tags


def main() -> None:
    """
    Generate the OpenAPI schema from the FastAPI app and write it to
    interfaces/openapi.json, creating directories as needed.
    """
    # Generate the schema
    schema = app.openapi()
    # Make sure tags (including 'todos') are present
    _ensure_tags(schema)

    # Resolve output path relative to this script location:
    # <container_root>/interfaces/openapi.json
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # points to .../src
    container_root = os.path.dirname(script_dir)  # points to container root
    interfaces_dir = os.path.join(container_root, "interfaces")
    os.makedirs(interfaces_dir, exist_ok=True)
    out_path = os.path.join(interfaces_dir, "openapi.json")

    # Write the schema with pretty formatting for readability
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
    print(f"Wrote OpenAPI schema to: {out_path}")


# PUBLIC_INTERFACE
def generate_openapi() -> str:
    """Generate the OpenAPI schema file and return the written file path."""
    main()
    # Return path for potential programmatic callers
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    container_root = os.path.dirname(script_dir)
    return os.path.join(container_root, "interfaces", "openapi.json")


if __name__ == "__main__":
    main()
