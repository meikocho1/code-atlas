import sqlite3
from pathlib import Path

SCHEMA = Path(__file__).with_name("schema.sql")


def connect(path: str = ":memory:") -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA.read_text())
    return connection


def cancel_order(connection: sqlite3.Connection, order_id: int) -> None:
    connection.execute("UPDATE orders SET status = 'cancelled' WHERE id = ?", (order_id,))


def record_refund(connection: sqlite3.Connection, order_id: int, amount_cents: int) -> int:
    """Record the single refund allowed for a cancelled order."""
    row = connection.execute("SELECT status FROM orders WHERE id = ?", (order_id,)).fetchone()
    if row is None or row[0] != "cancelled":
        raise ValueError("only cancelled orders can be refunded")
    cursor = connection.execute(
        "INSERT INTO refunds (order_id, amount_cents) VALUES (?, ?)", (order_id, amount_cents)
    )
    return cursor.lastrowid
