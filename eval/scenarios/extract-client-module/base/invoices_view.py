import json
from http.client import HTTPSConnection

API_HOST = "api.example.internal"


def fetch_invoice(invoice_id: str) -> dict:
    connection = HTTPSConnection(API_HOST)
    connection.request("GET", f"/invoices/{invoice_id}")
    response = connection.getresponse()
    return json.loads(response.read())


def render_invoice(invoice_id: str) -> str:
    invoice = fetch_invoice(invoice_id)
    return f"Invoice {invoice['id']}: {invoice['status']}"
