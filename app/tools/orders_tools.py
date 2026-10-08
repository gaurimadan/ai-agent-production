import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


INITIAL_ORDERS = (
    ("ORD001", "Gauri", "shipped", 1299, "Wireless Headphones"),
    ("ORD002", "Gauri", "delivered", 2499, "Smart Watch"),
)


@contextmanager
def _database() -> Iterator[sqlite3.Connection]:
    configured_path = os.environ.get("ORDERS_DB_PATH")
    database_path = (
        Path(configured_path)
        if configured_path
        else Path(__file__).resolve().parents[2] / "data" / "orders.sqlite"
    )
    database_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(database_path, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        with connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id TEXT PRIMARY KEY,
                    customer TEXT NOT NULL,
                    status TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    item TEXT NOT NULL
                )
                """
            )
            connection.executemany(
                """
                INSERT OR IGNORE INTO orders
                    (id, customer, status, amount, item)
                VALUES (?, ?, ?, ?, ?)
                """,
                INITIAL_ORDERS,
            )
            yield connection
    finally:
        connection.close()


def get_order(order_id: str):
    with _database() as connection:
        order = connection.execute(
            "SELECT id, customer, status, amount, item FROM orders WHERE id = ?",
            (order_id,),
        ).fetchone()

    if order is None:
        return {"success": False, "error": "Order not found"}

    return {"success": True, "order": dict(order)}


def cancel_order(order_id: str):
    with _database() as connection:
        result = connection.execute(
            "UPDATE orders SET status = 'cancelled' WHERE id = ? AND status = 'shipped'",
            (order_id,),
        )
        if result.rowcount == 1:
            return {
                "success": True,
                "message": f"Order {order_id} cancelled",
            }

        order = connection.execute(
            "SELECT status FROM orders WHERE id = ?",
            (order_id,),
        ).fetchone()

    if order is None:
        return {"success": False, "error": "Order not found"}

    return {
        "success": False,
        "error": "Only shipped orders can be cancelled",
    }


def refund_order(order_id: str):
    with _database() as connection:
        order = connection.execute(
            "SELECT amount FROM orders WHERE id = ?",
            (order_id,),
        ).fetchone()

    if order is None:
        return {"success": False, "error": "Order not found"}

    return {
        "success": True,
        "message": f"Refund initiated for {order_id}",
        "amount": order["amount"],
    }