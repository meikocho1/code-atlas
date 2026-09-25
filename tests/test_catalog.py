import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from code_atlas.git import inspect_repo, worktree_fingerprint
from code_atlas.refs import check_refs, find_refs
from code_atlas.store import Store


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.strip()


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.name", "Fixture")
        git(self.repo, "config", "user.email", "fixture@example.invalid")
        (self.repo / "main.py").write_text("VALUE = 1\n")
        git(self.repo, "add", "main.py")
        git(self.repo, "commit", "-qm", "base")
        self.data = self.root / "data"

    def test_fingerprint_covers_tracked_and_untracked_contents(self):
        repo = inspect_repo(self.repo)
        self.assertIsNone(worktree_fingerprint(repo))
        (self.repo / "main.py").write_text("VALUE = 2\n")
        first = worktree_fingerprint(repo)
        self.assertIsNotNone(first)
        untracked = self.repo / "new.py"
        untracked.write_text("NEXT = 1\n")
        second = worktree_fingerprint(repo)
        self.assertNotEqual(first, second)
        untracked.write_text("NEXT = 2\n")
        self.assertNotEqual(second, worktree_fingerprint(repo))

    def test_worktree_uses_same_project(self):
        branch = self.root / "other-worktree"
        git(self.repo, "worktree", "add", "-qb", "other", str(branch))
        with Store(self.data) as store:
            first = store.register(inspect_repo(self.repo))
            second = store.register(inspect_repo(branch))
            self.assertEqual(first["id"], second["id"])
            self.assertEqual(len(store.paths(first["id"])), 2)

    def test_tags_categories_and_immutable_runs(self):
        with Store(self.data) as store:
            project = store.register(inspect_repo(self.repo), kind="service")
            store.add_tag(project["id"], "client-a")
            store.add_tag(project["id"], "client-a")
            self.assertEqual(store.tags(project["id"]), ["client-a"])
            self.assertEqual(len(store.list_projects(kind="service", tag="client-a")), 1)
            run = store.add_run(
                project["id"], skill="understand-change", scope="commit", report="# Explanation\n",
                base_ref=None, head_sha=inspect_repo(self.repo).head, worktree_hash=None,
            )
            self.assertEqual(store.get_run(run["id"])["report"], "# Explanation\n")
            self.assertEqual(len(store.list_runs(project_id=project["id"], skill="review-change")), 0)
            self.assertEqual(len(store.list_runs(project_id=project["id"])), 1)

    def test_relocation_keeps_project_and_history(self):
        with Store(self.data) as store:
            project = store.register(inspect_repo(self.repo))
            run = store.add_run(
                project["id"], skill="understand-project", scope="project", report="Current map",
                base_ref=None, head_sha=inspect_repo(self.repo).head, worktree_hash=None,
            )
            moved = self.root / "moved-repo"
            self.repo.rename(moved)
            relocated = store.relocate(project["id"], inspect_repo(moved))
            self.assertEqual(relocated["id"], project["id"])
            self.assertEqual(store.get_run(run["id"])["project_id"], project["id"])
            self.assertEqual(store.paths(project["id"]), [str(moved.resolve())])

    def test_cli_register_record_filter_and_export(self):
        report = self.root / "report.md"
        report.write_text("# Review\nConcrete result.\n")

        def cli(*args):
            env = dict(os.environ, CODE_ATLAS_DATA_DIR=str(self.data), PYTHONPATH=str(PROJECT_ROOT))
            process = subprocess.run(
                [sys.executable, "-m", "code_atlas", "--json", *args],
                cwd=self.root, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            return json.loads(process.stdout)

        project = cli("project", "add", str(self.repo), "--kind", "service", "--tag", "client-a")
        self.assertEqual(project["kind"], "service")
        self.assertEqual(len(cli("project", "list", "--tag", "client-a")), 1)
        run = cli("history", "add", "--repo", str(self.repo), "--skill", "review-change",
                  "--scope", "commit", "--report", str(report))
        self.assertEqual(run["project_id"], project["id"])
        self.assertIsNone(run["base_ref"])  # The fixture's HEAD is a root commit.
        self.assertEqual(len(cli("history", "list", "--project", project["id"])), 1)
        (self.repo / "pkg").mkdir()
        self.assertEqual(len(cli("history", "list", "--project", str(self.repo / "pkg"))), 1)
        destination = self.root / "exported.md"
        cli("history", "export", run["id"], str(destination))
        self.assertEqual(destination.read_text(), report.read_text())

    def test_range_history_resolves_selected_revisions(self):
        original = git(self.repo, "rev-parse", "HEAD")
        (self.repo / "main.py").write_text("VALUE = 2\n")
        git(self.repo, "add", "main.py")
        git(self.repo, "commit", "-qm", "next")
        latest = git(self.repo, "rev-parse", "HEAD")
        report = self.root / "range.md"
        report.write_text("# Changed value\n")
        env = dict(os.environ, CODE_ATLAS_DATA_DIR=str(self.data), PYTHONPATH=str(PROJECT_ROOT))
        command = [sys.executable, "-m", "code_atlas", "--json", "history", "add",
                   "--repo", str(self.repo), "--skill", "understand-change", "--scope", "range",
                   "--report", str(report)]
        missing_base = subprocess.run(command, env=env, text=True, capture_output=True)
        self.assertEqual(missing_base.returncode, 1)
        saved = subprocess.run(command + ["--base", "HEAD~1", "--head", "HEAD"],
                               env=env, text=True, capture_output=True)
        self.assertEqual(saved.returncode, 0, saved.stderr)
        item = json.loads(saved.stdout)
        self.assertEqual(item["base_ref"], original)
        self.assertEqual(item["head_sha"], latest)
        self.assertIsNone(item["worktree_hash"])
        commit = subprocess.run(
            [sys.executable, "-m", "code_atlas", "--json", "history", "add",
             "--repo", str(self.repo), "--skill", "understand-change", "--scope", "commit",
             "--report", str(report)],
            env=env, text=True, capture_output=True,
        )
        self.assertEqual(commit.returncode, 0, commit.stderr)
        self.assertEqual(json.loads(commit.stdout)["base_ref"], original)

    def test_worktree_record_rejects_revision_flags_and_clean_tree(self):
        report = self.root / "report.md"
        report.write_text("# Working tree\n")
        env = dict(os.environ, CODE_ATLAS_DATA_DIR=str(self.data), PYTHONPATH=str(PROJECT_ROOT))
        command = [sys.executable, "-m", "code_atlas", "history", "add", "--repo", str(self.repo),
                   "--skill", "understand-change", "--scope", "worktree", "--report", str(report)]
        process = subprocess.run(command + ["--head", "HEAD"], env=env, text=True, capture_output=True)
        self.assertEqual(process.returncode, 1)
        self.assertIn("omit --base and --head", process.stderr)
        clean = subprocess.run(command, env=env, text=True, capture_output=True)
        self.assertEqual(clean.returncode, 1)
        self.assertIn("--scope commit", clean.stderr)

    def test_check_refs_against_worktree_and_commit(self):
        (self.repo / "main.py").write_text("VALUE = 2\nNEXT = 3\nLAST = 4\n")
        (self.root / "outside.txt").write_text("secret\n")
        (self.repo / "app" / "[id]").mkdir(parents=True)
        (self.repo / "app" / "[id]" / "page.tsx").write_text("export default 1\nexport const x = 2\n")
        (self.repo / "link.txt").symlink_to(self.root / "outside.txt")
        refs = find_refs("See `main.py:1`, `app/[id]/page.tsx:2`, `link.txt:1`, main.py:2-3, ./main.py:1, "
                         "missing.py:2, ../outside.txt:1, app/[id]/page.tsx:2 at 10:52.\n")
        self.assertEqual(refs, [("main.py", 1, 1), ("app/[id]/page.tsx", 2, 2), ("link.txt", 1, 1),
                                ("main.py", 2, 3), ("missing.py", 2, 2), ("../outside.txt", 1, 1)])
        repo = inspect_repo(self.repo)
        self.assertEqual([item["problem"] is None for item in check_refs(repo, refs, None)],
                         [True, True, False, True, False, False])
        self.assertEqual([item["problem"] is None for item in check_refs(repo, refs, repo.head)],
                         [True, False, False, False, False, False])

        env = dict(os.environ, CODE_ATLAS_DATA_DIR=str(self.data), PYTHONPATH=str(PROJECT_ROOT))
        command = [sys.executable, "-m", "code_atlas", "check-refs", "--repo", str(self.repo), "--report", "-"]
        passing = subprocess.run(command, input="`main.py:1-3`\n", env=env, text=True, capture_output=True)
        self.assertEqual(passing.returncode, 0, passing.stderr)
        failing = subprocess.run(command + ["--rev", "HEAD"], input="`main.py:1-3`\n", env=env, text=True, capture_output=True)
        self.assertEqual(failing.returncode, 1)
        self.assertIn("outside 1-1", failing.stdout)


if __name__ == "__main__":
    unittest.main()
