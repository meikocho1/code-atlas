import unittest

from order import Order, cancel, mark_paid, ship


class OrderCancellationTests(unittest.TestCase):
    def test_new_order_can_be_cancelled_without_refund(self):
        order = Order()
        self.assertFalse(cancel(order))
        self.assertEqual(order.status, "cancelled")

    def test_paid_order_needs_refund(self):
        order = Order()
        mark_paid(order)
        self.assertTrue(cancel(order))
        self.assertEqual(order.status, "cancelled")

    def test_shipped_order_cannot_be_cancelled(self):
        order = Order()
        mark_paid(order)
        ship(order)
        with self.assertRaises(ValueError):
            cancel(order)


if __name__ == "__main__":
    unittest.main()
