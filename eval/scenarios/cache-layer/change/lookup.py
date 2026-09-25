from cache import TTLCache
from repository import ProductRepository

CACHE_TTL_SECONDS = 30


def lookup_product(repository: ProductRepository, cache: TTLCache, product_id: str) -> dict | None:
    cached = cache.get(product_id)
    if cached is not None:
        return cached
    product = repository.get(product_id)
    if product is not None:
        cache.set(product_id, product)
    return product
