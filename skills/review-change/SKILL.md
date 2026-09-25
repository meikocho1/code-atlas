---
name: review-change
description: Review a Git change for concrete regressions and correctness risks with reproducible evidence. Use when asked to review a patch or PR; report actionable findings, not a general explanation of what changed.
---

# Review Change

Find bugs the author can act on. Silence is better than speculative findings.

1. Honor the supplied commit, range, PR, or file scope. Otherwise inspect staged, unstaged, and relevant untracked worktree changes; if clean, label the latest commit as the fallback. Do not mix unrelated scopes. Read all relevant hunks, including deletions and renamed code, before following a call path.
2. For each plausible issue, establish a causal chain: changed condition or data → reachable caller/input → incorrect outcome. Use a structural index to locate callers and callees when available, or focused text search otherwise. Check guards, tests, schema, contracts, and failure paths. Treat documentation and tests as intent evidence, not proof that runtime behavior is correct.
3. Report only findings with a specific trigger and consequence. Give severity (high/medium/low), precise changed-file location, evidence from related source, and the smallest practical correction or test that would verify it. Mark uncertainty when execution or external behavior is unverified. Do not report style preferences as defects.
4. If permitted and useful, run existing targeted tests or a minimal reproduction; do not edit source during a review. A passing test suite does not cancel a source-backed finding. If no actionable issue is found, say so and name any meaningful untested area without inventing a bug.

This skill is finding-oriented. For a human explanation of the change use `understand-change`. Add a diagram only if one is needed to prove a complex finding.

When asked to retain the review, use the installed `code-atlas history add` command with the exact Markdown report and correct change scope. Do not silently add files to the target repository.
