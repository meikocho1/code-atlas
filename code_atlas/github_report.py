"""Render a Code Atlas report as GitHub-flavored Markdown for a pull request comment or description.

GitHub renders Mermaid and `> [!NOTE]` alerts itself, so those pass through. Components become
tables, with emoji squares standing in for bars beside the written values; flows become Mermaid.
Everything else is copied from the source unchanged.
"""

from __future__ import annotations

import re
from itertools import zip_longest

from . import components, markdown
from .components import Chart, Compare, Component, Flow, Stats, format_number, text
from .html_report import report_language
from .refs import permalink

BAR_CELLS = 10
# One square per categorical slot, in the HTML palette's order; each row also prints its value.
SQUARES = ("🟦", "🟧", "🟩", "🟨", "🟪", "🟫", "⬛", "🟥")
SEVERITY_ICONS = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "⚪"}
_REF = re.compile(r"(?<!\[)`([^`\s]*[./][^`\s]*):(\d+)(?:[-–](\d+))?`(?!\]\()")


def _cell(value: str) -> str:
    return value.replace("|", "\\|")


def _table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(_cell(cell) for cell in headers) + " |", "|" + " --- |" * len(headers)]
    lines.extend("| " + " | ".join(_cell(cell) for cell in row) + " |" for row in rows)
    return "\n".join(lines)


def _title(title: str) -> list[str]:
    return [f"**{title}**", ""] if title else []


def _squares(value: float, largest: float, square: str) -> str:
    count = round(value / largest * BAR_CELLS) if largest > 0 else 0
    return square * (max(count, 1) if value > 0 else 0)


def _chart(chart: Chart, language: str) -> str:
    lines = _title(chart.title)
    if chart.kind == "bar":
        largest = max(row.value for row in chart.rows)
        rows = [[row.label, f"{format_number(row.value)} {row.unit}".strip(), _squares(row.value, largest, SQUARES[0])]
                for row in chart.rows]
        lines.append(_table([text(language, "item"), text(language, "value"), ""], rows))
    elif chart.kind == "diff":
        largest = max(row.value + row.removed for row in chart.rows)
        rows = [[row.label, f"+{format_number(row.value)}", f"−{format_number(row.removed)}",
                 _squares(row.value, largest, SQUARES[0]) + _squares(row.removed, largest, SQUARES[1])]
                for row in chart.rows]
        legend = f"{SQUARES[0]} {text(language, 'added')} · {SQUARES[1]} {text(language, 'removed')}"
        lines.append(_table([text(language, "item"), text(language, "added"), text(language, "removed"), legend], rows))
    else:
        total = sum(row.value for row in chart.rows)
        stacked = "".join(_squares(row.value, total, SQUARES[slot]) for slot, row in enumerate(chart.rows))
        rows = [[f"{SQUARES[slot]} {row.label}", format_number(row.value), f"{row.value / total * 100:.0f}%"]
                for slot, row in enumerate(chart.rows)]
        lines.extend([stacked, "", _table([text(language, "item"), text(language, "value"), text(language, "share")], rows)])
    return "\n".join(lines)


def _stats(stats: Stats, language: str) -> str:
    rows = [[f"**{value}**" for _, value, _ in stats.tiles]]
    if any(note for _, _, note in stats.tiles):
        rows.append([note for _, _, note in stats.tiles])
    return "\n".join(_title(stats.title) + [_table([label for label, _, _ in stats.tiles], rows)])


def _compare(compare: Compare, language: str) -> str:
    rows = [list(row) for row in zip_longest(*(values for _, values in compare.columns), fillvalue="")]
    return "\n".join(_title(compare.title) + [_table([label for label, _ in compare.columns], rows)])


def _mermaid_label(value: str) -> str:
    value = value.replace("`", "").replace('"', "#quot;").replace("<", "#lt;").replace(">", "#gt;")
    return f'"{value}"'


def _flow(flow: Flow, language: str) -> str:
    lines = ["```mermaid", "flowchart LR"]
    for number, step in enumerate(flow.steps, start=1):
        label = f"{step.actor}: {step.action}" if step.actor else step.action
        lines.append(f"  S{number}[{_mermaid_label(label)}]")
        if number > 1:
            lines.append(f"  S{number - 1} --> S{number}")
        for index, (condition, result) in enumerate(step.branches, start=1):
            lines.append(f"  S{number} -->|{_mermaid_label(condition)}| S{number}B{index}[{_mermaid_label(result)}]")
    lines.append("```")
    return "\n".join(_title(flow.title) + lines)


def _component(component: Component, language: str) -> str:
    if isinstance(component, Chart):
        return _chart(component, language)
    renderer = {Stats: _stats, Compare: _compare, Flow: _flow}[type(component)]
    return renderer(component, language)


def _link(source: str, base: str | None) -> str:
    if not base:
        return source

    def replace(match: re.Match) -> str:
        start = int(match.group(2))
        url = permalink(base, match.group(1), start, int(match.group(3) or start))
        return f"[{match.group(0)}]({url})" if url else match.group(0)
    return _REF.sub(replace, source)


def _block(block: markdown.Block, language: str, base: str | None) -> str:
    source = "\n".join(block.source)
    if block.kind == "fence":
        component = components.parse(block.name, block.arguments, block.body, language)
        return _component(component, language) if component is not None else source
    if block.kind == "heading":
        found = components.severity(block.text)
        if found:
            level, title = found
            source = f"{'#' * block.level} {SEVERITY_ICONS[level]} **{level.upper()}** {title}"
    elif block.kind == "table" and any(cell.strip().lower() in components.SEVERITIES
                                       for row in block.rows for cell in row):
        rows = [[f"{SEVERITY_ICONS[cell.strip().lower()]} {cell.strip().upper()}"
                 if cell.strip().lower() in components.SEVERITIES else cell for cell in row] for row in block.rows]
        source = _table(block.headers, rows)
    return _link(source, base)


def render_github(source: str, link_base: str | None = None) -> str:
    """Return GitHub-flavored Markdown; with link_base, `path:line` references link to that commit."""
    if not source.strip():
        raise ValueError("Report is empty")
    language = report_language(source)
    return "\n\n".join(_block(block, language, link_base) for block in markdown.parse(source)) + "\n"
