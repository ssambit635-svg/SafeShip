"""FastAPI application for the SafeShip orders API.

Endpoints (Day 2 contract):
- POST /orders        create an order
- GET  /orders/{id}   read an order (404 if absent)
- GET  /orders        list orders with bounded pagination
- GET  /health/live   liveness probe
- GET  /version       deployed commit/version
"""

from fastapi import FastAPI, HTTPException, Query

from app.models import Order, OrderCreate, OrderList
from app.storage import order_storage
from app.version import VERSION

app = FastAPI(title="SafeShip Orders API", version=VERSION)


@app.post("/orders", response_model=Order, status_code=201)
def create_order(order_create: OrderCreate) -> Order:
    """Create a fake order with an item name and positive quantity."""
    return order_storage.create(order_create)


@app.get("/orders/{order_id}", response_model=Order)
def get_order(order_id: str) -> Order:
    """Read an order by ID; return 404 if absent."""
    order = order_storage.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.get("/orders", response_model=OrderList)
def list_orders(
    page: int = Query(1, ge=1, description="Page number (1-based)."),
    page_size: int = Query(50, ge=1, le=100, description="Items per page, capped at 100."),
) -> OrderList:
    """List orders with bounded page size."""
    return order_storage.list(page=page, page_size=page_size)


@app.get("/health/live")
def health_live() -> dict[str, str]:
    """Confirm the application process can respond."""
    return {"status": "alive"}


@app.get("/version")
def version() -> dict[str, str]:
    """Return the deployed Git commit/version for troubleshooting."""
    return {"version": VERSION}
