#!/usr/bin/env python3
"""Build Code Atlas evaluation scenarios, score reports against them, and run Claude Code on them.

Each scenario lives in eval/scenarios/<id>/: base/ is the first commit, change/ is laid over it,
and scenario.json holds the request and the expectations that score() checks.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "eval" / "scenarios"
sys.path.insert(0, str(ROOT))

from code_atlas.git import inspect_repo  # noqa: E402
from code_atlas.refs import check_refs, find_refs  # noqa: E402

AUTHOR = ("-c", "user.name=Code Atlas Fixture", "-c", "user.email=fixture@example.invalid")
IGNORE = shutil.ignore_patterns("__pycache__", ".DS_Store")
DIAGRAMS = {
    "stateDiagram": "state", "erDiagram": "er", "sequenceDiagram": "sequence",
    "flowchart": "flowchart", "graph": "flowchart", "classDiagram": "class",
}
# Skills deliver HTML files by default; the run has no Write or render access and scores Markdown, so ask for it.
OUTPUT_INSTRUCTION = " Return the complete report as Markdown in your reply; do not create files or HTML."
# ponytail: English phrase lists only; scenario requests ask for English so scoring stays regex-based.
MOTIVATION = {
    "sourced": r"commit message|PR description|pull request",
    "unknown": r"not (?:established|stated|documented|given|known)|unknown|unclear|no (?:commit message|PR|pull request|issue)",
}


def scenario_ids(split: str | None = None) -> list[str]:
    return [
        path.parent.name for path in sorted(SCENARIOS.glob("*/scenario.json"))
        if split is None or json.loads(path.read_text(encoding="utf-8"))["split"] == split
    ]


def load(scenario_id: str) -> dict:
    path = SCENARIOS / scenario_id / "scenario.json"
    if not path.is_file():
        raise ValueError(f"Unknown scenario {scenario_id!r}; choose from {', '.join(scenario_ids())}")
    return json.loads(path.read_text(encoding="utf-8"))


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, stdout=subprocess.DEVNULL)


def build(scenario_id: str, dest: Path) -> dict:
    """Create the scenario repository at a new path: commit base/, then apply change/."""
    spec = load(scenario_id)
    source = SCENARIOS / scenario_id
    dest.mkdir(parents=True)
    _git(dest, "init", "-q")
    with (dest / ".git" / "info" / "exclude").open("a", encoding="utf-8") as stream:
        stream.write(".agents/\n.claude/\n__pycache__/\n")
    shutil.copytree(source / "base", dest, dirs_exist_ok=True, ignore=IGNORE)
    _git(dest, "add", "-A")
    _git(dest, *AUTHOR, "commit", "-qm", spec["base_message"])
    if (source / "change").is_dir():
        shutil.copytree(source / "change", dest, dirs_exist_ok=True, ignore=IGNORE)
    for path in spec.get("delete", []):
        (dest / path).unlink()
    # change/ lands within the same second as the base commit, so an edit that keeps the file size can
    # match Git's stat cache and be skipped ("racy git"). Dropping the cached entries forces a re-hash.
    if spec.get("commit_message"):
        _git(dest, "rm", "-r", "-q", "--cached", ".")
        _git(dest, "add", "-A")
        _git(dest, *AUTHOR, "commit", "-qm", spec["commit_message"])
    elif spec.get("stage"):
        _git(dest, "rm", "-q", "--cached", "--ignore-unmatch", "--", *spec["stage"])
        _git(dest, "add", "--", *spec["stage"])
    return spec


def visuals(report: str) -> list[str]:
    """Name each Mermaid diagram, whether left as a Markdown fence or rendered by `code-atlas render`."""
    kinds = []
    blocks = re.findall(r"```mermaid[^\n]*\n(.*?)```", report, re.DOTALL)
    blocks += re.findall(r'<pre class="mermaid"[^>]*>(.*?)</pre>', report, re.DOTALL)
    for block in blocks:
        words = block.split()
        first = words[0] if words else ""
        kinds.append(next((kind for prefix, kind in DIAGRAMS.items() if first.startswith(prefix)), "other"))
    return kinds


def score(scenario_id: str, repo: Path, report: str) -> dict:
    """Score a report with deterministic checks; soft is their mean, hard needs every check at 1."""
    expect = load(scenario_id)["expect"]
    kinds = visuals(report)
    shown = set(kinds) or {"none"}
    prefer, allow = expect["visual"]["prefer"], set(expect["visual"]["allow"])
    if len(kinds) > 2:
        visual = 0.0
    elif shown == {prefer}:
        visual = 1.0
    else:
        visual = 0.5 if shown <= allow | {prefer} else 0.0

    target = inspect_repo(repo)
    refs = check_refs(target, find_refs(report), target.head if expect["scope"] == "commit" else None)
    unresolved = [f"{item['path']}:{item['start']}-{item['end']}" for item in refs if item["problem"]]
    missing = [pattern for pattern in expect["facts"] if not re.search(pattern, report, re.IGNORECASE)]
    hits = [pattern for pattern in expect["forbidden"] if re.search(pattern, report, re.IGNORECASE)]
    checks = {
        "visual": visual,
        "refs": (len(refs) - len(unresolved)) / len(refs) if refs else 0.0,
        "facts": 1 - len(missing) / len(expect["facts"]) if expect["facts"] else 1.0,
        "forbidden": 0.0 if hits else 1.0,
        "motivation": 1.0 if re.search(MOTIVATION[expect["motivation"]], report, re.IGNORECASE) else 0.0,
    }
    return {
        "scenario": scenario_id,
        "hard": 1.0 if all(value == 1.0 for value in checks.values()) else 0.0,
        "soft": round(sum(checks.values()) / len(checks), 3),
        "checks": checks,
        "details": {"visuals": kinds, "unresolved_refs": unresolved, "missing_facts": missing, "forbidden_hits": hits},
    }


def install_skill(skill: str, repo: Path, text: str | None = None) -> str:
    """Copy a skill into the repository under a unique name, optionally replacing SKILL.md with text."""
    name = f"{skill}-under-test"  # A personal skill with the original name cannot shadow this copy.
    target = repo / ".claude" / "skills" / name
    shutil.copytree(ROOT / "skills" / skill, target, ignore=IGNORE)
    body = text if text is not None else (target / "SKILL.md").read_text(encoding="utf-8")
    (target / "SKILL.md").write_text(
        re.sub(r"^name: .*$", f"name: {name}", body, count=1, flags=re.MULTILINE), encoding="utf-8"
    )
    return name


def run(scenario_id: str, model: str) -> dict:
    """Build the scenario in a temporary directory, run Claude Code with its skill, and score the answer."""
    spec = load(scenario_id)
    work = Path(tempfile.mkdtemp(prefix=f"atlas-eval-{scenario_id}-"))
    repo = work / "repo"
    build(scenario_id, repo)
    name = install_skill(spec["skill"], repo)
    command = [
        "claude", "-p", spec["request"].format(skill=name) + OUTPUT_INSTRUCTION, "--output-format", "json", "--model", model,
        "--setting-sources", "project,local",  # Skip personal hooks, plugins, and skills.
        "--allowedTools", "Read", "Grep", "Glob", "Bash(git:*)",
    ]
    completed = subprocess.run(command, cwd=repo, capture_output=True, text=True, timeout=900)
    if completed.returncode:
        raise RuntimeError(f"claude exited {completed.returncode}: {completed.stderr.strip()[:500]}")
    output = json.loads(completed.stdout)
    report = output.get("result", "")
    (work / "report.md").write_text(report, encoding="utf-8")
    result = score(scenario_id, repo, report)
    result.update(model=model, work_dir=str(work), usage=output.get("usage"), cost_usd=output.get("total_cost_usd"))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    listing = commands.add_parser("list", help="List scenarios")
    listing.add_argument("--split", choices=("train", "val", "test"))
    make = commands.add_parser("build", help="Create a scenario repository at a new path")
    make.add_argument("scenario")
    make.add_argument("dest")
    grade = commands.add_parser("score", help="Score a report against a built scenario repository")
    grade.add_argument("scenario")
    grade.add_argument("repo")
    grade.add_argument("report", help="Report file, or - for stdin")
    execute = commands.add_parser("run", help="Run Claude Code with each scenario's skill and score it")
    execute.add_argument("scenarios", nargs="*", help="Scenario IDs; defaults to all in --split")
    execute.add_argument("--split", choices=("train", "val", "test"))
    execute.add_argument("--model", default="sonnet")
    args = parser.parse_args(argv)
    try:
        if args.command == "list":
            for scenario_id in scenario_ids(args.split):
                spec = load(scenario_id)
                print(f"{scenario_id}\t{spec['split']}\t{spec['skill']}\t{spec['summary']}")
        elif args.command == "build":
            build(args.scenario, Path(args.dest))
            print(f"Fixture ({args.scenario}) created at {args.dest}")
            print(f"Inspect it with: cd {args.dest} && git status --short && git log --oneline")
        elif args.command == "score":
            report = sys.stdin.read() if args.report == "-" else Path(args.report).read_text(encoding="utf-8")
            print(json.dumps(score(args.scenario, Path(args.repo), report), indent=2))
        else:
            results = []
            for scenario_id in args.scenarios or scenario_ids(args.split):
                try:
                    result = run(scenario_id, args.model)
                except (RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
                    result = {"scenario": scenario_id, "error": str(exc)}
                results.append(result)
                print(json.dumps(result), flush=True)
            scored = [item for item in results if "error" not in item]
            print(json.dumps({
                "runs": len(results), "errors": len(results) - len(scored),
                "hard": round(sum(item["hard"] for item in scored) / len(scored), 3) if scored else None,
                "soft": round(sum(item["soft"] for item in scored) / len(scored), 3) if scored else None,
                "cost_usd": round(sum(item.get("cost_usd") or 0 for item in scored), 4),
            }))
    except FileExistsError as exc:
        print(f"Destination already exists: {exc.filename}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
