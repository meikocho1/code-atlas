---
name: understand-change
description: Explain a Git change to a human using evidence from the diff and related code. Use when asked what changed, how a patch works, or what it means for users; select a diagram only when it clarifies the change.
---

# Understand Change

Explain the observed change in the user's language. Start from the change set, trace only the related code needed to verify its behavior, and connect implementation to user impact. This is a change explanation, not a general repository tour or a code review.

## 1. Establish the change set

Honor a supplied commit, range, PR, or file scope. Otherwise inspect the current worktree: staged changes, unstaged changes, and relevant untracked files. If it is clean, use the latest commit as a clearly labeled fallback when it exists. State the actual scope and base revision in the answer. Do not silently mix a branch diff with unrelated worktree edits. If no change can be identified, ask for a target rather than inventing one.

Use `git status --short`, `git diff --stat`, `git diff --name-status`, `git diff --cached`, `git diff`, `git show`, or equivalent read-only tools as appropriate. For a branch comparison, resolve the merge base first and name it. Inspect full relevant hunks, including deletions and renamed files. Treat generated files and lockfiles as context; do not let their size dominate the explanation.

## 2. Trace the behavior

Read changed code and the minimum adjacent code needed to establish entry points, callers, state changes, persistence, external calls, and failure paths. Use the [focused code-reading guide](references/code-reading.md): start with a compact change map, use a structural index to retrieve relevant symbols when available, and expand one unresolved relationship at a time. A Code Wiki or other repository map can identify where to look, but verify its claims against the current diff and source. Use tests and documentation to understand intended behavior, while distinguishing that intent from behavior proven by implementation. The reason for a change is not in the diff: take it only from commit messages, a PR description, an issue, or context the user supplies, and name that source (for example, “per the commit message”). Without such a source, say the motivation is not established. Do not execute code from the target repository merely to explain it.

Build a short evidence chain: **changed line → enclosing behavior → affected caller or user action**. Check the relevant before and after paths, including a meaningful rejected or failure path when one changed. Every material claim and every diagram node, transition, and edge must be supported by the diff or related source. Cite file paths and line numbers where possible. If a business effect cannot be established, say so; do not infer a workflow from names alone. Mark uncertain or unverified runtime effects plainly.

## 3. Choose the explanation, then the visual

Default to three lenses, kept proportionate to the change:

- **BUSINESS:** What changes for a user or operator, or “No demonstrated user-facing change” when appropriate.
- **SYSTEM:** Which boundaries, data, or runtime interactions change.
- **CODE:** The key implementation mechanism, including significant conditions or failure handling.

The lenses are headings for different questions, not a requirement to repeat the same fact three times. For a tiny change, one sentence per lens is enough.

Before drawing, state the reader question that a picture would answer. Use [diagram selection](references/diagram-selection.md) to select at most the views that add information. Prefer one focused diagram; use a second only when it answers a distinct important question. A small rename, copy edit, isolated constant, or local refactor often needs **no diagram**. Never draw one merely to fill a layer.

## 4. Deliver a verifiable explanation

Give the change scope, a one-sentence summary, and the three lenses. If a diagram helps, place it near the lens it explains and use Mermaid unless the requested output format requires another form. Label actors, edges, and transitions with observed behavior; keep one abstraction level per diagram and remove unrelated nodes. Add a one-sentence text explanation for each diagram. A Before/After table is often clearer than Mermaid for a simple behavior change.

Finish with evidence links or `path:line` references and any meaningful uncertainty. Explain only what the code supports. Do not turn possible defects into confirmed failures; if the user asks for review, use a review workflow instead.

Before delivering, if the `code-atlas` CLI is installed, check the report's `path:line` references. Pass the draft on stdin; add `--rev <commit>` when it cites a commit or the head of a range, and omit it for the working tree. Fix or remove every reference it reports. A reference to a removed line resolves only against the base (`--rev <base>`), so check such references there.

```bash
code-atlas check-refs --repo <repository> [--rev <commit>] --report - <<'CODE_ATLAS_REPORT'
<draft Markdown report>
CODE_ATLAS_REPORT
```

When the user asks to keep the result, save the exact Markdown report with the `code-atlas` CLI. Pass it on stdin so no file is written into the target repository:

```bash
code-atlas history add --repo <repository> --skill understand-change --scope <scope> --report - <<'CODE_ATLAS_REPORT'
<exact Markdown report>
CODE_ATLAS_REPORT
```

Record the scope actually analyzed: `worktree` for uncommitted changes (no `--base`/`--head`), `commit` (add `--head <commit>` unless it is HEAD), `range` (add `--base <base> --head <head>`), `project` for a repository-wide result, or `custom`. If `code-atlas` is not installed, return the report and say it was not saved.
