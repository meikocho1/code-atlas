# Choosing a visual for a change

Pick a visual by the question the reader cannot answer quickly from prose. A visual is optional. The source must support every relationship shown.

| Reader question | Use when the diff establishes | Best form |
| --- | --- | --- |
| What steps or decisions change for a person? | An observable workflow or policy branch | Business Flow (`flowchart`) |
| What happens in what order across actors or services? | Calls, messages, responses, or asynchronous work with meaningful ordering | Sequence Diagram |
| Which states and transitions are now allowed? | Explicit state values and transition rules | State Diagram |
| How are persisted entities related? | Schema changes with confirmed keys and cardinality | ER Diagram |
| Which components and boundaries interact differently? | Changed ownership, dependencies, or data flow | Architecture/Component Diagram |
| What is different before and after? | A small set of changed conditions, outputs, or responsibilities | Before/After table |

## Decision rules

1. State the diagram's single question. If a short sentence or small table answers it more clearly, skip Mermaid.
2. Match the diagram to evidence, not filenames. A migration does not automatically need an ER diagram; an API change does not automatically need a sequence diagram.
3. Show the changed path and just enough unchanged context to orient the reader. Keep labels concrete and maintain one abstraction level. Around 3–9 elements is a useful target, not a quota.
4. For a sequence, show a failure or alternate path when it materially changes the outcome and is evidenced. For a state diagram, show only actual states and legal transitions. For ER, read keys and cardinality from the schema rather than guessing.
5. Use default Mermaid colors for portability. Check syntax if a renderer is available. Add a plain sentence that conveys the diagram's point when Mermaid cannot render.
6. If multiple visuals seem useful, choose the one that resolves the main uncertainty. Add a second only for a different question that prose cannot answer as well.

## No-diagram examples

- A typo or label change: say what text changed and where it appears.
- An isolated threshold change: give old value, new value, and effect in a sentence or Before/After row.
- A private helper rename with identical behavior: identify the call sites and say that no behavior change was demonstrated.
