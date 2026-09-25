import sqlite3
import unittest

from shop import cancel_order, connect, record_refund


class RefundTests(unittest.TestCase):
    def setUp(self):
        self.db = connect()
        self.db.execute("INSERT INTO customers (id, name) VALUES (1, 'Fixture')")
        self.db.execute("INSERT INTO orders (id, customer_id) VALUES (1, 1)")

    def test_cancelled_order_gets_one_refund(self):
        cancel_order(self.db, 1)
        record_refund(self.db, 1, 500)
        with self.assertRaises(sqlite3.IntegrityError):
            record_refund(self.db, 1, 500)

    def test_open_order_cannot_be_refunded(self):
        with self.assertRaises(ValueError):
            record_refund(self.db, 1, 500)


if __name__ == "__main__":
    unittest.main()
