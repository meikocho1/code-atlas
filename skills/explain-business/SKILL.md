---
name: explain-business
description: Translate verified code behavior or a selected change into user, operator, and business effects. Use when a stakeholder needs the practical meaning of implementation details, without inventing product intent or metrics.
---

# Explain Business

Explain what the code enables, blocks, or changes for people and operations. Use the user's language and domain terms found in trusted product context.

1. Fix the scope: current behavior, selected feature, or Git change. For a change, compare before and after. Read the affected entry point, the decisive branch or state transition, and the nearest user-facing or operational caller. Prefer a structural index for navigation when available; verify the actual code and any existing wiki claims at the current revision.
2. Map **actor → action → rule → outcome**. Separate what the code establishes from likely business interpretation. Do not assert adoption, revenue, legal compliance, or customer value without corresponding evidence. If the repository only exposes an internal API, describe the API effect and say the end-user effect is not established.
3. Present the result through **BUSINESS** (who can do what), **SYSTEM** (where the rule is enforced and what crosses boundaries), and **CODE** (the small set of conditions implementing it). Use a Before/After table or Business Flow only when it clarifies a real decision or change. Avoid implementation jargon in BUSINESS while retaining file anchors for verification.
4. End with the biggest assumption or missing business context and one concrete question only if that missing fact changes the conclusion. Cite the source locations behind each important claim. Do not replace a formal review or invent defects; use `review-change` for correctness findings.

When asked to retain the explanation, use the installed `code-atlas history add` command with the exact Markdown report and correct scope. Do not silently add files to the target repository.
