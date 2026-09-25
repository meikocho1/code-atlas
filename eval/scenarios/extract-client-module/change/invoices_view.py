from api_client import get_json


def fetch_invoice(invoice_id: str) -> dict:
    return get_json(f"/invoices/{invoice_id}")


def render_invoice(invoice_id: str) -> str:
    invoice = fetch_invoice(invoice_id)
    return f"Invoice {invoice['id']}: {invoice['status']}"
