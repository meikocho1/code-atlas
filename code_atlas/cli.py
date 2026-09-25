"""Command-line access to the global Code Atlas catalog."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .git import GitError, inspect_repo, resolve_ref, worktree_fingerprint
from .store import Store


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="code-atlas", description="Manage projects and analysis history locally")
    root.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    groups = root.add_subparsers(dest="group", required=True)

    projects = groups.add_parser("project", help="Manage the global project catalog")
    project_actions = projects.add_subparsers(dest="action", required=True)
    add = project_actions.add_parser("add", help="Register a Git repository or worktree")
    add.add_argument("path", nargs="?", default=".")
    add.add_argument("--name")
    add.add_argument("--kind", help="User-defined category, such as app, library, or service")
    add.add_argument("--tag", action="append", default=[], help="Add a tag; may be repeated")
    listing = project_actions.add_parser("list", help="List registered projects")
    listing.add_argument("--kind")
    listing.add_argument("--tag")
    show = project_actions.add_parser("show", help="Show a project by ID or registered path")
    show.add_argument("identifier")
    kind = project_actions.add_parser("kind", help="Set a project's category")
    kind.add_argument("identifier")
    kind.add_argument("value")
    tag_add = project_actions.add_parser("tag-add", help="Add a project tag")
    tag_add.add_argument("identifier")
    tag_add.add_argument("tag")
    tag_remove = project_actions.add_parser("tag-remove", help="Remove a project tag")
    tag_remove.add_argument("identifier")
    tag_remove.add_argument("tag")
    relocate = project_actions.add_parser("relocate", help="Keep history when a repository moves")
    relocate.add_argument("identifier")
    relocate.add_argument("new_path")

    history = groups.add_parser("history", help="Manage immutable analysis records")
    history_actions = history.add_subparsers(dest="action", required=True)
    record = history_actions.add_parser("add", help="Record a Markdown analysis report")
    record.add_argument("--repo", default=".", help="Repository path; auto-registers it")
    record.add_argument("--skill", required=True, help="Skill name used to produce the report")
    record.add_argument("--scope", choices=("worktree", "commit", "range", "project", "custom"), required=True)
    record.add_argument("--base", help="Base commit or ref for a selected range")
    record.add_argument("--head", help="End commit or ref; defaults to the repository HEAD")
    record.add_argument("--report", required=True, help="Markdown report file, or - for stdin")
    runs = history_actions.add_parser("list", help="List analysis records")
    runs.add_argument("--project", help="Project ID or registered path")
    runs.add_argument("--skill")
    run_show = history_actions.add_parser("show", help="Show a saved analysis")
    run_show.add_argument("id")
    export = history_actions.add_parser("export", help="Write a saved report to a new file")
    export.add_argument("id")
    export.add_argument("destination")
    return root


def _project_dict(store: Store, row: object) -> dict:
    item = dict(row)
    item["paths"] = store.paths(item["id"])
    item["tags"] = store.tags(item["id"])
    return item


def _report_text(path: str) -> str:
    text = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError("Report is empty")
    return text


def execute(args: argparse.Namespace, store: Store) -> object:
    if args.group == "project":
        if args.action == "add":
            repo = inspect_repo(args.path)
            row = store.register(repo, name=args.name, kind=args.kind)
            for tag in args.tag:
                if tag.strip():
                    store.add_tag(row["id"], tag.strip())
            return _project_dict(store, row)
        if args.action == "list":
            return [_project_dict(store, row) for row in store.list_projects(kind=args.kind, tag=args.tag)]
        row = store.get_project(args.identifier)
        if args.action == "relocate":
            return _project_dict(store, store.relocate(row["id"], inspect_repo(args.new_path)))
        if args.action == "kind":
            if not args.value.strip():
                raise ValueError("Category cannot be empty")
            store.set_kind(row["id"], args.value.strip())
        elif args.action == "tag-add":
            if not args.tag.strip():
                raise ValueError("Tag cannot be empty")
            store.add_tag(row["id"], args.tag.strip())
        elif args.action == "tag-remove":
            store.remove_tag(row["id"], args.tag)
        return _project_dict(store, store.get_project(row["id"]))

    if args.action == "add":
        report = _report_text(args.report)
        if not args.skill.strip():
            raise ValueError("Skill name cannot be empty")
        if args.scope == "range" and not args.base:
            raise ValueError("--base is required for range history")
        if args.scope == "worktree" and (args.base or args.head):
            raise ValueError("Worktree history uses the current HEAD; omit --base and --head")
        repo = inspect_repo(args.repo)
        base_ref = resolve_ref(repo, args.base) if args.base else None
        head_sha = resolve_ref(repo, args.head) if args.head else repo.head
        if args.scope == "commit" and not args.base and head_sha:
            try:
                base_ref = resolve_ref(repo, f"{head_sha}^")
            except GitError:
                base_ref = None  # Root commit.
        worktree_hash = worktree_fingerprint(repo) if args.scope == "worktree" else None
        project = store.register(repo)
        saved = dict(store.add_run(
            project["id"], skill=args.skill.strip(), scope=args.scope, report=report,
            base_ref=base_ref, head_sha=head_sha, worktree_hash=worktree_hash,
        ))
        saved.pop("report")
        return saved
    if args.action == "list":
        project_id = store.get_project(args.project)["id"] if args.project else None
        return [dict(row) for row in store.list_runs(project_id=project_id, skill=args.skill)]
    row = store.get_run(args.id)
    if args.action == "export":
        destination = Path(args.destination).expanduser()
        with destination.open("x", encoding="utf-8") as stream:
            stream.write(row["report"])
        return {"id": args.id, "destination": str(destination.resolve())}
    return dict(row)


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        with Store() as store:
            result = execute(args, store)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif isinstance(result, list):
            if not result:
                print("No records")
            elif args.group == "project":
                for item in result:
                    print(f"{item['id']}\t{item['kind']}\t{item['name']}\t{', '.join(item['tags'])}")
            else:
                for item in result:
                    print(f"{item['id']}\t{item['created_at']}\t{item['skill']}\t{item['scope']}\t{item['project_id']}")
        elif args.group == "history" and args.action == "show":
            print(result["report"])
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (GitError, ValueError, OSError) as exc:
        print(f"code-atlas: {exc}", file=sys.stderr)
        return 1
