# Shared diagram selection

Across Code Atlas skills, choose a diagram by the question it answers and the code evidence available. A diagram is optional; prose or a Before/After table may be clearer for a small change. Keep each visual to one abstraction level and one question. Change-specific decision rules live in [`understand-change`](../skills/understand-change/references/diagram-selection.md), which is self-contained for installation in another repository.

Read a focused guide only when the selected view needs it:

- [Sequence](sequence.md): ordering across actors or services.
- [ER](er.md): persisted entities, keys, and cardinality.
- [State](state.md): legal states and transitions.
- [C4-style component view](c4.md): boundaries and dependencies.

For user-facing steps and decisions, use a small Business Flow. For a few old/new facts, use a Before/After table. Neither needs a separate diagram manual in this release.
