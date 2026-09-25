# Fixture walkthrough

Run `bash scripts/make-fixture.sh /tmp/code-atlas-demo [state|schema|tiny]` from the Code Atlas repository (`state` is the default), then open the new directory as the working directory in your agent. Copy `skills/understand-change` into that repository's `.agents/skills/` (Codex, pi, OpenCode, Gemini CLI, Cursor) or `.claude/skills/` (Claude Code) directory as described in the main README. The fixture's local Git exclude keeps this installation out of the example change set.

In every scenario, ask: “Use understand-change to explain the current change in BUSINESS / SYSTEM / CODE. Choose only a visual that helps.” For a quick behavioral check, run `python3 -m unittest -v` in the fixture directory. The script is only a local example; it makes no changes to the Code Atlas repository.

## `state`: state transition (uncommitted)

- Scope: the baseline commit versus the modified working tree, including the new untracked `test_order.py`.
- BUSINESS: an unshipped order may be cancelled; a paid cancellation signals that a refund is needed. It must not claim the refund is processed.
- SYSTEM: this fixture has one in-memory module; it does not establish a payment service, database, or API.
- CODE: `cancel()` accepts `new` and `paid`, rejects `shipped`, sets `cancelled`, and returns a Boolean.
- Code reading: inspect the changed `cancel()` hunk, the existing `mark_paid()` / `ship()` transitions, and the three focused tests. Reading other repository files or generating a wiki adds no evidence here.
- Visual: a small State Diagram can clarify the allowed transitions. A Before/After table or concise prose is also reasonable. ER or service architecture diagrams would be unsupported.

[Sample explanation](sample-explanation.md) shows one acceptable answer.

## `schema`: database change (committed)

- Scope: the working tree is clean, so the explanation must say it falls back to the latest commit, `Record refunds for cancelled orders`, compared with its parent.
- Motivation: “support staff need to see whether a cancelled order was refunded” comes only from the commit message and must be attributed to it. The message also puts payment processing out of scope, so the answer must not claim money is returned.
- BUSINESS: a cancelled order can have one recorded refund with a positive amount; refunding an order that is not cancelled is rejected.
- SYSTEM: a new `refunds` table references `orders` in the same SQLite database. No payment service or API is established.
- CODE: `record_refund()` checks the order status before inserting. `UNIQUE` on `order_id` rejects a second refund with `IntegrityError`, and `CHECK (amount_cents > 0)` rejects non-positive amounts.
- Visual: an ER Diagram is justified because the schema states the keys. The relationship is one order to **zero or one** refund (`orders ||--o| refunds`); drawing one-to-many is an evidence error. A Before/After list of tables is also reasonable. A Sequence or architecture diagram would be unsupported.

## `tiny`: boundary fix (uncommitted)

- Scope: the baseline commit versus unstaged edits to `shipping.py` and `test_shipping.py`.
- BUSINESS: a subtotal of exactly 5,000 yen now ships free instead of costing 500 yen. Nothing else changes.
- SYSTEM: no change to components, data, or runtime flow; one sentence saying so is enough.
- CODE: `shipping_fee()` changes `>` to `>=`; the test adds the 5,000 boundary.
- Visual: **no diagram.** One sentence or a single Before/After row is the most this change warrants; any Mermaid diagram fails the no-diagram rule.

## Comparing runs

Record the same three points for each scenario, and repeat them when comparing hosts, models, or Skill revisions:

1. Visual choice: State (or table) for `state`, ER with the correct cardinality (or table) for `schema`, none for `tiny`.
2. Evidence: every material claim and diagram edge has a `path:line` that actually supports it.
3. Motivation: stated only with its source (`schema`), or reported as not established (`state`, `tiny`).
