class NotifierError(Exception):
    """Raised when the downstream notification service cannot be reached."""


class Notifier:
    """Represents a client for an external notification service."""

    def notify(self, payment_id: str) -> None:
        raise NotImplementedError
