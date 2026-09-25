from dataclasses import dataclass


@dataclass
class StockItem:
    status: str = "available"


def reserve(item: StockItem) -> None:
    """Reserve an available item for a pending order."""
    if item.status != "available":
        raise ValueError("only available items can be reserved")
    item.status = "reserved"


def release(item: StockItem) -> None:
    """Release a reservation, returning the item to available stock."""
    if item.status != "reserved":
        raise ValueError("only reserved items can be released")
    item.status = "available"


def mark_sold(item: StockItem) -> None:
    if item.status != "reserved":
        raise ValueError("only reserved items can be sold")
    item.status = "sold"
