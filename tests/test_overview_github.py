import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from code_atlas.git import FileChange, change_stats, inspect_repo
from code_atlas.github_report import render_github
from code_atlas.html_report import render_html
from code_atlas.overview import build, kind

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, text=True, capture_output=True).stdout


class OverviewTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.repo = Path(temporary.name) / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.name", "Fixture")
        git(self.repo, "config", "user.email", "fixture@example.invalid")
        (self.repo / "app.py").write_text("A = 1\nB = 2\n")
        (self.repo / "README.md").write_text("# Demo\n")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "base")

    def test_counts_tracked_untracked_binary_and_deleted_files_read_only(self):
        (self.repo / "app.py").write_text("A = 1\nB = 3\nC = 4\n")
        (self.repo / "README.md").unlink()
        (self.repo / "tests").mkdir()
        (self.repo / "tests" / "test_app.py").write_text("x\ny")  # No final newline.
        (self.repo / "logo.png").write_bytes(b"\x89PNG\0\0data")
        git(self.repo, "config", "diff.renames", "copies")
        status_before = git(self.repo, "status", "--porcelain")
        changes = {change.path: change for change in change_stats(inspect_repo(self.repo))}
        self.assertEqual(git(self.repo, "status", "--porcelain"), status_before)
        self.assertEqual(changes["app.py"], FileChange("app.py", "M", 2, 1))
        self.assertEqual(changes["README.md"], FileChange("README.md", "D", 0, 1))
        self.assertEqual(changes["tests/test_app.py"], FileChange("tests/test_app.py", "A", 2, 0))
        self.assertEqual(changes["logo.png"], FileChange("logo.png", "A", None, None))

    def test_commit_and_range_modes(self):
        (self.repo / "app.py").write_text("A = 1\n")
        git(self.repo, "commit", "-qam", "trim")
        self.assertEqual(change_stats(inspect_repo(self.repo), head="HEAD"), [FileChange("app.py", "M", 0, 1)])
        root = {change.path: change.status for change in change_stats(inspect_repo(self.repo), head="HEAD~1")}
        self.assertEqual(root, {"README.md": "A", "app.py": "A"})
        self.assertEqual(len(change_stats(inspect_repo(self.repo), base="HEAD~1")), 1)

    def test_kind_classifies_paths(self):
        cases = {"src/app.py": "code", "tests/test_app.py": "test", "app_test.go": "test", "Button.spec.tsx": "test",
                 "OrderServiceTest.java": "test", "docs/guide.html": "docs", "README.md": "docs",
                 "package-lock.json": "config", ".github/workflows/ci.yml": "config", "Dockerfile": "config"}
        self.assertEqual({path: kind(path) for path in cases}, cases)

    def test_build_shows_charts_only_when_they_compare_something(self):
        single = build([FileChange("app.py", "M", 3, 1)], "en")
        self.assertIn("Files changed: 1 | 0 added, 1 modified, 0 deleted", single)
        self.assertNotIn("atlas-chart", single)
        many = [FileChange(f"src/m{index}.py", "M", 10 - index, 0) for index in range(10)]
        many += [FileChange("tests/test_m.py", "A", 5, 0), FileChange("logo.png", "A", None, None)]
        text = build(many, "ja")
        self.assertIn("変更ファイル: 12 | 追加 2・変更 10・削除 0 / バイナリ 1 件は行数なし", text)
        self.assertIn("`src/m0.py`: +10 −0", text)
        self.assertIn("ほか 3 ファイル: +6 −0", text)  # Ranks 9-11: m7 (3), m8 (2), m9 (1).
        self.assertIn("コード: 55\nテスト: 5", text)
        with self.assertRaises(ValueError):
            build([], "en")

    def test_cli_overview_renders_as_components(self):
        (self.repo / "app.py").write_text("A = 1\nB = 3\n")
        (self.repo / "test_app.py").write_text("assert True\n")
        env = dict(os.environ, PYTHONPATH=str(PROJECT_ROOT))
        result = subprocess.run([sys.executable, "-m", "code_atlas", "--json", "overview", "--repo", str(self.repo)],
                                env=env, text=True, capture_output=True, check=True)
        payload = json.loads(result.stdout)
        self.assertEqual(sorted(item["path"] for item in payload["files"]), ["app.py", "test_app.py"])
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "overview.html"
            render_html("# Change\n\n" + payload["markdown"], destination)
            output = destination.read_text(encoding="utf-8")
        self.assertIn('class="atlas-stat-value">+2</span>', output)
        self.assertIn("atlas-chart-diff", output)
        self.assertIn("atlas-chart-share", output)


