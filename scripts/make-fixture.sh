#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: bash scripts/make-fixture.sh NEW_DIRECTORY" >&2
  exit 2
fi

destination=$1
if [[ -e "$destination" ]]; then
  echo "Destination already exists: $destination" >&2
  exit 2
fi

mkdir -p "$destination"
cd "$destination"
git init -q
printf '.agents/\n.claude/\n' >> .git/info/exclude

cat > order.py <<'PY'
from dataclasses import dataclass


@dataclass
class Order:
    status: str = "new"


def mark_paid(order: Order) -> None:
    if order.status != "new":
        raise ValueError("only new orders can be paid")
    order.status = "paid"


def ship(order: Order) -> None:
    if order.status != "paid":
        raise ValueError("only paid orders can ship")
    order.status = "shipped"
PY

cat > README.md <<'MD'
# Order fixture

An order starts as `new`, may become `paid`, and then `shipped`.
MD

git add order.py README.md
git -c user.name='Code Atlas Fixture' -c user.email='fixture@example.invalid' commit -qm 'Baseline order lifecycle'

cat >> order.py <<'PY'


def cancel(order: Order) -> bool:
    """Cancel an unshipped order; return whether a payment refund is needed."""
    if order.status not in {"new", "paid"}:
        raise ValueError("shipped orders cannot be cancelled")
    refund_needed = order.status == "paid"
    order.status = "cancelled"
    return refund_needed
PY

cat >> README.md <<'MD'
An unshipped order can now be cancelled. Cancelling a paid order marks a refund as needed; this fixture does not perform a refund.
MD

cat > test_order.py <<'PY'
import unittest

from order import Order, cancel, mark_paid, ship


class OrderCancellationTests(unittest.TestCase):
    def test_new_order_can_be_cancelled_without_refund(self):
        order = Order()
        self.assertFalse(cancel(order))
        self.assertEqual(order.status, "cancelled")

    def test_paid_order_needs_refund(self):
        order = Order()
        mark_paid(order)
        self.assertTrue(cancel(order))
        self.assertEqual(order.status, "cancelled")

    def test_shipped_order_cannot_be_cancelled(self):
        order = Order()
        mark_paid(order)
        ship(order)
        with self.assertRaises(ValueError):
            cancel(order)


if __name__ == "__main__":
    unittest.main()
PY

printf 'Fixture created at %s\n' "$destination"
printf 'Inspect it with: cd %s && git status --short && git diff\n' "$destination"
