import unittest

from orders import connect, total_for_order


class OrderItemsTests(unittest.TestCase):
    def setUp(self):
        self.db = connect()
        self.db.execute("INSERT INTO orders (id) VALUES (1)")

    def test_total_sums_multiple_items(self):
        self.db.execute(
            "INSERT INTO order_items (order_id, unit_price_cents, quantity) VALUES (1, 500, 2)"
        )
        self.db.execute(
            "INSERT INTO order_items (order_id, unit_price_cents, quantity) VALUES (1, 300, 1)"
        )
        self.assertEqual(total_for_order(self.db, 1), 1300)

    def test_total_is_zero_with_no_items(self):
        self.assertEqual(total_for_order(self.db, 1), 0)


if __name__ == "__main__":
    unittest.main()
