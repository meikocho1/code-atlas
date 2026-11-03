"""Render Code Atlas's report Markdown as a safe, readable HTML document."""

from __future__ import annotations

import html
import re
from pathlib import Path
from urllib.parse import urlsplit

from . import components, html_components, markdown
from .refs import permalink


_TASK = re.compile(r"^\[([ xX])\]\s+(.+)$")
_REF = re.compile(r"^[^\s`]*[./][^\s`]*:\d+(?:[-–]\d+)?$")


def report_language(source: str) -> str:
    return "ja" if re.search(r"[\u3040-\u30ff\u3400-\u9fff]", source) else "en"


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


def _cell(value: str) -> str:
    if value.strip().lower() in components.SEVERITIES:
        return html_components.severity_badge(value.strip().lower())
    return _inline(value)


def _fence(block: markdown.Block, language: str) -> str:
    component = components.parse(block.name, block.arguments, block.body, language)
    if component is not None:
        return html_components.render(component, _inline, language)
    text = html.escape(block.body)
    if block.name == "mermaid":
        hint = components.text(language, "scroll")
        return f'<div class="atlas-diagram"><span class="atlas-diagram-hint">{hint}</span><pre class="mermaid" tabindex="0">{text}</pre></div>'
    label = html.escape(block.name or "text", quote=True)
    return (f'<div class="atlas-code-block"><span class="atlas-code-label">{label}</span>'
            f'<pre class="atlas-code"><code class="language-{label}">{text}</code></pre></div>')


def _heading(block: markdown.Block) -> str:
    found = components.severity(block.text)
    if found:
        level, title = found
        return f'<h{block.level} class="atlas-finding">{html_components.severity_badge(level)} {_inline(title)}</h{block.level}>'
    lens = components.layer(block.text) if block.level == 2 else None
    if lens:
        return f"<h2>{html_components.layer_tag(lens[0])} {_inline(lens[1])}</h2>"
    return f"<h{block.level}>{_inline(block.text)}</h{block.level}>"


def _paragraph(text: str) -> str:
    css_class = "atlas-summary" if re.match(r"^\*\*(?:結論|Summary|要点)[:：]", text, re.IGNORECASE) else ""
    css_class = css_class or ("atlas-scope" if re.match(r"^\*\*(?:対象|Scope)[:：]", text, re.IGNORECASE) else "")
    class_attribute = f' class="{css_class}"' if css_class else ""
    return f"<p{class_attribute}>{_inline(text)}</p>"


def _block(block: markdown.Block, language: str) -> str:
    if block.kind == "fence":
        return _fence(block, language)
    if block.kind == "heading":
        return _heading(block)
    if block.kind == "rule":
        return "<hr>"
    if block.kind == "table":
        head = "".join(f'<th scope="col">{_inline(cell)}</th>' for cell in block.headers)
        body = "".join(
            "<tr>" + "".join(f"<td>{_cell(row[index]) if index < len(row) else ''}</td>"
                             for index in range(len(block.headers))) + "</tr>"
            for row in block.rows
        )
        return f'<div class="atlas-table"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'
    if block.kind == "list":
        tag = "ol" if block.ordered else "ul"
        items = [_TASK.match(item) for item in block.items]
        if all(items):
            # A review checklist; the boxes can be ticked while reading but are not saved.
            rows = "".join(
                f'<li><label><input type="checkbox"{" checked" if task.group(1) != " " else ""}> '
                f"<span>{_inline(task.group(2))}</span></label></li>"
                for task in items
            )
            return f'<{tag} class="atlas-tasks">{rows}</{tag}>'
        return f"<{tag}>" + "".join(f"<li>{_inline(item)}</li>" for item in block.items) + f"</{tag}>"
    if block.kind == "quote":
        inner = "\n".join(_block(child, language) for child in block.children)
        if block.alert:
            return html_components.callout(block.alert, inner, language)
        return f"<blockquote>{inner}</blockquote>"
    return _paragraph(block.text)


def _content(blocks: list[markdown.Block], language: str) -> tuple[str, str, str, bool]:
    """Render the page body: an at-a-glance header, then one section per level-2 heading."""
    title = next((re.sub(r"[`*_]", "", block.text) for block in blocks
                  if block.kind == "heading" and block.level == 1), "Code Atlas Report")
    first_section = next((index for index, block in enumerate(blocks)
                          if block.kind == "heading" and block.level == 2), len(blocks))
    parts = []
    if first_section:
        glance = "\n".join(_block(block, language) for block in blocks[:first_section])
        parts.append(f'<header class="atlas-glance" aria-label="{components.text(language, "glance")}">{glance}</header>')
    contents = []
    for block in blocks[first_section:]:
        if block.kind == "heading" and block.level == 2:
            if contents:
                parts.append("</section>")
            lens = components.layer(block.text)
            css_class = f"atlas-section atlas-lens-{lens[0]}" if lens else "atlas-section"
            section_id = f"section-{len(contents) + 1}"
            parts.append(f'<section id="{section_id}" class="{css_class}">')
            label = html.escape(re.sub(r"[`*_]", "", lens[1] if lens else block.text))
            tag = html_components.layer_tag(lens[0]) if lens else ""
            contents.append(f'<a href="#{section_id}">{tag}<span>{label}</span></a>')
        parts.append(_block(block, language))
    if contents:
        parts.append("</section>")
    has_diagram = any(_has_mermaid(block) for block in blocks)
    return title, "\n".join(parts), "\n".join(contents), has_diagram


def _has_mermaid(block: markdown.Block) -> bool:
    if block.kind == "quote":
        return any(_has_mermaid(child) for child in block.children)
    return block.kind == "fence" and block.name == "mermaid"


_REF_CHIP = re.compile(r'<code class="atlas-ref">([^<]*):(\d+)(?:[-–](\d+))?</code>')


def _link_refs(content: str, base: str) -> str:
    """Turn `path:line` chips into permalinks, leaving chips that already sit inside a link."""
    parts = re.split(r"(<a [^>]*>.*?</a>)", content, flags=re.DOTALL)
    for index in range(0, len(parts), 2):
        def link(match: re.Match) -> str:
            start = int(match.group(2))
            url = permalink(base, html.unescape(match.group(1)), start, int(match.group(3) or start))
            if url is None:
                return match.group(0)
            return f'<a class="atlas-ref-link" href="{html.escape(url, quote=True)}" rel="noopener noreferrer">{match.group(0)}</a>'
        parts[index] = _REF_CHIP.sub(link, parts[index])
    return "".join(parts)


def render_html(source: str, destination: Path, link_base: str | None = None) -> Path:
    """Create a standalone HTML report without overwriting an existing file.

    With link_base (see refs.permalink_base), `path:line` references link to that commit.
    """
    if not source.strip():
        raise ValueError("Report is empty")
    destination = destination.expanduser()
    if destination.suffix.lower() != ".html":
        raise ValueError("HTML destination must end in .html")
    language = report_language(source)
    title, content, toc, has_diagram = _content(markdown.parse(source), language)
    if link_base:
        content = _link_refs(content, link_base)
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
