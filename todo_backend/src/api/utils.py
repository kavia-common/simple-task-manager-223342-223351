from __future__ import annotations

from typing import Any, Dict, Iterable, List, Sequence, Union


# PUBLIC_INTERFACE
def pagination_envelope(
    items: Union[Sequence[Any], Iterable[Any]],
    total: int,
    limit: int,
    offset: int,
) -> Dict[str, Any]:
    """
    Build a standard pagination envelope for list endpoints.

    Args:
        items: The list/iterable of items for the current page.
        total: Total number of items that match the query (ignoring pagination).
        limit: The limit used for pagination.
        offset: The offset used for pagination.

    Returns:
        Dict with keys: items, total, limit, offset.
    """
    # Ensure items is materialized as a list (in case an iterator is passed)
    materialized: List[Any] = list(items) if not isinstance(items, list) else items
    return {
        "items": materialized,
        "total": int(total),
        "limit": int(max(limit, 0)),
        "offset": int(max(offset, 0)),
    }
