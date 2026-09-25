import sqlite3
from pathlib import Path

SCHEMA = Path(__file__).with_name("schema.sql")


def connect(path: str = ":memory:") -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA.read_text())
    return connection


def total_for_order(connection: sqlite3.Connection, order_id: int) -> int:
    """Sum unit_price_cents * quantity across every item on an order."""
    row = connection.execute(
        "SELECT SUM(unit_price_cents * quantity) FROM order_items WHERE order_id = ?", (order_id,)
    ).fetchone()
    return row[0] or 0
