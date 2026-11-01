"""Render parsed report components as HTML (charts in HTML/CSS, no script)."""

from __future__ import annotations

import html
from typing import Callable

from .components import Chart, Compare, Component, Flow, Stats, format_number, text

Inline = Callable[[str], str]


def _width(value: float, largest: float) -> str:
    return f"{0 if largest <= 0 else value / largest * 100:.2f}%"


def _data_table(headers: list[str], rows: list[list[str]], language: str) -> str:
    head = "".join(f'<th scope="col">{html.escape(cell)}</th>' for cell in headers)
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    return (f'<details class="atlas-chart-table"><summary>{text(language, "table")}</summary>'
            f'<div class="atlas-table"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div></details>')


def _figure(kind: str, title: str, inline: Inline, content: str) -> str:
    caption = f"<figcaption>{inline(title)}</figcaption>" if title else ""
    return f'<figure class="atlas-chart atlas-chart-{kind}">{caption}{content}</figure>'


def _legend(items: list[tuple[int, str]]) -> str:
    keys = "".join(f'<li><span class="atlas-swatch atlas-series-{slot}" aria-hidden="true"></span>{label}</li>'
                   for slot, label in items)
    return f'<ul class="atlas-legend">{keys}</ul>'


def _caption(title: str, inline: Inline) -> str:
    return f'<p class="atlas-stats-title">{inline(title)}</p>' if title else ""


def _bar(chart: Chart, inline: Inline, language: str) -> str:
    largest = max(row.value for row in chart.rows)
    lines = []
    table = []
    for row in chart.rows:
        shown = html.escape(f"{format_number(row.value)} {row.unit}".strip())
        lines.append(f'<div class="atlas-bar-row"><span class="atlas-bar-label">{inline(row.label)}</span>'
                     f'<span class="atlas-bar-track"><span class="atlas-bar atlas-series-1" style="width:{_width(row.value, largest)}" title="{html.escape(row.label, quote=True)}: {shown}"></span></span>'
                     f'<span class="atlas-bar-value">{shown}</span></div>')
        table.append([inline(row.label), shown])
    content = (f'<div class="atlas-bars">{"".join(lines)}</div>'
               + _data_table([text(language, "item"), text(language, "value")], table, language))
    return _figure("bar", chart.title, inline, content)


def _diff(chart: Chart, inline: Inline, language: str) -> str:
    largest = max(row.value + row.removed for row in chart.rows)
    added_label, removed_label = text(language, "added"), text(language, "removed")
    lines = []
    table = []
    for row in chart.rows:
        shown = f"+{format_number(row.value)} −{format_number(row.removed)}"
        segments = []
        for slot, amount, name in ((1, row.value, added_label), (2, row.removed, removed_label)):
            if amount:
                segments.append(f'<span class="atlas-bar atlas-series-{slot}" style="flex-grow:{amount:g}" title="{html.escape(row.label, quote=True)}: {name} {format_number(amount)}"></span>')
        lines.append(f'<div class="atlas-bar-row"><span class="atlas-bar-label">{inline(row.label)}</span>'
                     f'<span class="atlas-bar-track"><span class="atlas-stack" style="width:{_width(row.value + row.removed, largest)}">{"".join(segments)}</span></span>'
                     f'<span class="atlas-bar-value">{shown}</span></div>')
        table.append([inline(row.label), f"+{format_number(row.value)}", f"−{format_number(row.removed)}"])
    content = (_legend([(1, html.escape(added_label)), (2, html.escape(removed_label))])
               + f'<div class="atlas-bars">{"".join(lines)}</div>'
               + _data_table([text(language, "item"), added_label, removed_label], table, language))
    return _figure("diff", chart.title, inline, content)


