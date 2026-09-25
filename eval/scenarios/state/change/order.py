from dataclasses import dataclass


@dataclass
class Order:
    status: str = "new"


def mark_paid(order: Order) -> None:
    if order.status != "new":
        raise ValueError("only new orders can be paid")
    order.status = "paid"


def ship(order: Order) -> None:
    if order.status != "paid":
        raise ValueError("only paid orders can ship")
    order.status = "shipped"


def cancel(order: Order) -> bool:
    """Cancel an unshipped order; return whether a payment refund is needed."""
    if order.status not in {"new", "paid"}:
        raise ValueError("shipped orders cannot be cancelled")
    refund_needed = order.status == "paid"
    order.status = "cancelled"
    return refund_needed
