from repository import ProductRepository


def lookup_product(repository: ProductRepository, product_id: str) -> dict | None:
    return repository.get(product_id)
