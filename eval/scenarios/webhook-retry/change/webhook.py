from dataclasses import dataclass

from notifier import Notifier, NotifierError

MAX_NOTIFY_ATTEMPTS = 3


@dataclass
class Payment:
    id: str
    amount_cents: int


class PaymentStore:
    def __init__(self) -> None:
        self._payments: dict[str, Payment] = {}

    def save(self, payment: Payment) -> None:
        self._payments[payment.id] = payment


def handle_webhook(store: PaymentStore, notifier: Notifier, payload: dict) -> Payment:
    payment = Payment(id=payload["id"], amount_cents=payload["amount_cents"])
    store.save(payment)
    for attempt in range(1, MAX_NOTIFY_ATTEMPTS + 1):
        try:
            notifier.notify(payment.id)
            break
        except NotifierError:
            if attempt == MAX_NOTIFY_ATTEMPTS:
                raise
    return payment
