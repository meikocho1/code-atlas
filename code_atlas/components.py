"""Render Code Atlas report components: fenced blocks that stay readable as plain Markdown.

Each renderer returns HTML, or None when the block does not parse; the caller then shows
the block as ordinary code so no content is lost.
"""

from __future__ import annotations

import html
import re
from typing import Callable

Inline = Callable[[str], str]

SEVERITIES = ("critical", "high", "medium", "low")
CALLOUTS = ("note", "tip", "important", "warning", "caution")
MAX_SERIES = 8

_TEXT = {
    "ja": {
        "table": "表で見る", "item": "項目", "value": "値", "share": "割合", "added": "追加", "removed": "削除",
        "other": "その他", "note": "補足", "tip": "ヒント", "important": "重要", "warning": "注意", "caution": "警告",
        "scroll": "図は左右にスクロールできます",
    },
    "en": {
        "table": "View as table", "item": "Item", "value": "Value", "share": "Share", "added": "Added", "removed": "Removed",
        "other": "Other", "note": "Note", "tip": "Tip", "important": "Important", "warning": "Warning", "caution": "Caution",
        "scroll": "Scroll sideways to see the whole diagram",
    },
}
_NUMBER = re.compile(r"^([+-]?\d[\d,]*(?:\.\d+)?)\s*(.*)$")
_DIFF = re.compile(r"^\+\s*(\d[\d,]*)\s*[-−–]\s*(\d[\d,]*)$")


def text(language: str, key: str) -> str:
    return _TEXT.get(language, _TEXT["en"])[key]


def _pairs(body: str, last: bool = False) -> list[tuple[str, str]] | None:
    """Split `label: value` lines at a colon followed by a space.

    Chart labels may be paths holding colons and their values are numbers, so charts split
    at the last colon; stats and comparisons carry prose values, so they split at the first.
    """
    pairs = []
    for line in body.splitlines():
        if not line.strip():
            continue
        split = str.rpartition if last else str.partition
        label, separator, value = split(line.strip(), ": ")
        if not separator:
            label, separator, value = split(line.strip(), "：")
        if not separator or not label.strip() or not value.strip():
            return None
        pairs.append((label.strip(), value.strip()))
    return pairs or None


def _number(value: str) -> float:
    return float(value.replace(",", ""))


def _format(value: float) -> str:
    return f"{value:,.0f}" if value == int(value) else f"{value:,.2f}".rstrip("0").rstrip(".")


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


def _bar(title: str, body: str, inline: Inline, language: str) -> str | None:
    pairs = _pairs(body, last=True)
    if not pairs:
        return None
    rows = []
    for label, value in pairs:
        match = _NUMBER.match(value)
        if not match:
            return None
        rows.append((label, _number(match.group(1)), match.group(2)))
    if any(value < 0 for _, value, _ in rows):
        return None  # Bars grow from one baseline; a signed series needs another form.
    largest = max(value for _, value, _ in rows)
    lines = []
    table = []
    for label, value, unit in rows:
        shown = html.escape(f"{_format(value)} {unit}".strip())
        lines.append(f'<div class="atlas-bar-row"><span class="atlas-bar-label">{inline(label)}</span>'
                     f'<span class="atlas-bar-track"><span class="atlas-bar atlas-series-1" style="width:{_width(value, largest)}" title="{html.escape(label, quote=True)}: {shown}"></span></span>'
                     f'<span class="atlas-bar-value">{shown}</span></div>')
        table.append([inline(label), shown])
    content = (f'<div class="atlas-bars">{"".join(lines)}</div>'
               + _data_table([text(language, "item"), text(language, "value")], table, language))
    return _figure("bar", title, inline, content)


def _diff(title: str, body: str, inline: Inline, language: str) -> str | None:
    pairs = _pairs(body, last=True)
    if not pairs:
        return None
    rows = []
    for label, value in pairs:
        match = _DIFF.match(value)
        if not match:
            return None
        rows.append((label, _number(match.group(1)), _number(match.group(2))))
    largest = max(added + removed for _, added, removed in rows)
    added_label, removed_label = text(language, "added"), text(language, "removed")
    lines = []
    table = []
    for label, added, removed in rows:
        total = added + removed
        shown = f"+{_format(added)} −{_format(removed)}"
        segments = []
        for slot, amount, name in ((1, added, added_label), (2, removed, removed_label)):
            if amount:
                segments.append(f'<span class="atlas-bar atlas-series-{slot}" style="flex-grow:{amount:g}" title="{html.escape(label, quote=True)}: {name} {_format(amount)}"></span>')
        lines.append(f'<div class="atlas-bar-row"><span class="atlas-bar-label">{inline(label)}</span>'
                     f'<span class="atlas-bar-track"><span class="atlas-stack" style="width:{_width(total, largest)}">{"".join(segments)}</span></span>'
                     f'<span class="atlas-bar-value">{shown}</span></div>')
        table.append([inline(label), f"+{_format(added)}", f"−{_format(removed)}"])
    content = (_legend([(1, html.escape(added_label)), (2, html.escape(removed_label))])
               + f'<div class="atlas-bars">{"".join(lines)}</div>'
               + _data_table([text(language, "item"), added_label, removed_label], table, language))
    return _figure("diff", title, inline, content)


