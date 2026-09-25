from dataclasses import dataclass


@dataclass
class Subscription:
    status: str = "active"


def cancel(subscription: Subscription) -> None:
    if subscription.status != "active":
        raise ValueError("only active subscriptions can be cancelled")
    subscription.status = "cancelled"
