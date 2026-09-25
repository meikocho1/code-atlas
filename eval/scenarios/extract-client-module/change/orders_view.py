from api_client import get_json


def fetch_order(order_id: str) -> dict:
    return get_json(f"/orders/{order_id}")


def render_order(order_id: str) -> str:
    order = fetch_order(order_id)
    return f"Order {order['id']}: {order['status']}"
