from dataclasses import dataclass


@dataclass
class Subscription:
    status: str = "active"


def pause(subscription: Subscription) -> None:
    """Pause an active subscription so billing stops without cancelling."""
    if subscription.status != "active":
        raise ValueError("only active subscriptions can be paused")
    subscription.status = "paused"


def resume(subscription: Subscription) -> None:
    """Resume a paused subscription."""
    if subscription.status != "paused":
        raise ValueError("only paused subscriptions can be resumed")
    subscription.status = "active"


def cancel(subscription: Subscription) -> None:
    if subscription.status not in {"active", "paused"}:
        raise ValueError("only active or paused subscriptions can be cancelled")
    subscription.status = "cancelled"
