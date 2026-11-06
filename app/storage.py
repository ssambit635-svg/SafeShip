"""Thread-safe in-memory order storage.

This is a placeholder for Day 3 (PostgreSQL). The interface is intentionally
small so the database-backed implementation can be swapped in later without
touching the route handlers.
"""

import threading

from app.models import Order, OrderCreate, OrderList


class OrderStorage:
    def __init__(self) -> None:
        self._orders: dict[str, Order] = {}
        self._lock = threading.Lock()

    def create(self, order_create: OrderCreate) -> Order:
        order = Order(
            item_name=order_create.item_name,
            quantity=order_create.quantity,
        )
        with self._lock:
            self._orders[order.id] = order
        return order

    def get(self, order_id: str) -> Order | None:
        with self._lock:
            return self._orders.get(order_id)

    def list(self, page: int = 1, page_size: int = 50) -> OrderList:
        with self._lock:
            all_orders = list(self._orders.values())
            total = len(all_orders)
            start = (page - 1) * page_size
            end = start + page_size
            page_orders = all_orders[start:end]

        return OrderList(
            orders=page_orders,
            total=total,
            page=page,
            page_size=page_size,
        )

    def count(self) -> int:
        with self._lock:
            return len(self._orders)


# Module-level instance used by the route handlers.
order_storage = OrderStorage()
