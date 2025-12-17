from __future__ import annotations

from datetime import date, datetime
from typing import Optional, Union

from pydantic import BaseModel, Field, field_validator, ConfigDict

# Shared type for incoming due_date which can be a date, datetime, or ISO8601 string
DueDateInput = Union[date, datetime, str]
DueDate = Optional[datetime]


def _parse_due_date(value: Optional[DueDateInput]) -> Optional[datetime]:
    """
    Internal helper to normalize due_date input into an aware datetime (naive allowed).
    - If value is a string, attempt to parse via datetime.fromisoformat; if time is missing, set to 00:00.
    - If value is a date (not datetime), convert to datetime at 00:00.
    - If value is a datetime, return as-is.
    """
    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    if isinstance(value, date):
        # Promote a date to a datetime at midnight
        return datetime(value.year, value.month, value.day, 0, 0, 0)

    if isinstance(value, str):
        # Try parsing ISO strings; support both date and datetime formats
        s = value.strip()
        # Attempt full datetime parsing first
        try:
            return datetime.fromisoformat(s)
        except ValueError:
            # If only a date is provided, convert to midnight
            try:
                d = date.fromisoformat(s)
                return datetime(d.year, d.month, d.day, 0, 0, 0)
            except ValueError as e:
                raise ValueError(
                    "Invalid due_date format. Use ISO8601 date or datetime string (e.g., '2025-01-31' or '2025-01-31T13:45:00')."
                ) from e

    # Any other type is invalid
    raise ValueError("Invalid type for due_date; expected date, datetime, or ISO8601 string.")


# PUBLIC_INTERFACE
class TodoCreate(BaseModel):
    """
    Schema for creating a new Todo item.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Buy groceries",
                "description": "Milk, eggs, bread",
                "completed": False,
                "due_date": "2025-02-01",
            }
        }
    )

    title: str = Field(..., description="Short title for the todo item", min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, description="Optional detailed description")
    completed: bool = Field(default=False, description="Completion status flag")
    due_date: Optional[datetime] = Field(
        default=None,
        description="Due date/time of the todo item. Accepts ISO8601 date or datetime; dates are set to 00:00",
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """
        Strip whitespace and enforce 1..200 length.
        """
        if v is None:
            raise ValueError("title is required")
        s = v.strip()
        if not (1 <= len(s) <= 200):
            raise ValueError("title length must be between 1 and 200 characters")
        return s

    @field_validator("due_date", mode="before")
    @classmethod
    def parse_due_date(cls, v: Optional[DueDateInput]) -> Optional[datetime]:
        """
        Normalize due_date from str/date/datetime to datetime.
        """
        return _parse_due_date(v)


# PUBLIC_INTERFACE
class TodoUpdate(BaseModel):
    """
    Schema for updating an existing Todo item.
    All fields are optional; only provided fields will be updated.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Buy groceries and supplies",
                "description": "Milk, eggs, bread, and paper towels",
                "completed": True,
                "due_date": "2025-02-02T09:30:00",
            }
        }
    )

    title: Optional[str] = Field(default=None, description="Short title for the todo item", min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, description="Optional detailed description")
    completed: Optional[bool] = Field(default=None, description="Completion status flag")
    due_date: Optional[datetime] = Field(
        default=None,
        description="Due date/time of the todo item. Accepts ISO8601 date or datetime; dates are set to 00:00",
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """
        If title is provided, strip whitespace and enforce 1..200 length.
        """
        if v is None:
            return v
        s = v.strip()
        if not (1 <= len(s) <= 200):
            raise ValueError("title length must be between 1 and 200 characters")
        return s

    @field_validator("due_date", mode="before")
    @classmethod
    def parse_due_date(cls, v: Optional[DueDateInput]) -> Optional[datetime]:
        """
        Normalize due_date from str/date/datetime to datetime.
        """
        return _parse_due_date(v)


# PUBLIC_INTERFACE
class TodoOut(BaseModel):
    """
    Schema returned by the API for a Todo item.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 123,
                "title": "Buy groceries",
                "description": "Milk, eggs, bread",
                "completed": False,
                "due_date": "2025-02-01T00:00:00",
                "created_at": "2025-01-25T10:15:30.123456",
                "updated_at": "2025-01-26T09:00:00.000001",
            }
        }
    )

    id: int = Field(..., description="Unique identifier of the todo item")
    title: str = Field(..., description="Short title for the todo item")
    description: Optional[str] = Field(default=None, description="Optional detailed description")
    completed: bool = Field(..., description="Completion status flag")
    due_date: Optional[datetime] = Field(
        default=None, description="Due date/time of the todo item as an ISO8601 datetime"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
