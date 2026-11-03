# Report components

`code-atlas render` turns a few Markdown conventions into components: stat tiles, charts, a flow, an impact map, a Before/After comparison, a review checklist, callouts, and severity badges. Each one is plain text in Markdown, so the saved report, `check-refs`, and hosts without the renderer still read correctly. A block that does not parse is shown as ordinary code, never dropped. `code-atlas render --format github` turns the same report into Markdown that GitHub displays in a pull request.

## Report shape

Readers should get the point from the top of the report before reading any paragraph. For a report about a change, use this order:

1. A title and the one-sentence conclusion (`**Summary:**` or `**結論:**`).
2. The scope line (`**Scope:**` or `**対象:**`).
3. The output of `code-atlas overview` for the analyzed scope, pasted unchanged: stat tiles and, when there is something to compare, charts of changed lines per file and by kind. It is computed from Git, so its numbers need no further checking. Pass `--lang ja` for a Japanese report, `--head <commit>` for one commit, or `--base <base> --head <head>` for a range. Omit it when the CLI is unavailable rather than estimating the numbers.
4. One section per lens (BUSINESS, SYSTEM, CODE), each opening with the component that answers its question: a Before/After for a changed behavior, a flow for steps or a decision, a Mermaid diagram for states, ordering, or structure.

Show rather than tell. When the decisive point is a sequence of steps or a branch, draw it as a flow instead of describing it in a paragraph. When it is a change in outcomes, use a Before/After. Keep the prose for what a picture cannot carry: the reason, the evidence, and the uncertainty.

A tiny change (a typo, one constant) still gets the conclusion and the overview tiles, but usually no further component. Components never replace the conclusion or the evidence beside each claim.

## Evidence rules

- Every number must come from something you observed. Examples: `git diff --numstat` (for an untracked file, `git diff --no-index --numstat /dev/null <file>`), a count of files in the reviewed change, or a count of findings in this report. Never estimate or round a number to make a chart look better.
- Name what is counted and the scope in the caption or the text around the component, such as "changed lines in the working tree, including untracked `test_order.py`".
- A chart is not a diagram. It does not replace a Mermaid view when the reader needs a flow, state, or structure, and it does not count as one.
- `path:line` references inside components are checked like any other reference. Write chart labels as `` `path`: value `` (with a space after the colon) so a label is never mistaken for a line reference.

## Syntax

Each data line is `label: value`, split at a colon followed by a space. Chart lines split at the last such colon, so a label may contain colons. Stat and Before/After lines split at the first, so a value may contain colons. Inline Markdown (`` `code` ``, `**bold**`, links) works in labels and values.

### Stat tiles

Use them for two to six headline numbers at the top of a report. Add an optional note after ` | `.

````markdown
```atlas-stats
Files changed: 3 | 1 untracked
Lines added: +37
Actionable findings: 2 | 1 high
```
````

### Bar chart

Use it to compare the size of a few non-negative quantities, such as changed lines per area or calls per entry point. Text after the number is a unit.

````markdown
```atlas-chart bar Changed lines by directory
`app/models`: 42 lines
`app/views`: 9 lines
```
````

### Diff chart

Use it to show where a large change concentrates, with added and removed lines per file. List the files that matter, largest first, and summarize the rest in text.

````markdown
```atlas-chart diff Changed lines per file
`test_order.py`: +27 −0
`order.py`: +9 −2
```
````

### Share bar

Use it to show parts of one whole, such as findings by severity or changed lines by kind (code, tests, docs). Up to eight parts are shown in order, and any beyond seven fold into "Other". Parts with zero are listed but not drawn.

````markdown
```atlas-chart share Findings by severity
high: 1
medium: 2
low: 0
```
````

### Flow

