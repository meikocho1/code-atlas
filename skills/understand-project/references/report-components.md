# Report components

`code-atlas render` turns a few Markdown conventions into HTML components: stat tiles, charts, a Before/After comparison, callouts, and severity badges. Each one is plain text in Markdown, so the saved report, `check-refs`, and hosts without the renderer still read correctly. A block that does not parse is shown as ordinary code, never dropped.

Components are optional. Use one only when it answers a reader question faster than a sentence or table would. A tiny change needs none. They never replace the one-sentence conclusion or the evidence beside each claim.

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

## Without the renderer

If `code-atlas` is unavailable and you write HTML yourself, keep the same order and meaning. Render stat tiles as a row of labeled numbers and charts as labeled bars with the value written at each bar, and include the data as a table. Render callouts with a visible label, not color alone.
