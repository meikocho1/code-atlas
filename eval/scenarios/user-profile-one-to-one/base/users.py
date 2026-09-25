import sqlite3
from pathlib import Path

SCHEMA = Path(__file__).with_name("schema.sql")


def connect(path: str = ":memory:") -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA.read_text())
    return connection


def get_user(connection: sqlite3.Connection, user_id: int) -> sqlite3.Row | None:
    connection.row_factory = sqlite3.Row
    return connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
