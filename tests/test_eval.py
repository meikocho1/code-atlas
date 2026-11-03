import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "eval"))

import harness  # noqa: E402


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, text=True, capture_output=True).stdout


class EvalHarnessTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def test_build_reproduces_the_documented_fixtures(self):
        state = self.root / "state"
        harness.build("state", state)
        # examples/sample-explanation.md cites these lines.
        self.assertTrue((state / "order.py").read_text().splitlines()[20].startswith("def cancel("))
        self.assertEqual(git(state, "status", "--short").split("\n")[:3], [" M README.md", " M order.py", "?? test_order.py"])
        schema = self.root / "schema"
        harness.build("schema", schema)
        self.assertEqual(git(schema, "status", "--short"), "")
        self.assertEqual(git(schema, "log", "-1", "--format=%s"), "Record refunds for cancelled orders\n")
        self.assertIn("__pycache__/", (schema / ".git" / "info" / "exclude").read_text())

    def test_build_commits_edits_that_keep_the_file_size(self):
        repo = self.root / "timeout"
        harness.build("timeout-constant", repo)  # 30 -> 60 keeps the size; racy git once kept the old blob.
        change = harness.SCENARIOS / "timeout-constant" / "change" / "network.py"
        self.assertEqual(git(repo, "show", "HEAD:network.py"), change.read_text())

    def test_score_rewards_the_expected_answer_and_flags_mistakes(self):
        tiny = self.root / "tiny"
        harness.build("tiny", tiny)
        good = harness.score("tiny", tiny, "`shipping.py:5` now uses `>=`, so a 5,000 yen subtotal ships free. "
                                           "Why it changed is not established.")
        self.assertEqual((good["hard"], good["soft"]), (1.0, 1.0))
        bad = harness.score("tiny", tiny, "```mermaid\nflowchart TD\n  A --> B\n```\nSee `shipping.py:40`.")
        self.assertEqual(bad["hard"], 0.0)
        self.assertEqual((bad["checks"]["visual"], bad["checks"]["refs"], bad["checks"]["motivation"]), (0.0, 0.0, 0.0))
        self.assertEqual(bad["details"]["unresolved_refs"], ["shipping.py:40-40"])

        schema = self.root / "schema"
        harness.build("schema", schema)
        one_to_many = harness.score("schema", schema, "```mermaid\nerDiagram\n  orders ||--o{ refunds : has\n```")
        self.assertEqual((one_to_many["checks"]["visual"], one_to_many["checks"]["forbidden"]), (1.0, 0.0))

    def test_review_brief_scenario_rewards_a_business_ready_brief(self):
        repo = self.root / "brief"
        harness.build("brief-approval-threshold", repo)
        good = harness.score("brief-approval-threshold", repo, """# Expenses over 100,000 now need a manager

**Summary:** Expenses over 100,000 wait for a manager; an expense of exactly 100,000 is still approved at once.

```atlas-flow Expense approval
Employee: submits an expense
[changed] over 100,000 => waits for a manager
100,000 or less => approved at once
[added] Manager: approves a waiting expense
```

- [ ] An expense of exactly 100,000 skips approval. Is that the policy? (`expenses.py:14`)
- [ ] Anyone can approve; the code does not check that the approver is a manager. (`expenses.py:20-23`)

> [!WARNING]
> Unverified: who calls these functions, and how payment treats a waiting expense. No commit message or PR states why this changed.
""")
        self.assertEqual(good["hard"], 1.0, good)
        wrong = harness.score("brief-approval-threshold", repo,
                              "Expenses of 100,000 or more need a manager (`expenses.py:14`).")
        self.assertEqual(wrong["hard"], 0.0)
        self.assertEqual((wrong["checks"]["visual"], wrong["checks"]["forbidden"]), (0.0, 0.0))
        self.assertIn("(?m)^- \\[ \\] ", wrong["details"]["missing_facts"])

    def test_score_counts_a_diagram_rendered_to_html(self):
        schema = self.root / "schema"
        harness.build("schema", schema)
        diagram = "erDiagram\n  orders ||--o{ refunds : has\n"
        rendered = f'<div class="atlas-diagram"><pre class="mermaid" tabindex="0">{diagram}</pre></div>'
        self.assertEqual(harness.visuals(rendered), ["er"])
        self.assertEqual(harness.visuals(f"```mermaid\n{diagram}```"), ["er"])
        self.assertEqual(harness.visuals("```atlas-flow\nA: start\nB: end\n```"), ["flowchart"])
        self.assertEqual(harness.visuals('<figure class="atlas-flow"><ol></ol></figure>'), ["flowchart"])


if __name__ == "__main__":
    unittest.main()
