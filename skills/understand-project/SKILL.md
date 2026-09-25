---
name: understand-project
description: Explain how an unfamiliar repository works using a source-backed map of its purpose, entry points, modules, and important flows. Use for onboarding or project-wide understanding, not for explaining one Git change.
---

# Understand Project

Give the reader a usable map of the **current** repository in their language. Scope the answer to the requested subsystem if one is named. Do not substitute a directory listing for an explanation.

1. Establish the repository root and revision. Check its README, manifests, deployment configuration, and top-level source layout. Note uncommitted changes that may affect the map. If a CodeGraph-style symbol index exists, ask it for the relevant entry points and cross-module paths before opening whole files. If a code wiki exists, use it as navigation after checking its source revision; verify important claims in current source. Without either, search for likely entry points and read focused ranges. Avoid vendor and generated code unless it defines a real boundary.
2. Identify the user or operator purpose from product documentation and observable entry points. Trace two or three **representative** paths from entry point through modules to data or external effects. Include a consequential alternate path where it changes the outcome. If a business purpose is not evidenced, state that limit.
3. Explain the project through **BUSINESS** (supported use cases), **SYSTEM** (components and boundaries), and **CODE** (entry points and key abstractions). Name the files or symbols that let a new contributor navigate each claim. Distinguish declared architecture from actual calls and configuration.
4. Draw at most one small architecture or flow diagram when it resolves a real orientation question. Use only evidenced nodes and labeled edges at one abstraction level. Skip the diagram for a small library or a requested narrow answer that prose covers better. Add a text summary of any diagram.
5. State the revision, what was inspected, what remains unknown, and where the reader should start for the next task. Cite source paths and line numbers when available. Do not claim exhaustive coverage; expand only when the user requests a deeper map.

This skill explains a repository's present shape. For a selected patch use `understand-change`; for a finding-oriented review use `review-change`.

When asked to retain the result, use the installed `code-atlas history add --scope project` command with the exact Markdown report and repository path. Do not silently add files to the target repository.
