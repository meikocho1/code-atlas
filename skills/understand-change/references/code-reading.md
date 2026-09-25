# Focused code reading

The goal is to answer the changed-behavior question with the fewest *relevant* source reads. Token savings are useful only while the explanation remains complete and checkable.

## Build a change map first

From the selected Git range, collect file names, change types, and a compact diff summary. Group changed hunks by behavior rather than by file. Mark likely entry points, state or schema changes, external boundaries, and tests. Read the actual changed hunks before trusting an index: an index may describe the base commit or lag behind uncommitted edits.

For each behavior group, keep a small working note:

| Question | Evidence to find |
| --- | --- |
| What is newly allowed, blocked, or returned? | Before and after branch or output |
| Who reaches the changed behavior? | Closest relevant caller, route, job, or public API |
| What persists or crosses a boundary? | Actual write, event, request, or schema relationship |
| What happens on a meaningful alternate path? | Guard, error, retry, rollback, or test |

Do not dump this table into the final answer unless it helps the reader. Use it to decide the next read and to catch unsupported claims.

## Choose the narrowest navigation source

1. **Structural index available:** Ask one focused question about the changed symbols and their caller/callee path. With CodeGraph, follow the host's tool guidance: some setups expose `codegraph_explore` alone, while others use `codegraph_context` to narrow the area before one `codegraph_explore`. Use `codegraph_callers` or `codegraph_callees` only if exposed and a specific gap remains. Avoid repeating the same lookup with text search. Check changed hunks directly if the index could be stale.
2. **Existing code wiki or module map:** Read only the page for the affected module or flow. Prefer a wiki with a recorded source revision; compare it with the change base. Treat even a matching wiki as navigation and context, then confirm every claimed edge in current code. Do not generate a full wiki for a single change explanation.
3. **No index:** Search for exact changed symbols within likely directories, then read bounded source ranges around the definitions and closest callers. Expand from there only when the user-facing or system effect remains unclear. Ignore vendor, generated, and unrelated files unless the diff makes them material.

The branches above can complement one another: a wiki may name the module, and an index may then reveal its call path. Neither replaces the Git diff as the change source.

## Expand only to resolve a gap

Follow a call or data edge when it could change the BUSINESS, SYSTEM, or CODE conclusion. Stop when each material conclusion has a source anchor and no unresolved relationship could plausibly reverse it. If the call graph is dynamic or an external service's behavior is unknown, state the limit instead of reading the whole repository or inventing a result. Prefer a clear “caller not established” over a confident but unsupported user journey.
