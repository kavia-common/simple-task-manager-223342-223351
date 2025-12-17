from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..repositories import ListQuery, Repository, get_repository
from ..schemas import TodoCreate, TodoOut, TodoUpdate
from ..utils import pagination_envelope

router = APIRouter(
    prefix="/api/v1/todos",
    tags=["todos"],
)


class PaginationEnvelope(BaseModel):
    """
    Envelope for paginated list responses.
    """
    items: List[TodoOut] = Field(..., description="List of Todo items")
    total: int = Field(..., description="Total number of items matching the query")
    limit: int = Field(..., description="Limit applied to the query")
    offset: int = Field(..., description="Offset applied to the query")


def _get_repo(repo: Repository = Depends(get_repository)) -> Repository:
    """
    Dependency wrapper for repository to keep signatures clean.
    """
    return repo


# PUBLIC_INTERFACE
@router.post(
    "/",
    response_model=TodoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create Todo",
    description="Create a new Todo item and return the created resource.",
    responses={
        201: {"description": "Todo created successfully"},
        400: {"description": "Validation error"},
    },
)
def create_todo(payload: TodoCreate, repo: Repository = Depends(_get_repo)) -> TodoOut:
    """
    Create a new Todo.
    """
    created = repo.create(payload)
    return TodoOut(**created)  # type: ignore[arg-type]


# PUBLIC_INTERFACE
@router.get(
    "/",
    response_model=PaginationEnvelope,
    summary="List Todos",
    description=(
        "List todos with optional filters and pagination.\n\n"
        "Query parameters:\n"
        "- limit: max number of items to return (0..1000)\n"
        "- offset: number of items to skip (>=0)\n"
        "- completed: filter by completion status\n"
        "- q: search query for title/description (substring match)\n"
        "- sort: one of created_at, -created_at, updated_at, -updated_at\n"
        "- order: asc or desc (if provided, it overrides the direction in sort)\n\n"
        "Returns a pagination envelope with items and total count."
    ),
    responses={
        200: {"description": "List retrieved successfully"},
        400: {"description": "Invalid query parameters"},
    },
)
def list_todos(
    limit: int = Query(50, ge=0, le=1000, description="Maximum number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    completed: Optional[bool] = Query(None, description="Filter by completion status"),
    q: Optional[str] = Query(None, description="Search text for title/description"),
    sort: Optional[str] = Query(
        "-created_at",
        description="Sort by field: created_at, -created_at, updated_at, -updated_at",
    ),
    order: Optional[str] = Query(
        None, description="Override sort direction: 'asc' or 'desc'"
    ),
    repo: Repository = Depends(_get_repo),
) -> PaginationEnvelope:
    """
    List todos with pagination and filters.
    """
    # Validate and normalize sorting
    normalized_sort = (sort or "-created_at").strip().lower()
    # If order is set, override the direction on normalized_sort
    if order:
        ord_norm = order.strip().lower()
        if ord_norm not in {"asc", "desc"}:
            raise HTTPException(status_code=400, detail="order must be 'asc' or 'desc'")
        field = normalized_sort.lstrip("-")
        if field not in {"created_at", "updated_at"}:
            field = "created_at"
        normalized_sort = f"-{field}" if ord_norm == "desc" else field
    else:
        # no order override; ensure field validity
        field = normalized_sort.lstrip("-")
        if field not in {"created_at", "updated_at"}:
            normalized_sort = "-created_at"

    query = ListQuery(
        limit=limit,
        offset=offset,
        completed=completed,
        search=q.strip() if q else None,
        sort=normalized_sort,
    )
    items, total = repo.list(query)
    envelope = pagination_envelope(
        items=[TodoOut(**it) for it in items],  # type: ignore[arg-type]
        total=total,
        limit=limit,
        offset=offset,
    )
    # Pydantic model will validate and serialize the helper's dict
    return PaginationEnvelope(**envelope)  # type: ignore[arg-type]


# PUBLIC_INTERFACE
@router.get(
    "/{todo_id}",
    response_model=TodoOut,
    summary="Get Todo",
    description="Get a single Todo item by ID.",
    responses={
        200: {"description": "Todo found"},
        404: {"description": "Todo not found"},
    },
)
def get_todo(todo_id: int, repo: Repository = Depends(_get_repo)) -> TodoOut:
    """
    Retrieve a single Todo item by its ID.
    """
    item = repo.get(todo_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return TodoOut(**item)  # type: ignore[arg-type]


# PUBLIC_INTERFACE
@router.put(
    "/{todo_id}",
    response_model=TodoOut,
    summary="Replace Todo",
    description=(
        "Replace an existing Todo item. Any fields omitted will be set to their default/null "
        "equivalent as per the schema."
    ),
    responses={
        200: {"description": "Todo updated"},
        404: {"description": "Todo not found"},
    },
)
def put_todo(todo_id: int, payload: TodoCreate, repo: Repository = Depends(_get_repo)) -> TodoOut:
    """
    Full update (replace) semantics implemented via the partial-update capable repository by
    mapping TodoCreate into TodoUpdate fields.
    """
    # Turn create payload into a full-field update
    update = TodoUpdate(
        title=payload.title,
        description=payload.description,
        completed=payload.completed,
        due_date=payload.due_date,
    )
    updated = repo.update(todo_id, update)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return TodoOut(**updated)  # type: ignore[arg-type]


# PUBLIC_INTERFACE
@router.patch(
    "/{todo_id}",
    response_model=TodoOut,
    summary="Update Todo",
    description="Partially update fields of a Todo item.",
    responses={
        200: {"description": "Todo updated"},
        404: {"description": "Todo not found"},
    },
)
def patch_todo(todo_id: int, payload: TodoUpdate, repo: Repository = Depends(_get_repo)) -> TodoOut:
    """
    Partial update of a Todo item.
    """
    updated = repo.update(todo_id, payload)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return TodoOut(**updated)  # type: ignore[arg-type]


# PUBLIC_INTERFACE
@router.delete(
    "/{todo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Todo",
    description="Delete a Todo item by ID.",
    responses={
        204: {"description": "Todo deleted"},
        404: {"description": "Todo not found"},
    },
)
def delete_todo(todo_id: int, repo: Repository = Depends(_get_repo)) -> None:
    """
    Delete a Todo. Returns 204 on success, 404 if not found.
    """
    ok = repo.delete(todo_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return None
