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

When asked to retain the result, use the installed `code-atlas history add` command with the exact Markdown report and correct scope. Do not silently add files to the target repository.
