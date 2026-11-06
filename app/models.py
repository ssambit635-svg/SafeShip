"""Pydantic models for the orders API.

Kept explicit and dependency-free (no ORM) so data boundaries are visible.
"""

from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class OrderCreate(BaseModel):
    """Input payload for creating an order."""

    item_name: str = Field(
        min_length=1,
        max_length=200,
        description="Name of the item being ordered.",
    )
    quantity: int = Field(
        gt=0,
        le=10_000,
        description="Positive quantity of the item.",
    )


class Order(BaseModel):
    """An order as stored and returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    item_name: str
    quantity: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class OrderList(BaseModel):
    """Paginated list of orders."""

    orders: list[Order]
    total: int
    page: int
    page_size: int
