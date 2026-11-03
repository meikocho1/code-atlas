"""Parse Code Atlas report Markdown into blocks that several renderers share.

Only the block set Code Atlas reports use is recognized: headings, paragraphs, lists, tables,
fenced code (including components and Mermaid), quotes and GitHub alerts, and rules. Each
block keeps its source lines, so a renderer can pass a block through unchanged.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})([^\r\n]*)$")
LIST_ITEM = re.compile(r"^ {0,3}([-*+]|\d+[.)])\s+(.+)$")
RULE = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$")
TABLE_RULE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$")
ALERT = re.compile(r"^\[!(note|tip|important|warning|caution)\]\s*$", re.IGNORECASE)


@dataclass
class Block:
    kind: str  # heading, paragraph, list, table, fence, quote, rule
    source: list[str]
    level: int = 0  # heading level
    text: str = ""  # heading or paragraph text
    ordered: bool = False
    items: list[str] = field(default_factory=list)
    headers: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    info: str = ""  # fence info string, e.g. "mermaid" or "atlas-chart bar Title"
    body: str = ""  # fence body
    alert: str = ""  # quote: GitHub alert kind, if any
    children: list["Block"] = field(default_factory=list)  # quote contents

    @property
    def name(self) -> str:
        """The fence's language or component name, lowercased."""
        return self.info.strip().partition(" ")[0].lower()

    @property
    def arguments(self) -> str:
        return self.info.strip().partition(" ")[2].strip()


def table_cells(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    cells: list[str] = []
    cell: list[str] = []
    escaped = False
    in_code = False
    for character in line:
        if escaped:
            cell.append(character)
            escaped = False
        elif character == "\\":
            escaped = True
        elif character == "`":
            in_code = not in_code
            cell.append(character)
        elif character == "|" and not in_code:
            cells.append("".join(cell).strip())
            cell = []
        else:
            cell.append(character)
    cells.append("".join(cell).strip())
    return cells


def _starts_block(lines: list[str], position: int) -> bool:
    line = lines[position]
    if HEADING.match(line) or FENCE.match(line) or LIST_ITEM.match(line) or RULE.match(line):
        return True
    if line.lstrip().startswith(">"):
        return True
    return position + 1 < len(lines) and "|" in line and bool(TABLE_RULE.match(lines[position + 1]))


def parse(markdown: str) -> list[Block]:
    lines = markdown.splitlines()
    blocks: list[Block] = []
    position = 0
    while position < len(lines):
        line = lines[position]
        start = position
        if not line.strip():
            position += 1
            continue

        fence = FENCE.match(line)
        if fence:
            marker, info = fence.groups()
            position += 1
            body: list[str] = []
            while position < len(lines):
                closing = FENCE.match(lines[position])
                if (closing and closing.group(1)[0] == marker[0] and len(closing.group(1)) >= len(marker)
                        and not closing.group(2).strip()):
                    position += 1
                    break
                body.append(lines[position])
                position += 1
            blocks.append(Block("fence", lines[start:position], info=info.strip(), body="\n".join(body)))
            continue

        heading = HEADING.match(line)
        if heading:
            position += 1
            blocks.append(Block("heading", [line], level=len(heading.group(1)), text=heading.group(2).strip()))
            continue

        if RULE.match(line):
            position += 1
            blocks.append(Block("rule", [line]))
            continue

        if position + 1 < len(lines) and "|" in line and TABLE_RULE.match(lines[position + 1]):
            headers = table_cells(line)
            position += 2
            rows = []
            while position < len(lines) and "|" in lines[position] and lines[position].strip():
                rows.append(table_cells(lines[position]))
                position += 1
            blocks.append(Block("table", lines[start:position], headers=headers, rows=rows))
            continue

        item = LIST_ITEM.match(line)
        if item:
            ordered = item.group(1)[0].isdigit()
            items = []
            while position < len(lines):
                current = LIST_ITEM.match(lines[position])
                if not current or current.group(1)[0].isdigit() != ordered:
                    break
                items.append(current.group(2))
                position += 1
            blocks.append(Block("list", lines[start:position], ordered=ordered, items=items))
            continue

        if line.lstrip().startswith(">"):
            quoted = []
            while position < len(lines) and lines[position].lstrip().startswith(">"):
                quoted.append(re.sub(r"^ ?", "", lines[position].lstrip()[1:], count=1))
                position += 1
            alert = ALERT.match(quoted[0].strip())
            children = parse("\n".join(quoted[1:] if alert else quoted))
            blocks.append(Block("quote", lines[start:position], alert=alert.group(1).lower() if alert else "",
                                children=children))
            continue

        paragraph = [line.strip()]
        position += 1
        while position < len(lines) and lines[position].strip() and not _starts_block(lines, position):
            paragraph.append(lines[position].strip())
            position += 1
        blocks.append(Block("paragraph", lines[start:position], text=" ".join(paragraph)))
    return blocks
