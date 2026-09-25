import unittest

from subscription import Subscription, cancel, pause, resume


class SubscriptionPauseTests(unittest.TestCase):
    def test_pause_then_resume(self):
        subscription = Subscription()
        pause(subscription)
        self.assertEqual(subscription.status, "paused")
        resume(subscription)
        self.assertEqual(subscription.status, "active")

    def test_paused_subscription_can_be_cancelled(self):
        subscription = Subscription()
        pause(subscription)
        cancel(subscription)
        self.assertEqual(subscription.status, "cancelled")

    def test_cancelled_subscription_cannot_be_paused(self):
        subscription = Subscription()
        cancel(subscription)
        with self.assertRaises(ValueError):
            pause(subscription)


if __name__ == "__main__":
    unittest.main()
