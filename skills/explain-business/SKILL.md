---
name: explain-business
description: Translate verified code behavior or a selected change into user, operator, and business effects. Use when a stakeholder needs the practical meaning of implementation details, without inventing product intent or metrics.
---

# Explain Business

Explain what the code enables, blocks, or changes for people and operations. Use the user's language and domain terms found in trusted product context.

1. Fix the scope: current behavior, selected feature, or Git change. For a change, compare before and after. Read the affected entry point, the decisive branch or state transition, and the nearest user-facing or operational caller. Prefer a structural index for navigation when available; verify the actual code and any existing wiki claims at the current revision.
2. Map **actor → action → rule → outcome**. Separate what the code establishes from likely business interpretation. Take product intent or the reason for a change only from commit messages, a PR description, an issue, product documentation, or context the user supplies, and name that source. Do not assert adoption, revenue, legal compliance, or customer value without corresponding evidence. If the repository only exposes an internal API, describe the API effect and say the end-user effect is not established.
3. Present the result through **BUSINESS** (who can do what), **SYSTEM** (where the rule is enforced and what crosses boundaries), and **CODE** (the small set of conditions implementing it). Use a Before/After table or Business Flow only when it clarifies a real decision or change. Avoid implementation jargon in BUSINESS while retaining file anchors for verification.
4. End with the biggest assumption or missing business context and one concrete question only if that missing fact changes the conclusion. Cite the source locations behind each important claim. Do not replace a formal review or invent defects; use `review-change` for correctness findings.

Before delivering, if the `code-atlas` CLI is installed, check the report's `path:line` references. Pass the draft on stdin; add `--rev <commit>` when it cites a commit or the head of a range, and omit it for the working tree. Fix or remove every reference it reports. A reference to a removed line resolves only against the base (`--rev <base>`), so check such references there.

```bash
code-atlas check-refs --repo <repository> [--rev <commit>] --report - <<'CODE_ATLAS_REPORT'
<draft Markdown report>
CODE_ATLAS_REPORT
```

When the user asks to keep the result, save the exact Markdown report with the `code-atlas` CLI. Pass it on stdin so no file is written into the target repository:

```bash
code-atlas history add --repo <repository> --skill explain-business --scope <scope> --report - <<'CODE_ATLAS_REPORT'
<exact Markdown report>
CODE_ATLAS_REPORT
```

Record the scope actually analyzed: `worktree` for uncommitted changes (no `--base`/`--head`), `commit` (add `--head <commit>` unless it is HEAD), `range` (add `--base <base> --head <head>`), `project` for a repository-wide result, or `custom`. If `code-atlas` is not installed, return the report and say it was not saved.
