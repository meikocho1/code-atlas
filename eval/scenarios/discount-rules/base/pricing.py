def apply_coupon(price_cents: int, coupon_percent: int) -> int:
    discount = price_cents * coupon_percent // 100
    return price_cents - discount
