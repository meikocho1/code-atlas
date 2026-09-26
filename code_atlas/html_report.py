"""Render Code Atlas's report Markdown as a safe, readable HTML document."""

from __future__ import annotations

import html
import re
from pathlib import Path
from urllib.parse import urlsplit

from . import components


_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})([^\r\n]*)$")
_LIST = re.compile(r"^ {0,3}([-*+]|\d+[.)])\s+(.+)$")
_RULE = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$")
_TABLE_RULE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$")
_REF = re.compile(r"^[^\s`]*[./][^\s`]*:\d+(?:[-–]\d+)?$")
_SEVERITY_HEADING = re.compile(r"^\[(critical|high|medium|low)\]\s+(.+)$", re.IGNORECASE)
_CALLOUT = re.compile(r"^\[!(note|tip|important|warning|caution)\]\s*$", re.IGNORECASE)


def _safe_url(value: str) -> str | None:
    url = value.strip()
    if not url or url.startswith("//"):
        return None
    try:
        parsed = urlsplit(url)
    except ValueError:
        return None
    if parsed.scheme and parsed.scheme.lower() not in {"http", "https", "mailto"}:
        return None
    if not parsed.scheme and url.startswith("\\"):
        return None
    return html.escape(url, quote=True)


def _inline(value: str, depth: int = 0) -> str:
    """Render the small inline Markdown set used by Code Atlas reports."""
    if depth > 5:
        return html.escape(value)
    result: list[str] = []
    index = 0
    while index < len(value):
        if value[index] == "`":
            length = len(value[index:]) - len(value[index:].lstrip("`"))
            marker = "`" * length
            end = value.find(marker, index + length)
            if end != -1:
                code = value[index + length:end]
                css_class = ' class="atlas-ref"' if _REF.match(code) else ""
                result.append(f"<code{css_class}>{html.escape(code)}</code>")
                index = end + length
                continue
        if value[index] == "[":
            middle = value.find("](", index + 1)
            end = value.find(")", middle + 2) if middle != -1 else -1
            if end != -1:
                href = _safe_url(value[middle + 2:end])
                if href is not None:
                    label = _inline(value[index + 1:middle], depth + 1)
                    result.append(f'<a href="{href}" rel="noopener noreferrer">{label}</a>')
                    index = end + 1
                    continue
        if value.startswith("**", index):
            end = value.find("**", index + 2)
            if end > index + 2:
                result.append(f"<strong>{_inline(value[index + 2:end], depth + 1)}</strong>")
                index = end + 2
                continue
        if value[index] == "*":
            end = value.find("*", index + 1)
            if end > index + 1:
                result.append(f"<em>{_inline(value[index + 1:end], depth + 1)}</em>")
                index = end + 1
                continue
        if value[index] == "\\" and index + 1 < len(value):
            result.append(html.escape(value[index + 1]))
            index += 2
            continue
        result.append(html.escape(value[index]))
        index += 1
    return "".join(result)


def _table_cells(line: str) -> list[str]:
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


def _starts_block(line: str) -> bool:
    return bool(_HEADING.match(line) or _FENCE.match(line) or _LIST.match(line)
                or _RULE.match(line) or line.lstrip().startswith(">"))


