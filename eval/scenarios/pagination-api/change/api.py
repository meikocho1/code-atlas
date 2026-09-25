DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200


def list_items(items: list[dict], page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> list[dict]:
    page_size = min(page_size, MAX_PAGE_SIZE)
    start = (page - 1) * page_size
    return items[start:start + page_size]
