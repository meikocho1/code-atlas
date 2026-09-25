---
name: review-change
description: Review a Git change for concrete regressions and correctness risks with reproducible evidence. Use when asked to review a patch or PR; report actionable findings, not a general explanation of what changed.
---

# Review Change

Find bugs the author can act on. Silence is better than speculative findings: prefer precision over recall.

1. **Fix the file list.** Honor the supplied commit, range, PR, or file scope. Otherwise use staged, unstaged, and relevant untracked worktree changes; if clean, label the latest commit as the fallback. Do not mix unrelated scopes. If the `ocr` CLI (OpenCodeReview) is installed, let it do this deterministic step from the repository root: `ocr delegate preview --format json` with `--from <base> --to <head>`, `-c <commit>`, or no flag for the worktree returns the reviewable files, excluded files with reasons, and the merge base; `ocr delegate rule --format json <paths>` returns review rules grouped by file. If it rejects `--format`, rerun without it and read the text output. OCR's rules do not cover every file type, so treat its exclusions as suggestions: review any excluded file yourself unless the reason is that it is generated, vendored, or a lockfile (for example, Markdown and configuration excluded as `unsupported_ext` still need review). Without `ocr`, list changed files from Git and exclude only generated files, lockfiles, and vendored code, each with a reason.
2. **Keep a coverage checklist.** Track every reviewable file by path and status until it is `reviewed` or `skipped` with a concrete reason. Read all relevant hunks, including deletions and renames; read an untracked file whole. For a large change, review in bounded batches of related files, such as a handler with its test or all locale files together. Do not stop after the first serious finding.
3. **Trace each plausible issue.** Establish a causal chain: changed condition or data → reachable caller/input → incorrect outcome. Use a structural index to locate callers and callees when available, or focused text search otherwise. Check guards, tests, schema, contracts, and failure paths. A supplied PR description or issue states the intended behavior; a mismatch with the implementation is a finding only when a concrete input shows it. Treat documentation and tests as intent evidence, not proof that runtime behavior is correct.
4. **Reflect before reporting.** Re-open the cited lines at the reviewed revision. Confirm that the path and line range point to the code the finding describes, and that the trigger and consequence still hold after reading the surrounding guards. Drop any finding that fails either check. If permitted and useful, run existing targeted tests or a minimal reproduction; do not edit source during a review. A passing test suite does not cancel a source-backed finding.
5. **Report.** Open with the number of actionable findings or a clear statement that none were found. Give each finding a short outcome-focused title, then the trigger, consequence, evidence, and smallest correction or test that would verify it. Include `path:start-end` in the new file, severity (critical/high/medium/low), and category (bug, security, performance, test, other). Order by severity, keep one issue per section, and put the evidence beside the claim rather than in a long code dump. Mark uncertainty when execution or external behavior is unverified. Do not report style preferences as defects. End with compact coverage: total, reviewed, and skipped files, with a reason for each skip. If no actionable issue is found, say so and name any meaningful untested area without inventing a bug.

This skill is finding-oriented. For a human explanation of the change use `understand-change`. Add a diagram only if one is needed to prove a complex finding.

Before delivering, if the `code-atlas` CLI is installed, check the report's `path:line` references. Pass the draft on stdin; add `--rev <commit>` when it cites a commit or the head of a range, and omit it for the working tree. Fix or remove every reference it reports. A reference to a removed line resolves only against the base (`--rev <base>`), so check such references there.

```bash
code-atlas check-refs --repo <repository> [--rev <commit>] --report - <<'CODE_ATLAS_REPORT'
<draft Markdown report>
CODE_ATLAS_REPORT
```

Deliver every report as a standalone HTML file by default, even when the user did not ask for a file. Draft the report in Markdown for reference checking, then render that same text with `code-atlas render --report - <new-report.html>` (or `python3 -m code_atlas render`). Choose a new writable output path outside the analyzed repository; never overwrite a prior report. Give the user a link to the HTML file and a brief summary in the response. If the CLI is unavailable, create a standalone HTML file with available tools; if file creation is unavailable, return the complete HTML document. Use another format only when the user explicitly requests it.

When the user asks to keep the result, save the exact Markdown report with the `code-atlas` CLI. Pass it on stdin so no file is written into the target repository:

```bash
code-atlas history add --repo <repository> --skill review-change --scope <scope> --report - <<'CODE_ATLAS_REPORT'
<exact Markdown report>
CODE_ATLAS_REPORT
```

Record the scope actually analyzed: `worktree` for uncommitted changes (no `--base`/`--head`), `commit` (add `--head <commit>` unless it is HEAD), `range` (add `--base <base> --head <head>`), `project` for a repository-wide result, or `custom`. If `code-atlas` is not installed, return the report and say it was not saved.
