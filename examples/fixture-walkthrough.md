# Fixture walkthrough

Run `bash scripts/make-fixture.sh /tmp/code-atlas-demo` from the Code Atlas repository, then open `/tmp/code-atlas-demo` as the working directory in Codex or Claude Code. Copy `skills/understand-change` into that repository's `.agents/skills/` or `.claude/skills/` directory as described in the main README. The fixture's local Git exclude keeps this installation out of the example change set.

Ask: “Use understand-change to explain the current change in BUSINESS / SYSTEM / CODE. Choose only a visual that helps.”

Useful checks for the explanation:

- Scope: the baseline commit versus the modified working tree, including the new untracked `test_order.py`.
- BUSINESS: an unshipped order may be cancelled; a paid cancellation signals that a refund is needed. It must not claim the refund is processed.
- SYSTEM: this fixture has one in-memory module; it does not establish a payment service, database, or API.
- CODE: `cancel()` accepts `new` and `paid`, rejects `shipped`, sets `cancelled`, and returns a Boolean.
- Code reading: inspect the changed `cancel()` hunk, the existing `mark_paid()` / `ship()` transitions, and the three focused tests. Reading other repository files or generating a wiki adds no evidence here.
- Visual: a small State Diagram can clarify the allowed transitions. A Before/After table or concise prose is also reasonable. ER or service architecture diagrams would be unsupported.

For a quick behavioral check, run `python3 -m unittest -v` in the fixture directory. The script is only a local example; it makes no changes to the Code Atlas repository.
