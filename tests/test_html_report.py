import tempfile
import unittest
from pathlib import Path

from code_atlas.html_report import render_html


class HtmlReportTests(unittest.TestCase):
    def test_renders_report_sections_table_and_diagram(self):
        report = """# 注文の変更

**結論:** キャンセルできます。

## 利用者への影響（BUSINESS）

| 状態 | 結果 |
| --- | --- |
| 新規 | 返金不要 |

```mermaid
flowchart TD
  A[新規] --> B[キャンセル]
```

## 実装（CODE）

根拠は `order.py:21-27` です。
"""
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "report.html"
            render_html(report, path)
            output = path.read_text(encoding="utf-8")
        self.assertIn("<title>注文の変更</title>", output)
        self.assertIn('class="atlas-summary"', output)
        self.assertIn('class="atlas-business"', output)
        self.assertIn("<th scope=\"col\">状態</th>", output)
        self.assertIn('class="mermaid"', output)
        self.assertIn("mermaid@11", output)
        self.assertIn('href="#section-1"', output)
        self.assertIn("order.py:21-27", output)

    def test_escapes_html_and_unsafe_links(self):
        report = "# Title\n\n<script>alert(1)</script> [safe](https://example.com) [bad](javascript:alert(1))\n"
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "report.html"
            render_html(report, path)
            output = path.read_text(encoding="utf-8")
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", output)
        self.assertNotIn("<script>alert(1)</script>", output)
        self.assertIn('href="https://example.com"', output)
        self.assertNotIn('href="javascript:', output)

    def test_preserves_literal_mermaid_inside_a_longer_code_fence(self):
        report = "# Title\n\n````markdown\n```mermaid\nA --> B\n```\n````\n"
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "report.html"
            render_html(report, path)
            output = path.read_text(encoding="utf-8")
        self.assertNotIn('class="mermaid"', output)
        self.assertIn("```mermaid", output)

    def test_refuses_to_overwrite_and_requires_html_extension(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "report.html"
            render_html("# Report\n", path)
            with self.assertRaises(FileExistsError):
                render_html("# Changed\n", path)
            self.assertIn("Report", path.read_text(encoding="utf-8"))
            with self.assertRaisesRegex(ValueError, "end in .html"):
                render_html("# Report\n", Path(folder) / "report.md")


    def render(self, report):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "report.html"
            render_html(report, path)
            return path.read_text(encoding="utf-8")

    def test_renders_stats_compare_and_callouts(self):
        output = self.render("""# Title

```atlas-stats
Files changed: 3 | 1 untracked
Findings: 0
```

```atlas-compare
Before: Orders cannot be cancelled
After: Unshipped orders can be cancelled
After: Shipped orders are rejected
After: Status: `cancelled`
```

> [!WARNING]
> Refunds are **not** executed.
>
> - Nothing is saved

> Plain quote
""")
        self.assertIn('class="atlas-stat-value">3</span><span class="atlas-stat-note">1 untracked', output)
        self.assertIn('style="--columns:2"', output)
        self.assertIn("<li>Shipped orders are rejected</li>", output)
        self.assertIn("<li>Status: <code>cancelled</code></li>", output)
        self.assertIn('atlas-callout atlas-callout-warning', output)
        self.assertIn(">Warning</p>", output)
        self.assertIn("<strong>not</strong>", output)
        self.assertIn("<li>Nothing is saved</li>", output)
        self.assertIn("<blockquote><p>Plain quote</p></blockquote>", output)
        self.assertNotIn("atlas-stats\n", output)

    def test_renders_charts_with_table_views(self):
        output = self.render("""# 変更

```atlas-chart bar Changed lines
`app/models/order.rb:12`: 12 lines
docs: 3
```

```atlas-chart diff 差分
`order.py`: +9 −1
README.md: +1 -0
```

```atlas-chart share 指摘
high: 1
low: 3
```
""")
        self.assertIn('<figcaption>Changed lines</figcaption>', output)
        self.assertIn('style="width:100.00%"', output)
        self.assertIn('style="width:25.00%"', output)
        self.assertIn('>12 lines</span>', output)
        self.assertIn('<code class="atlas-ref">app/models/order.rb:12</code>', output)
        self.assertIn('+9 −1', output)
        self.assertIn('>追加</li>', output)
        self.assertIn('style="flex-grow:3"', output)
        self.assertIn("3 · 75%", output)
        self.assertEqual(output.count("<summary>表で見る</summary>"), 3)

    def test_share_folds_series_past_eight_into_other(self):
        rows = "\n".join(f"item{index}: 1" for index in range(10))
        output = self.render(f"# Title\n\n```atlas-chart share Many\n{rows}\n```\n")
        self.assertIn("atlas-series-8", output)
        self.assertNotIn("atlas-series-9", output)
        self.assertIn("Other<span", output)
        self.assertIn("3 · 30%", output)

    def test_malformed_components_fall_back_to_code(self):
        output = self.render("""# Title

```atlas-chart bar Broken
order.py: many
```

```atlas-chart pie Unknown
a: 1
```

```atlas-compare
Only: one column
```
""")
        self.assertNotIn("atlas-chart-bar", output)
        self.assertIn('<code class="language-atlas-chart">order.py: many', output)
        self.assertIn("a: 1", output)
        self.assertIn("Only: one column", output)

    def test_severity_badges_in_headings_and_table_cells(self):
        output = self.render("""# Review

### [HIGH] Refund flag is lost

| Severity | File |
| --- | --- |
| critical | `a.py:1` |
""")
        self.assertIn('<h3 class="atlas-finding"><span class="atlas-badge atlas-severity-high">HIGH</span> Refund flag is lost</h3>', output)
        self.assertIn('<td><span class="atlas-badge atlas-severity-critical">CRITICAL</span></td>', output)

    def test_component_content_is_escaped(self):
        output = self.render("""# Title

```atlas-chart bar <img src=x onerror=alert(1)>
<script>alert(1)</script>: 5
```

```atlas-stats
"><b>x</b>: <i>1</i>
```
""")
        self.assertNotIn("<script>alert(1)</script>", output)
        self.assertNotIn("<img src=x", output)
        self.assertNotIn("<b>x</b>", output)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", output)

    def test_links_references_to_a_commit_when_given_a_base(self):
        report = ("# Title\n\nSee `app/order.py:21-27`, `README.md:4`, `../secret.py:1`, "
                  "and [the `order.py:3` note](https://example.com).\n")
        base = "https://github.com/o/r/blob/" + "a" * 40 + "/"
        with tempfile.TemporaryDirectory() as folder:
            linked, plain = Path(folder) / "linked.html", Path(folder) / "plain.html"
            render_html(report, linked, base)
            render_html(report, plain)
            output = linked.read_text(encoding="utf-8")
            self.assertNotIn("atlas-ref-link\"", plain.read_text(encoding="utf-8"))
        self.assertIn(f'<a class="atlas-ref-link" href="{base}app/order.py#L21-L27"', output)
        self.assertIn(f'href="{base}README.md#L4"', output)
        self.assertNotIn("secret.py#", output)
        self.assertNotIn("order.py#L3", output)  # Already inside a link; anchors cannot nest.


if __name__ == "__main__":
    unittest.main()
