import unittest

from inventory import StockItem, mark_sold, release, reserve


class ReservationTests(unittest.TestCase):
    def test_reserve_then_sell(self):
        item = StockItem()
        reserve(item)
        self.assertEqual(item.status, "reserved")
        mark_sold(item)
        self.assertEqual(item.status, "sold")

    def test_release_returns_to_available(self):
        item = StockItem()
        reserve(item)
        release(item)
        self.assertEqual(item.status, "available")

    def test_available_item_cannot_be_sold_directly(self):
        item = StockItem()
        with self.assertRaises(ValueError):
            mark_sold(item)


if __name__ == "__main__":
    unittest.main()