Use it for steps a person or the code goes through, and for a decision with its outcomes. Each line is a step, optionally `actor: action`. A `condition => result` line branches from the step above it; the next plain line continues the main path from the first branch, so list the branch that leads on first. It renders without a script, so it also works offline, and becomes Mermaid in GitHub output. Use Mermaid instead for states, message ordering between services, or entity relationships.

````markdown
```atlas-flow How cancel() decides
Caller: calls `cancel(order)`
`cancel()`: checks the order status
new => cancelled, no refund (`False`)
paid => cancelled, refund needed (`True`)
shipped => `ValueError`
```
````

Every step and branch needs the same evidence as a diagram edge. Name the caller generically ("Caller") when the code does not show who calls it.

To show what a change does to the flow, start a step or branch line with `[added]`, `[changed]`, or `[removed]` (or `[追加]`, `[変更]`, `[削除]`). Marked steps get a labeled chip and a heavier or struck-through border, so a reviewer sees the new flow and the difference in one picture. Keep removed steps in place, marked `[removed]`, rather than dropping them.

````markdown
```atlas-flow Expense approval
Employee: submits an expense
[added] over 100,000 => waits for a manager
100,000 or less => approved automatically
[added] Manager: approves a waiting expense
```
````

### Impact map

Use it to show who and what a change touches: roles, screens, operations, data, and outside parties. Each line is `who / what: change | note`. The change word comes first after the colon: `added`, `changed`, `removed`, `no change`, or `unverified` (or `追加`, `変更`, `削除`, `影響なし`, `未確認`). Lines that share a `who` are grouped, and a count per change kind sits on top. Mark an effect `unverified` when the code does not establish it; those are what a human reviewer should check first.

````markdown
```atlas-impact Who is affected
Employee / Submitting an expense: changed | over 100,000 now waits for approval
Manager / Approving: added | can approve a waiting expense
Accounting / Payment: unverified | what payment does with a waiting expense is not in this repository
```
````

### Review checklist

A list whose every item starts with `[ ]` (or `[x]`) becomes a checklist: tickable boxes in HTML, and GitHub's own task list in a pull request. Use it for questions a reviewer must answer, each naming the concrete behavior and ending with its `path:line`.

```markdown
- [ ] An expense of exactly 100,000 is approved without a manager. Is that intended? (`expenses.py:14`)
```

### Before / After

Use it for a behavior change in two to four states. Repeat a key to add another bullet. The last column is emphasized as the result.

````markdown
```atlas-compare
Before: Orders cannot be cancelled
After: Unshipped orders can be cancelled
After: Shipped orders are rejected
```
````

### Callouts

These use GitHub alert syntax: `NOTE`, `TIP`, `IMPORTANT`, `WARNING`, or `CAUTION`. Use `WARNING` for a material limitation of the analysis (for example, "refunds are not executed by this change") and `NOTE` for the closing uncertainty. Use at most a few per report.

```markdown
> [!WARNING]
> The refund itself is not executed by this change.
```

### Severity badges

A heading that starts with `[critical]`, `[high]`, `[medium]`, or `[low]` gets a badge. So does a table cell that contains only one of these words. Use them for review findings, not for explanations.

```markdown
### [high] Cancelling a shipped order silently succeeds
```

## Pull requests

For a pull request comment or description, render the same Markdown with `code-atlas render --format github --report - -` (stdout) or a new `.md` file. Stat tiles, charts, comparisons, and impact maps become tables, with emoji squares beside the written values. Flows become Mermaid with changed steps labeled and outlined, severities become an icon and a word, and checklists, callouts, and Mermaid pass through. Add `--repo <repository> --rev <commit>` so `path:line` references link to the pushed commit.

## Without the renderer

If `code-atlas` is unavailable and you write HTML yourself, keep the same order and meaning. Render stat tiles as a row of labeled numbers and charts as labeled bars with the value written at each bar, and include the data as a table. Render a flow as numbered steps with the branches listed under their step and each change written as a word. Render an impact map as a table of who, what, change, and note. Render callouts with a visible label, not color alone.
