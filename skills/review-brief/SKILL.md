---
name: review-brief
description: Prepare a pull request or code change for review by people who know the business but not the code, such as product, operations, or support staff. Use when asked to make a change reviewable by non-engineers, to show which people and business flows a change affects, or to list what a business reviewer should confirm before merging.
---

# Review Brief

Prepare a change so that someone who knows how the work is done, but cannot read the diff, can see within a minute what changes for whom and can catch a business rule the code gets wrong. You make the rules visible and ask; the reviewer decides whether they are right. Do not judge a business rule as a defect, and do not invent business effects the code does not show.

## 1. Fix the change and its stated intent

Honor a supplied PR, branch, range, or commit; otherwise use the working tree (staged, unstaged, and relevant untracked files), and if it is clean, use the latest commit as a labeled fallback. Name the scope and base. Read the PR description, commit messages, and any linked issue for the intended behavior, and name that source when you use it. Without one, say the intent is not stated. Use read-only Git commands; do not run the project's code.

## 2. Trace each behavior to a person or an operation

For every changed behavior, follow the code from its entry point (a screen, API endpoint, job, command, or function a caller uses) to its outcome: who acts, what rule decides, what state or data results, and what leaves the system (notifications, payments, exports). Read only the related code needed to establish this. When the code does not show who triggers it, call that party "the caller" and mark the effect as unverified.

Collect the decisions a business reviewer can judge:

- conditions, thresholds, and boundary values, including whether a limit is inclusive (`>=`) or exclusive (`>`);
- defaults, time limits, and rounding;
- who is allowed to do something, and whether the code checks it at all;
- what happens on failure, rejection, retry, or cancellation;
- paths a process of this kind usually has but this change does not provide (for example, rejecting or undoing an approval). Raise these only as questions, never as defects.

## 3. Write the brief for a non-engineer

Use the reader's language and everyday words. Explain a technical term in place the first time it is needed, and put code names in parentheses only where a reader might need them to find something. Follow the report shape in the [report components](references/report-components.md), in this order:

1. A title and a one-sentence conclusion (`**Summary:**` or `**結論:**`): who is affected and what changes for them.
2. The scope line, then the output of `code-atlas overview` for that scope.
3. **Who is affected** (a BUSINESS section): an `atlas-impact` map with one line per role, screen, operation, data set, or outside party, each marked added, changed, removed, no change, or unverified, with a short note. Mark every effect the code does not establish as unverified, such as what a downstream payment or report does with a new state. List an unchanged area only when a reviewer would reasonably worry about it and you checked the code.
4. **How the work flows now** (BUSINESS): one `atlas-flow` of the new flow, with `[added]`, `[changed]`, or `[removed]` on each step and branch this change touches (or `[追加]`, `[変更]`, `[削除]`). Draw a second flow only when a second process changes.
5. **The rules, by example** (BUSINESS): a table of concrete inputs on both sides of each boundary and the outcome the code gives, such as 99,999 / 100,000 / 100,001 for a limit of "over 100,000". Compute each outcome from the code and cite the condition.
6. **Please confirm** (BUSINESS): three to seven questions as a task list (`- [ ]`), most important first. Each names the concrete behavior and asks for a decision a business reviewer can make, followed by its `path:line`. Prefer boundaries, missing paths, permissions, and data that becomes visible to someone or is lost.
7. **Not checked in this brief**: a `> [!WARNING]` or `> [!NOTE]` callout listing what remains unverified, including anything outside the repository.
8. **Evidence for developers** (a CODE section): the decisive conditions with `path:line`, kept short.

Keep the business sections free of code walkthroughs. Every claim, impact line, flow step, and example row must be supported by the diff or the related code; mark anything else as unverified.

This skill prepares people to find business mismatches. For defects in the code itself, use `review-change`; a full review can include both.

Before delivering, if the `code-atlas` CLI is installed, check the report's `path:line` references. Pass the draft on stdin; add `--rev <commit>` when it cites a commit or the head of a range, and omit it for the working tree. Fix or remove every reference it reports. A reference to a removed line resolves only against the base (`--rev <base>`), so check such references there.

```bash
code-atlas check-refs --repo <repository> [--rev <commit>] --report - <<'CODE_ATLAS_REPORT'
<draft Markdown report>
CODE_ATLAS_REPORT
```

Deliver every report as a standalone HTML file by default, even when the user did not ask for a file. Draft the report in Markdown for reference checking, then render that same text with `code-atlas render --report - <new-report.html>` (or `python3 -m code_atlas render`). When the report cites a commit or the head of a range, add `--repo <repository> --rev <commit>` as for `check-refs`; `path:line` references then link to that commit on GitHub or GitLab if it has been pushed. Choose a new writable output path outside the analyzed repository; never overwrite a prior report. Shape the report so its point is visible before any paragraph, following the [report components](references/report-components.md): for a change, paste the output of `code-atlas overview` (with the same `--base`/`--head` as the analyzed scope) after the scope line, and draw steps and decisions as a flow rather than prose. Components stay readable as Markdown. For a pull request, also render the same text with `--format github`. Give the user a link to the HTML file and a brief summary in the response. If the CLI is unavailable, create a standalone HTML file with available tools; if file creation is unavailable, return the complete HTML document. Use another format only when the user explicitly requests it.

When the user asks to keep the result, save the exact Markdown report with the `code-atlas` CLI. Pass it on stdin so no file is written into the target repository:

```bash
code-atlas history add --repo <repository> --skill review-brief --scope <scope> --report - <<'CODE_ATLAS_REPORT'
<exact Markdown report>
CODE_ATLAS_REPORT
```

Record the scope actually analyzed: `worktree` for uncommitted changes (no `--base`/`--head`), `commit` (add `--head <commit>` unless it is HEAD), `range` (add `--base <base> --head <head>`), `project` for a repository-wide result, or `custom`. If `code-atlas` is not installed, return the report and say it was not saved.
