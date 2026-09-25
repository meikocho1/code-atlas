from dataclasses import dataclass


@dataclass
class Payment:
    id: str
    amount_cents: int


class PaymentStore:
    def __init__(self) -> None:
        self._payments: dict[str, Payment] = {}

    def save(self, payment: Payment) -> None:
        self._payments[payment.id] = payment


def handle_webhook(store: PaymentStore, payload: dict) -> Payment:
    payment = Payment(id=payload["id"], amount_cents=payload["amount_cents"])
    store.save(payment)
    return payment
