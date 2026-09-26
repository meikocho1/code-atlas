---
name: visualize-data-flow
description: Trace how a specific input, event, or record moves through code, transforms, and storage, then draw a source-backed data-flow view. Use for provenance, processing, or handoff questions rather than a static component map.
---

# Visualize Data Flow

Answer “where does this data come from, what changes it, and where does it go?” for one named datum or workflow. Ask for the datum if no useful starting point can be inferred.

1. Establish the revision and starting boundary: user input, API request, event, file, database row, or job. Find the actual producer, transformation points, and sinks. Use a structural index for caller/callee paths when available, then inspect the exact source ranges that establish transformations and side effects. Search narrowly when there is no index. Verify any wiki map against current code.
2. Track **value and meaning**, not just function calls: field name, validation, normalization, mapping, persistence, emitted event, and consumer. Check whether a branch drops, rejects, retries, or duplicates data. Distinguish a declared schema from runtime transformations. Stop at an external boundary whose behavior is not visible.
3. Choose a flowchart for stages and branching, or a Sequence Diagram when ordering among actors is the hard part. Do not draw both unless they answer different requested questions. Label arrows with the data or event carried, and mark transforms on the nodes. Omit unrelated components; do not guess sensitive-data handling or retention.
4. Start with a plain-language sentence saying where the data starts and what observable result it produces. Then give **BUSINESS** meaning, **SYSTEM** path, and **CODE** anchors in that order, using short reader-facing sections. State the input/output contract, important alternate path, and any unverified step. Cite paths and line numbers beside the claims and diagram relationships they support. Introduce what to look for in the diagram and follow it with a one-sentence text alternative. If Mermaid rendering is known to be unavailable, use a readable numbered flow or table instead of raw diagram code as the main explanation.

For persisted entity relationships, use an ER view only when keys and cardinality are explicit in the schema. For static dependencies, use `visualize-architecture`.

Before delivering, if the `code-atlas` CLI is installed, check the report's `path:line` references. Pass the draft on stdin; add `--rev <commit>` when it cites a commit or the head of a range, and omit it for the working tree. Fix or remove every reference it reports. A reference to a removed line resolves only against the base (`--rev <base>`), so check such references there.

```bash
code-atlas check-refs --repo <repository> [--rev <commit>] --report - <<'CODE_ATLAS_REPORT'
<draft Markdown report>
CODE_ATLAS_REPORT
```

Deliver every report as a standalone HTML file by default, even when the user did not ask for a file. Draft the report in Markdown for reference checking, then render that same text with `code-atlas render --report - <new-report.html>` (or `python3 -m code_atlas render`). When the report cites a commit or the head of a range, add `--repo <repository> --rev <commit>` as for `check-refs`; `path:line` references then link to that commit on GitHub or GitLab if it has been pushed. Choose a new writable output path outside the analyzed repository; never overwrite a prior report. When a headline number, a Before/After contrast, a finding's severity, or a caveat reads faster as a component, use the [report components](references/report-components.md); they stay readable as Markdown. Give the user a link to the HTML file and a brief summary in the response. If the CLI is unavailable, create a standalone HTML file with available tools; if file creation is unavailable, return the complete HTML document. Use another format only when the user explicitly requests it.

When the user asks to keep the result, save the exact Markdown report with the `code-atlas` CLI. Pass it on stdin so no file is written into the target repository:

```bash
code-atlas history add --repo <repository> --skill visualize-data-flow --scope <scope> --report - <<'CODE_ATLAS_REPORT'
<exact Markdown report>
CODE_ATLAS_REPORT
```

Record the scope actually analyzed: `worktree` for uncommitted changes (no `--base`/`--head`), `commit` (add `--head <commit>` unless it is HEAD), `range` (add `--base <base> --head <head>`), `project` for a repository-wide result, or `custom`. If `code-atlas` is not installed, return the report and say it was not saved.
