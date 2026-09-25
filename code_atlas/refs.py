"""Find `path:line` references in a report and check them against a repository."""

from __future__ import annotations

import re

from .git import Repo, read_file

# A backquoted reference keeps its whole path, so `app/[id]/page.tsx:3` and `docs/my guide.md:3` survive.
QUOTED = re.compile(r"`([^`\n]+?):(\d+)(?:[-–](\d+))?`")
# ponytail: a path needs a dot or slash, so `10:52` is skipped but `example.com:443` in prose is checked as a file.
# A bare path must start after whitespace or punctuation; an unquoted app/[id]/page.tsx:3 is skipped, not cut to /page.tsx.
BARE = re.compile(r"(?<![^\s(\[{<>\"'*,;|=])([\w./-]*\w):(\d+)(?:[-–](\d+))?")


def find_refs(text: str) -> list[tuple[str, int, int]]:
    refs: list[tuple[str, int, int]] = []
    for path, start, end in QUOTED.findall(text) + BARE.findall(QUOTED.sub(" ", text)):
        if "." not in path and "/" not in path:
            continue
        ref = (path.removeprefix("./"), int(start), int(end or start))
        if ref not in refs:
            refs.append(ref)
    return refs


def check_refs(repo: Repo, refs: list[tuple[str, int, int]], rev: str | None) -> list[dict]:
    files: dict[str, bytes | None] = {}
    results = []
    for path, start, end in refs:
        if path not in files:
            files[path] = read_file(repo, path, rev)
        data = files[path]
        if data is None:
            problem = f"file not found in {rev or 'working tree'}"
        else:
            count = len(data.splitlines())
            problem = None if 1 <= start <= end <= count else f"lines {start}-{end} outside 1-{count}"
        results.append({"path": path, "start": start, "end": end, "problem": problem})
    return results
