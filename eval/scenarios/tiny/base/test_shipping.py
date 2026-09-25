import unittest

from shipping import shipping_fee


class ShippingFeeTests(unittest.TestCase):
    def test_threshold(self):
        self.assertEqual(shipping_fee(4999), 500)
        self.assertEqual(shipping_fee(6000), 0)


if __name__ == "__main__":
    unittest.main()
