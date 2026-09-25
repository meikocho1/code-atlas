def _sum_line_items(items):
    return sum(item["price"] * item["qty"] for item in items)


def order_total(order):
    return _sum_line_items(order["items"])


def invoice_total(invoice):
    return _sum_line_items(invoice["items"])