def _share(chart: Chart, inline: Inline, language: str) -> str:
    total = sum(row.value for row in chart.rows)
    segments = []
    legend = []
    table = []
    for slot, row in enumerate(chart.rows, start=1):
        percent = f"{row.value / total * 100:.0f}%"
        if row.value:
            segments.append(f'<span class="atlas-bar atlas-series-{slot}" style="flex-grow:{row.value:g}" title="{html.escape(row.label, quote=True)}: {format_number(row.value)} ({percent})"></span>')
        legend.append((slot, f'{inline(row.label)}<span class="atlas-legend-value">{format_number(row.value)} · {percent}</span>'))
        table.append([inline(row.label), format_number(row.value), percent])
    content = (f'<div class="atlas-share"><span class="atlas-stack">{"".join(segments)}</span></div>'
               + _legend(legend)
               + _data_table([text(language, "item"), text(language, "value"), text(language, "share")], table, language))
    return _figure("share", chart.title, inline, content)


def _stats(stats: Stats, inline: Inline, language: str) -> str:
    tiles = []
    for label, value, note in stats.tiles:
        detail = f'<span class="atlas-stat-note">{inline(note)}</span>' if note else ""
        tiles.append(f'<div class="atlas-stat"><span class="atlas-stat-label">{inline(label)}</span>'
                     f'<span class="atlas-stat-value">{inline(value)}</span>{detail}</div>')
    return f'<div class="atlas-stats-block">{_caption(stats.title, inline)}<div class="atlas-stats">{"".join(tiles)}</div></div>'


def _compare(compare: Compare, inline: Inline, language: str) -> str:
    cards = []
    for index, (label, values) in enumerate(compare.columns):
        role = " atlas-compare-last" if index == len(compare.columns) - 1 else ""
        items = "".join(f"<li>{inline(value)}</li>" for value in values)
        cards.append(f'<div class="atlas-compare-card{role}"><span class="atlas-compare-label">{inline(label)}</span><ul>{items}</ul></div>')
    return (f'<div class="atlas-compare-block">{_caption(compare.title, inline)}'
            f'<div class="atlas-compare" style="--columns:{len(compare.columns)}">{"".join(cards)}</div></div>')


def _flow(flow: Flow, inline: Inline, language: str) -> str:
    steps = []
    for number, step in enumerate(flow.steps, start=1):
        actor = f'<span class="atlas-flow-actor">{inline(step.actor)}</span>' if step.actor else ""
        branches = ""
        if step.branches:
            options = "".join(
                f'<li><span class="atlas-flow-condition">{inline(condition)}</span>'
                f'<span class="atlas-flow-arrow" aria-hidden="true">→</span>'
                f'<span class="atlas-flow-result">{inline(result)}</span></li>'
                for condition, result in step.branches
            )
            branches = f'<ul class="atlas-flow-branches" aria-label="{text(language, "condition")}">{options}</ul>'
        steps.append(f'<li class="atlas-flow-step{" atlas-flow-decision" if step.branches else ""}">'
                     f'<span class="atlas-flow-number" aria-hidden="true">{number}</span>'
                     f'<div class="atlas-flow-card">{actor}<span class="atlas-flow-action">{inline(step.action)}</span>{branches}</div></li>')
    caption = f"<figcaption>{inline(flow.title)}</figcaption>" if flow.title else ""
    return f'<figure class="atlas-flow">{caption}<ol class="atlas-flow-steps">{"".join(steps)}</ol></figure>'


def render(component: Component, inline: Inline, language: str) -> str:
    if isinstance(component, Chart):
        return {"bar": _bar, "diff": _diff, "share": _share}[component.kind](component, inline, language)
    renderer = {Stats: _stats, Compare: _compare, Flow: _flow}[type(component)]
    return renderer(component, inline, language)


def severity_badge(level: str) -> str:
    return f'<span class="atlas-badge atlas-severity-{level}">{html.escape(level.upper())}</span>'


def layer_tag(lens: str) -> str:
    return f'<span class="atlas-layer atlas-layer-{lens}">{lens.upper()}</span>'


def callout(kind: str, body_html: str, language: str) -> str:
    return (f'<aside class="atlas-callout atlas-callout-{kind}"><p class="atlas-callout-title">'
            f'<span class="atlas-callout-icon" aria-hidden="true"></span>{text(language, kind)}</p>{body_html}</aside>')
