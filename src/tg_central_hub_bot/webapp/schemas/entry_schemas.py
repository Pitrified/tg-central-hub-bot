"""Pydantic schemas for the entries resource."""

from datetime import datetime

from pydantic import BaseModel
from pydantic import Field


class EntryCreate(BaseModel):
    """Schema for creating a new entry."""

    text: str = Field(min_length=1, max_length=500)


class EntryRead(BaseModel):
    """Schema for reading an entry."""

    id: int
    text: str
    created_at: datetime
