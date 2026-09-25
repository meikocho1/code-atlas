# Order fixture

An order starts as `new`, may become `paid`, and then `shipped`.
An unshipped order can now be cancelled. Cancelling a paid order marks a refund as needed; this fixture does not perform a refund.
