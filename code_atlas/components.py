"""Parse Code Atlas report components: fenced blocks that stay readable as plain Markdown.

`parse()` turns a block into data, or returns None when it does not parse; renderers then
show the block as ordinary code so no content is lost. Rendering lives in html_components.py
(HTML) and github_report.py (GitHub-flavored Markdown).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Union

SEVERITIES = ("critical", "high", "medium", "low")
CALLOUTS = ("note", "tip", "important", "warning", "caution")
LAYERS = ("business", "system", "code")
MAX_SERIES = 8

_TEXT = {
    "ja": {
        "table": "表で見る", "item": "項目", "value": "値", "share": "割合", "added": "追加", "removed": "削除",
        "other": "その他", "note": "補足", "tip": "ヒント", "important": "重要", "warning": "注意", "caution": "警告",
        "scroll": "図は左右にスクロールできます", "glance": "ひと目で", "condition": "条件", "result": "結果",
        "step": "手順", "added": "追加", "changed": "変更", "removed": "削除", "unchanged": "影響なし",
        "unknown": "未確認", "impact": "影響範囲", "who": "対象", "change": "影響", "detail": "内容",
    },
    "en": {
        "table": "View as table", "item": "Item", "value": "Value", "share": "Share", "added": "Added", "removed": "Removed",
        "other": "Other", "note": "Note", "tip": "Tip", "important": "Important", "warning": "Warning", "caution": "Caution",
        "scroll": "Scroll sideways to see the whole diagram", "glance": "At a glance", "condition": "Condition",
        "result": "Result", "step": "Step", "added": "Added", "changed": "Changed", "removed": "Removed",
        "unchanged": "No change", "unknown": "Unverified", "impact": "Impact", "who": "Who", "change": "Change",
        "detail": "Detail",
    },
}
_NUMBER = re.compile(r"^([+-]?\d[\d,]*(?:\.\d+)?)\s*(.*)$")
_DIFF = re.compile(r"^\+\s*(\d[\d,]*)\s*[-−–]\s*(\d[\d,]*)$")
_BRANCH = re.compile(r"(?:^|\s+)(?:=>|⇒)\s+")
# How a flow step or an impact area changes. Each is shown with an icon and a word, never color alone.
CHANGES = ("added", "changed", "removed", "unchanged", "unknown")
_CHANGE_WORDS = {
    "added": "added", "new": "added", "追加": "added", "新規": "added",
    "changed": "changed", "変更": "changed",
    "removed": "removed", "削除": "removed", "廃止": "removed",
    "unchanged": "unchanged", "no change": "unchanged", "影響なし": "unchanged", "変更なし": "unchanged",
    "unknown": "unknown", "unverified": "unknown", "未確認": "unknown",
}
_MARKER = re.compile(r"^\[([^\]]+)\]\s+(.+)$")


def change_kind(word: str) -> str | None:
    return _CHANGE_WORDS.get(word.strip().lower())


def _marked(line: str) -> tuple[str, str]:
    """Split a leading `[added]` / `[変更]` style marker from a flow line."""
    match = _MARKER.match(line)
    if match and change_kind(match.group(1)) in {"added", "changed", "removed"}:
        return change_kind(match.group(1)), match.group(2).strip()
    return "", line


def text(language: str, key: str) -> str:
    return _TEXT.get(language, _TEXT["en"])[key]


@dataclass
class ChartRow:
    label: str
    value: float  # Added lines for a diff chart.
    removed: float = 0
    unit: str = ""


@dataclass
class Chart:
    kind: str  # bar, diff, or share
    title: str
    rows: list[ChartRow]


@dataclass
class Stats:
    title: str
    tiles: list[tuple[str, str, str]]  # label, value, note


@dataclass
class Compare:
    title: str
    columns: list[tuple[str, list[str]]]


@dataclass
class Branch:
    condition: str
    result: str
    change: str = ""  # added, changed, removed, or "" for unchanged


@dataclass
class Step:
    actor: str
    action: str
    branches: list[Branch] = field(default_factory=list)
    change: str = ""


@dataclass
class ImpactArea:
    group: str  # who or where, such as a role or a screen; may be empty
    item: str
    change: str  # one of CHANGES
    note: str


@dataclass
class Impact:
    title: str
    areas: list[ImpactArea]


@dataclass
class Flow:
    title: str
    steps: list[Step]


Component = Union[Chart, Stats, Compare, Flow, Impact]


def format_number(value: float) -> str:
    return f"{value:,.0f}" if value == int(value) else f"{value:,.2f}".rstrip("0").rstrip(".")


def _number(value: str) -> float:
    return float(value.replace(",", ""))


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


def _chart(arguments: str, body: str, language: str) -> Chart | None:
    kind, _, title = arguments.partition(" ")
    kind = kind.lower()
    pairs = _pairs(body, last=True)
    if kind not in {"bar", "diff", "share"} or not pairs:
        return None
    rows = []
    for label, value in pairs:
        if kind == "diff":
            match = _DIFF.match(value)
            if not match:
                return None
            rows.append(ChartRow(label, _number(match.group(1)), _number(match.group(2))))
            continue
        match = _NUMBER.match(value)
        if not match or _number(match.group(1)) < 0:
            return None  # Bars grow from one baseline; a signed series needs another form.
        rows.append(ChartRow(label, _number(match.group(1)), unit=match.group(2) if kind == "bar" else ""))
    if kind == "share":
        if len(rows) > MAX_SERIES:
            # A ninth hue is never generated; the tail folds into "Other".
            rows = rows[:MAX_SERIES - 1] + [ChartRow(text(language, "other"), sum(row.value for row in rows[MAX_SERIES - 1:]))]
        if sum(row.value for row in rows) <= 0:
            return None
    return Chart(kind, title.strip(), rows)


def _stats(arguments: str, body: str, language: str) -> Stats | None:
    pairs = _pairs(body)
    if not pairs:
        return None
    tiles = []
    for label, value in pairs:
        value, _, note = value.partition(" | ")
        tiles.append((label, value.strip(), note.strip()))
    return Stats(arguments, tiles)


def _compare(arguments: str, body: str, language: str) -> Compare | None:
    pairs = _pairs(body)
    if not pairs:
        return None
    columns: dict[str, list[str]] = {}
    for label, value in pairs:
        columns.setdefault(label, []).append(value)
    if not 2 <= len(columns) <= 4:
        return None
    return Compare(arguments, list(columns.items()))


def _flow(arguments: str, body: str, language: str) -> Flow | None:
    """Steps run top to bottom; a `condition => result` line branches from the step above it.

    The next plain line continues the main path, from the first branch when the step above has any.

    A leading `[added]`, `[changed]`, or `[removed]` (or `[追加]`, `[変更]`, `[削除]`) marks what this
    change does to a step or branch, so a reviewer sees the new flow and its difference at once.
    """
    steps: list[Step] = []
    for line in body.splitlines():
        change, line = _marked(line.strip())
        if not line:
            continue
        branch = _BRANCH.split(line, maxsplit=1)
        if len(branch) == 2:
            if not steps or not branch[0].strip() or not branch[1].strip():
                return None
            steps[-1].branches.append(Branch(branch[0].strip(), branch[1].strip(), change))
            continue
        actor, separator, action = line.partition(": ")
        step = Step(actor.strip(), action.strip()) if separator and action.strip() else Step("", line)
        step.change = change
        steps.append(step)
    if not steps or (len(steps) < 2 and len(steps[0].branches) < 2):
        return None
    return Flow(arguments, steps)


def _impact(arguments: str, body: str, language: str) -> Impact | None:
    """Each line is `who / what: change | note`; the change word comes first after the colon."""
    pairs = _pairs(body)
    if not pairs:
        return None
    areas = []
    for label, value in pairs:
        word, _, note = value.partition(" | ")
        change = change_kind(word)
        if change is None:
            return None
        group, separator, item = label.rpartition(" / ")
        areas.append(ImpactArea(group.strip() if separator else "", item.strip(), change, note.strip()))
    return Impact(arguments, areas)


_PARSERS = {"atlas-chart": _chart, "atlas-stats": _stats, "atlas-compare": _compare, "atlas-flow": _flow,
            "atlas-impact": _impact}


def parse(name: str, arguments: str, body: str, language: str) -> Component | None:
    parser = _PARSERS.get(name.lower())
    return parser(arguments.strip(), body, language) if parser else None


def layer(label: str) -> tuple[str, str] | None:
    """Find a BUSINESS / SYSTEM / CODE lens in a heading; return it and the heading without a bracketed tag."""
    match = re.search(r"\b(BUSINESS|SYSTEM|CODE)\b", label)
    if not match:
        return None
    stripped = re.sub(r"\s*[（(]\s*(?:BUSINESS|SYSTEM|CODE)\s*[)）]\s*$", "", label).strip()
    return match.group(1).lower(), stripped or label


def severity(label: str) -> tuple[str, str] | None:
    """Split a `[high] Title` heading into its severity and title."""
    match = re.match(r"^\[(critical|high|medium|low)\]\s+(.+)$", label, re.IGNORECASE)
    return (match.group(1).lower(), match.group(2)) if match else None
