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
