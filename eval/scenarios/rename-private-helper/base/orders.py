def _calc_total(items):
    return sum(item["price"] * item["qty"] for item in items)


def order_total(order):
    return _calc_total(order["items"])


def invoice_total(invoice):
    return _calc_total(invoice["items"])