def _content(markdown: str, language: str) -> tuple[str, str, str, bool]:
    lines = markdown.splitlines()
    parts: list[str] = []
    contents: list[str] = []
    title = "Code Atlas Report"
    title_found = False
    has_diagram = False
    section_open = False
    position = 0
    section_number = 0
    while position < len(lines):
        line = lines[position]
        if not line.strip():
            position += 1
            continue

        fence = _FENCE.match(line)
        if fence:
            marker, info = fence.groups()
            position += 1
            code: list[str] = []
            while position < len(lines):
                closing = _FENCE.match(lines[position])
                if closing and closing.group(1)[0] == marker[0] and len(closing.group(1)) >= len(marker) and not closing.group(2).strip():
                    position += 1
                    break
                code.append(lines[position])
                position += 1
            name, _, arguments = info.strip().partition(" ")
            renderer = components.RENDERERS.get(name.lower())
            rendered = renderer(arguments, "\n".join(code), _inline, language) if renderer else None
            if rendered is not None:
                parts.append(rendered)
                continue
            text = html.escape("\n".join(code))
            if name.lower() == "mermaid":
                has_diagram = True
                hint = components.text(language, "scroll")
                parts.append(f'<div class="atlas-diagram"><span class="atlas-diagram-hint">{hint}</span><pre class="mermaid" tabindex="0">{text}</pre></div>')
            else:
                label = html.escape(name or "text", quote=True)
                parts.append(f'<div class="atlas-code-block"><span class="atlas-code-label">{label}</span><pre class="atlas-code"><code class="language-{label}">{text}</code></pre></div>')
            continue

        heading = _HEADING.match(line)
        if heading:
            level = len(heading.group(1))
            label = heading.group(2).strip()
            if level == 1 and not title_found:
                title = re.sub(r"[`*_]", "", label)
                title_found = True
            if level == 2:
                if section_open:
                    parts.append("</section>")
                section_number += 1
                section_open = True
                css_class = "atlas-business" if "BUSINESS" in label.upper() else "atlas-section"
                parts.append(f'<section id="section-{section_number}" class="{css_class}">')
                contents.append(f'<a href="#section-{section_number}">{html.escape(re.sub(r"[`*_]", "", label))}</a>')
            severity = _SEVERITY_HEADING.match(label)
            if severity:
                badge = components.severity_badge(severity.group(1))
                parts.append(f'<h{level} class="atlas-finding">{badge} {_inline(severity.group(2))}</h{level}>')
            else:
                parts.append(f"<h{level}>{_inline(label)}</h{level}>")
            position += 1
            continue

        if _RULE.match(line):
            parts.append("<hr>")
            position += 1
            continue

        if position + 1 < len(lines) and "|" in line and _TABLE_RULE.match(lines[position + 1]):
            headers = _table_cells(line)
            position += 2
            rows: list[list[str]] = []
            while position < len(lines) and "|" in lines[position] and lines[position].strip():
                rows.append(_table_cells(lines[position]))
                position += 1
            table = ['<div class="atlas-table"><table><thead><tr>']
            table.extend(f"<th scope=\"col\">{_inline(cell)}</th>" for cell in headers)
            table.append("</tr></thead><tbody>")
            for row in rows:
                table.append("<tr>")
                table.extend(f"<td>{_cell(row[index]) if index < len(row) else ''}</td>" for index in range(len(headers)))
                table.append("</tr>")
            table.append("</tbody></table></div>")
            parts.append("".join(table))
            continue

        item = _LIST.match(line)
        if item:
            ordered = item.group(1)[0].isdigit()
            tag = "ol" if ordered else "ul"
            parts.append(f"<{tag}>")
            while position < len(lines):
                current = _LIST.match(lines[position])
                if not current or current.group(1)[0].isdigit() != ordered:
                    break
                parts.append(f"<li>{_inline(current.group(2))}</li>")
                position += 1
            parts.append(f"</{tag}>")
            continue

        if line.lstrip().startswith(">"):
            quoted = []
            while position < len(lines) and lines[position].lstrip().startswith(">"):
                quoted.append(re.sub(r"^ ?", "", lines[position].lstrip()[1:], count=1))
                position += 1
            alert = _CALLOUT.match(quoted[0].strip())
            inner = _content("\n".join(quoted[1:] if alert else quoted), language)[1]
            if alert:
                parts.append(components.callout(alert.group(1).lower(), inner, language))
            else:
                parts.append(f"<blockquote>{inner}</blockquote>")
            continue

        paragraph = [line.strip()]
        position += 1
        while position < len(lines) and lines[position].strip() and not _starts_block(lines[position]):
            if position + 1 < len(lines) and "|" in lines[position] and _TABLE_RULE.match(lines[position + 1]):
                break
            paragraph.append(lines[position].strip())
            position += 1
        text = " ".join(paragraph)
        css_class = "atlas-summary" if re.match(r"^\*\*(?:結論|Summary|要点)[:：]", text, re.IGNORECASE) else ""
        css_class = css_class or ("atlas-scope" if re.match(r"^\*\*(?:対象|Scope)[:：]", text, re.IGNORECASE) else "")
        class_attribute = f' class="{css_class}"' if css_class else ""
        parts.append(f"<p{class_attribute}>{_inline(text)}</p>")

    if section_open:
        parts.append("</section>")
    return title, "\n".join(parts), "\n".join(contents), has_diagram


def _cell(value: str) -> str:
    if value.strip().lower() in components.SEVERITIES:
        return components.severity_badge(value)
    return _inline(value)


def render_html(markdown: str, destination: Path) -> Path:
    """Create a standalone HTML report without overwriting an existing file."""
    if not markdown.strip():
        raise ValueError("Report is empty")
    destination = destination.expanduser()
    if destination.suffix.lower() != ".html":
        raise ValueError("HTML destination must end in .html")
    language = "ja" if re.search(r"[\u3040-\u30ff\u3400-\u9fff]", markdown) else "en"
    title, content, toc, has_diagram = _content(markdown, language)
    style = Path(__file__).with_name("report.css").read_text(encoding="utf-8")
    contents_label = "目次" if language == "ja" else "Contents"
    nav = f'<nav aria-label="{contents_label}"><span class="atlas-nav-label">CONTENTS</span>{toc}</nav>' if toc else ""
    diagram_script = """
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
  const token = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  mermaid.initialize({
    startOnLoad: false,
    securityLevel: 'strict',
    theme: 'base',
    themeVariables: {
      darkMode: window.matchMedia('(prefers-color-scheme: dark)').matches,
      background: token('--paper'),
      primaryColor: token('--accent-soft'),
      primaryTextColor: token('--ink'),
      primaryBorderColor: token('--line-strong'),
      lineColor: token('--muted'),
      secondaryColor: token('--page'),
      tertiaryColor: token('--paper'),
      edgeLabelBackground: token('--paper'),
      fontFamily: getComputedStyle(document.body).fontFamily,
    },
  });
  mermaid.run({ querySelector: '.mermaid' }).then(() => {
    if (window.matchMedia('(max-width: 850px)').matches) {
      document.querySelectorAll('.atlas-diagram .mermaid').forEach((diagram) => {
        diagram.scrollLeft = (diagram.scrollWidth - diagram.clientWidth) / 2;
      });
    }
  });
</script>""" if has_diagram else ""
    page = f"""<!doctype html>
<html lang="{language}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>{style}</style>
</head>
<body>
  <header class="atlas-topbar"><span class="atlas-mark">CA</span><span>Code Atlas</span><span class="atlas-topbar-end">REPORT</span></header>
  <div class="atlas-layout">{nav}<main id="main-content">
    <div class="atlas-kicker">CODE ATLAS · ANALYSIS</div>
    {content}
  </main></div>
  {diagram_script}
</body>
</html>
"""
    with destination.open("x", encoding="utf-8") as stream:
        stream.write(page)
    return destination.resolve()
