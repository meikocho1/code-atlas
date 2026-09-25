import json
from http.client import HTTPSConnection

API_HOST = "api.example.internal"


def fetch_order(order_id: str) -> dict:
    connection = HTTPSConnection(API_HOST)
    connection.request("GET", f"/orders/{order_id}")
    response = connection.getresponse()
    return json.loads(response.read())


def render_order(order_id: str) -> str:
    order = fetch_order(order_id)
    return f"Order {order['id']}: {order['status']}"
