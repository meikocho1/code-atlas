from dataclasses import dataclass


@dataclass
class StockItem:
    status: str = "available"


def mark_sold(item: StockItem) -> None:
    if item.status != "available":
        raise ValueError("only available items can be sold")
    item.status = "sold"
