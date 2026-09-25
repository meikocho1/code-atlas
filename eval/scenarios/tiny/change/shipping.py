FREE_SHIPPING_THRESHOLD = 5000  # yen


def shipping_fee(subtotal: int) -> int:
    return 0 if subtotal >= FREE_SHIPPING_THRESHOLD else 500