class GithubReportTests(unittest.TestCase):
    REPORT = """# Review

**Summary:** One finding.

```atlas-stats
Findings: 1 | 1 high
Files: 2
```

### [high] Refund flag is lost

| Severity | Where |
| --- | --- |
| high | `app/order.py:21-27` |

```atlas-chart diff Changed lines
`a.py`: +10 −5
`b.py`: +1 −0
```

```atlas-chart share Kinds
Code: 3
Tests: 1
```

```atlas-compare
Before: Can cancel shipped
After: Shipped is rejected
After: Paid needs refund
```

```atlas-flow Cancel
Caller: calls `cancel()`
paid => "refund" <needed>
shipped => error
```

> [!NOTE]
> See `app/order.py:3` and [`app/order.py:4`](https://example.com).

```mermaid
flowchart LR
  A --> B
```
"""

    def test_converts_components_to_github_markdown(self):
        output = render_github(self.REPORT)
        self.assertIn("| Findings | Files |\n| --- | --- |\n| **1** | **2** |\n| 1 high |  |", output)
        self.assertIn("### 🟠 **HIGH** Refund flag is lost", output)
        self.assertIn("| 🟠 HIGH | `app/order.py:21-27` |", output)
        self.assertIn("| `a.py` | +10 | −5 | 🟦🟦🟦🟦🟦🟦🟦🟧🟧🟧 |", output)
        self.assertIn("| `b.py` | +1 | −0 | 🟦 |", output)
        self.assertIn("🟦🟦🟦🟦🟦🟦🟦🟦🟧🟧\n", output)
        self.assertIn("| 🟦 Code | 3 | 75% |", output)
        self.assertIn("| Can cancel shipped | Shipped is rejected |\n|  | Paid needs refund |", output)
        self.assertIn('S1["Caller: calls cancel()"]', output)
        self.assertIn('S1 -->|"paid"| S1B1["#quot;refund#quot; #lt;needed#gt;"]', output)
        self.assertIn("> [!NOTE]", output)
        self.assertIn("```mermaid\nflowchart LR\n  A --> B\n```", output)
        self.assertNotIn("atlas-", output)

    def test_links_references_unless_already_linked(self):
        base = "https://github.com/o/r/blob/" + "c" * 40 + "/"
        output = render_github(self.REPORT, base)
        self.assertIn(f"[`app/order.py:21-27`]({base}app/order.py#L21-L27)", output)
        self.assertIn(f"[`app/order.py:3`]({base}app/order.py#L3)", output)
        self.assertIn("[`app/order.py:4`](https://example.com)", output)
        self.assertEqual(output.count("app/order.py#L4"), 0)

    def test_cli_writes_github_markdown_to_stdout_or_a_new_file(self):
        env = dict(os.environ, PYTHONPATH=str(PROJECT_ROOT))
        with tempfile.TemporaryDirectory() as folder:
            report = Path(folder) / "report.md"
            report.write_text(self.REPORT, encoding="utf-8")
            command = [sys.executable, "-m", "code_atlas", "render", "--format", "github", "--report", str(report)]
            stdout = subprocess.run([*command, "-"], env=env, text=True, capture_output=True, check=True).stdout
            self.assertIn("### 🟠 **HIGH**", stdout)
            destination = Path(folder) / "comment.md"
            subprocess.run([*command, str(destination)], env=env, capture_output=True, check=True)
            self.assertEqual(destination.read_text(encoding="utf-8"), stdout)
            again = subprocess.run([*command, str(destination)], env=env, capture_output=True, text=True)
            self.assertNotEqual(again.returncode, 0)
            wrong = subprocess.run([*command, str(Path(folder) / "comment.html")], env=env, capture_output=True, text=True)
            self.assertIn("must end in .md", wrong.stderr)


if __name__ == "__main__":
    unittest.main()
