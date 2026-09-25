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
