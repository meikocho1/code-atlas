import sqlite3
from pathlib import Path

SCHEMA = Path(__file__).with_name("schema.sql")


def connect(path: str = ":memory:") -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.executescript(SCHEMA.read_text())
    return connection


def find_by_email(connection: sqlite3.Connection, email: str) -> sqlite3.Row | None:
    connection.row_factory = sqlite3.Row
    return connection.execute("SELECT * FROM customers WHERE email = ?", (email,)).fetchone()
