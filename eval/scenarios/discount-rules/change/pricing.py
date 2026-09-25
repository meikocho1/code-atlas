MEMBER_DISCOUNT_PERCENT = 10
MAX_DISCOUNT_PERCENT = 30


def apply_coupon(price_cents: int, coupon_percent: int, is_member: bool = False) -> int:
    total_percent = coupon_percent + (MEMBER_DISCOUNT_PERCENT if is_member else 0)
    total_percent = min(total_percent, MAX_DISCOUNT_PERCENT)
    discount = price_cents * total_percent // 100
    return price_cents - discount
