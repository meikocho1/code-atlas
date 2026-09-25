class ProductRepository:
    """Represents a datastore lookup for product records."""

    def __init__(self, records: dict[str, dict]) -> None:
        self._records = records

    def get(self, product_id: str) -> dict | None:
        return self._records.get(product_id)
