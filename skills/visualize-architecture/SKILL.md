---
name: visualize-architecture
description: Create a focused, source-backed architecture or component diagram for a repository or subsystem. Use when the reader needs to understand boundaries and dependencies, not request ordering or a data lifecycle.
---

# Visualize Architecture

Draw the smallest architecture view that answers the user's boundary question. State the repository revision or change range represented.

1. Identify the requested scope and the abstraction level: context (people and external systems), container (deployable units), or component (parts within one unit). Keep one level per diagram. A generic project map belongs to `understand-project` when no visual question is present.
2. Gather evidence from entry points, manifests, routing, imports, clients, queues, deployment files, and persistence configuration. Prefer a structural index for symbol relationships if available; inspect changed hunks directly for a change-focused request. Existing wiki diagrams are leads, not proof of current topology. Read only the files needed to establish the nodes and edges in view.
3. Select nodes that matter to the question. Label each edge with the real call, event, protocol, or data access and make direction consistent. Mark an external boundary in words or shape. Do not invent infrastructure implied only by conventions. If an edge cannot be established, omit it and state the uncertainty.
4. Return a Mermaid flowchart with a short title, a one-sentence reading guide, and source references for every material relationship. Keep it readable in one screen; split only if the user asks two distinct architecture questions. Use default colors for light and dark themes. If a diagram would add little, explain the architecture in prose instead.

For time ordering use `visualize-data-flow` when the question follows data, or a Sequence Diagram through `understand-change` when the question is about a patch.

Before delivering, if the `code-atlas` CLI is installed, check the report's `path:line` references. Pass the draft on stdin; add `--rev <commit>` when it cites a commit or the head of a range, and omit it for the working tree. Fix or remove every reference it reports. A reference to a removed line resolves only against the base (`--rev <base>`), so check such references there.

```bash
code-atlas check-refs --repo <repository> [--rev <commit>] --report - <<'CODE_ATLAS_REPORT'
<draft Markdown report>
CODE_ATLAS_REPORT
```

When the user asks to keep the result, save the exact Markdown report with the `code-atlas` CLI. Pass it on stdin so no file is written into the target repository:

```bash
code-atlas history add --repo <repository> --skill visualize-architecture --scope <scope> --report - <<'CODE_ATLAS_REPORT'
<exact Markdown report>
CODE_ATLAS_REPORT
```

Record the scope actually analyzed: `worktree` for uncommitted changes (no `--base`/`--head`), `commit` (add `--head <commit>` unless it is HEAD), `range` (add `--base <base> --head <head>`), `project` for a repository-wide result, or `custom`. If `code-atlas` is not installed, return the report and say it was not saved.
