---
name: understand-project
description: Explain how an unfamiliar repository works using a source-backed map of its purpose, entry points, modules, and important flows. Use for onboarding or project-wide understanding, not for explaining one Git change.
---

# Understand Project

Give the reader a usable map of the **current** repository in their language. Scope the answer to the requested subsystem if one is named. Do not substitute a directory listing for an explanation.

1. Establish the repository root and revision. Check its README, manifests, deployment configuration, and top-level source layout. Note uncommitted changes that may affect the map. If a CodeGraph-style symbol index exists, ask it for the relevant entry points and cross-module paths before opening whole files. If a code wiki exists, use it as navigation after checking its source revision; verify important claims in current source. Without either, search for likely entry points and read focused ranges. Avoid vendor and generated code unless it defines a real boundary.
2. Identify the user or operator purpose from product documentation and observable entry points. Trace two or three **representative** paths from entry point through modules to data or external effects. Include a consequential alternate path where it changes the outcome. If a business purpose is not evidenced, state that limit.
3. Start with a two-sentence orientation: what this project lets people do, then how it works at a high level. Explain it through **BUSINESS** (supported use cases), **SYSTEM** (components and boundaries), and **CODE** (entry points and key abstractions), in that order. Use reader-facing headings and short sections instead of a directory inventory. Name the files or symbols that let a contributor navigate each claim. Distinguish declared architecture from actual calls and configuration.
4. Draw at most one small architecture or flow diagram when it resolves a real orientation question. Introduce what the reader should notice. Use only evidenced nodes and labeled edges at one abstraction level. Skip the diagram for a small library or a requested narrow answer that prose covers better. Add a one-sentence text summary; if Mermaid cannot render, use a readable text flow instead of raw diagram code as the main explanation.
5. State the revision and what was inspected in a compact scope line. Put source references beside the claims they support. Close with what remains unknown and one useful starting point for the next task. Do not claim exhaustive coverage; expand only when the user requests a deeper map.

This skill explains a repository's present shape. For a selected patch use `understand-change`; for a finding-oriented review use `review-change`.

Before delivering, if the `code-atlas` CLI is installed, check the report's `path:line` references. Pass the draft on stdin; add `--rev <commit>` when it cites a commit or the head of a range, and omit it for the working tree. Fix or remove every reference it reports. A reference to a removed line resolves only against the base (`--rev <base>`), so check such references there.

```bash
code-atlas check-refs --repo <repository> [--rev <commit>] --report - <<'CODE_ATLAS_REPORT'
<draft Markdown report>
CODE_ATLAS_REPORT
```

When the user asks to keep the result, save the exact Markdown report with the `code-atlas` CLI. Pass it on stdin so no file is written into the target repository:

```bash
code-atlas history add --repo <repository> --skill understand-project --scope <scope> --report - <<'CODE_ATLAS_REPORT'
<exact Markdown report>
CODE_ATLAS_REPORT
```

Record the scope actually analyzed: `worktree` for uncommitted changes (no `--base`/`--head`), `commit` (add `--head <commit>` unless it is HEAD), `range` (add `--base <base> --head <head>`), `project` for a repository-wide result, or `custom`. If `code-atlas` is not installed, return the report and say it was not saved.