def _share(title: str, body: str, inline: Inline, language: str) -> str | None:
    pairs = _pairs(body, last=True)
    if not pairs:
        return None
    rows = []
    for label, value in pairs:
        match = _NUMBER.match(value)
        if not match or _number(match.group(1)) < 0:
            return None
        rows.append((label, _number(match.group(1))))
    if len(rows) > MAX_SERIES:
        # A ninth hue is never generated; the tail folds into "Other".
        rows = rows[:MAX_SERIES - 1] + [(text(language, "other"), sum(value for _, value in rows[MAX_SERIES - 1:]))]
    total = sum(value for _, value in rows)
    if total <= 0:
        return None
    segments = []
    legend = []
    table = []
    for slot, (label, value) in enumerate(rows, start=1):
        percent = f"{value / total * 100:.0f}%"
        if value:
            segments.append(f'<span class="atlas-bar atlas-series-{slot}" style="flex-grow:{value:g}" title="{html.escape(label, quote=True)}: {_format(value)} ({percent})"></span>')
        legend.append((slot, f'{inline(label)}<span class="atlas-legend-value">{_format(value)} · {percent}</span>'))
        table.append([inline(label), _format(value), percent])
    content = (f'<div class="atlas-share"><span class="atlas-stack">{"".join(segments)}</span></div>'
               + _legend(legend)
               + _data_table([text(language, "item"), text(language, "value"), text(language, "share")], table, language))
    return _figure("share", title, inline, content)


def chart(arguments: str, body: str, inline: Inline, language: str) -> str | None:
    kind, _, title = arguments.strip().partition(" ")
    renderer = {"bar": _bar, "diff": _diff, "share": _share}.get(kind.lower())
    return renderer(title.strip(), body, inline, language) if renderer else None


def stats(arguments: str, body: str, inline: Inline, language: str) -> str | None:
    pairs = _pairs(body)
    if not pairs:
        return None
    tiles = []
    for label, value in pairs:
        value, _, note = value.partition(" | ")
        detail = f'<span class="atlas-stat-note">{inline(note.strip())}</span>' if note.strip() else ""
        tiles.append(f'<div class="atlas-stat"><span class="atlas-stat-label">{inline(label)}</span>'
                     f'<span class="atlas-stat-value">{inline(value.strip())}</span>{detail}</div>')
    caption = f'<p class="atlas-stats-title">{inline(arguments.strip())}</p>' if arguments.strip() else ""
    return f'<div class="atlas-stats-block">{caption}<div class="atlas-stats">{"".join(tiles)}</div></div>'


def compare(arguments: str, body: str, inline: Inline, language: str) -> str | None:
    pairs = _pairs(body)
    if not pairs:
        return None
    columns: dict[str, list[str]] = {}
    for label, value in pairs:
        columns.setdefault(label, []).append(value)
    if not 2 <= len(columns) <= 4:
        return None
    cards = []
    for index, (label, values) in enumerate(columns.items()):
        role = " atlas-compare-last" if index == len(columns) - 1 else ""
        items = "".join(f"<li>{inline(value)}</li>" for value in values)
        cards.append(f'<div class="atlas-compare-card{role}"><span class="atlas-compare-label">{inline(label)}</span><ul>{items}</ul></div>')
    caption = f'<p class="atlas-stats-title">{inline(arguments.strip())}</p>' if arguments.strip() else ""
    return f'<div class="atlas-compare-block">{caption}<div class="atlas-compare" style="--columns:{len(columns)}">{"".join(cards)}</div></div>'


RENDERERS = {"atlas-chart": chart, "atlas-stats": stats, "atlas-compare": compare}


def severity_badge(value: str) -> str:
    level = value.strip().lower()
    return f'<span class="atlas-badge atlas-severity-{level}">{html.escape(level.upper())}</span>'


def callout(kind: str, body_html: str, language: str) -> str:
    return (f'<aside class="atlas-callout atlas-callout-{kind}"><p class="atlas-callout-title">'
            f'<span class="atlas-callout-icon" aria-hidden="true"></span>{text(language, kind)}</p>{body_html}</aside>')
