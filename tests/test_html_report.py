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


if __name__ == "__main__":
    unittest.main()
