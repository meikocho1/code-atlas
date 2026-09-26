"""Find `path:line` references in a report and check them against a repository."""

from __future__ import annotations

import re
from urllib.parse import quote, urlsplit

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


_SCP_REMOTE = re.compile(r"^[\w.-]+@([\w.-]+):(?!/)(.+)$")
_SHA = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
# Hosts whose file-view URL shape is known; others get no links rather than guessed ones.
_HOSTS = {"github.com": "{repo}/blob/{sha}/", "gitlab.com": "{repo}/-/blob/{sha}/"}


def permalink_base(remote: str | None, sha: str | None) -> str | None:
    """Return the URL prefix for files at a commit on GitHub or GitLab, or None.

    Only the host and repository path are kept, so credentials in an HTTPS remote never
    reach a report.
    """
    if not remote or not sha or not _SHA.match(sha):
        return None
    scp = _SCP_REMOTE.match(remote.strip())
    if scp:
        host, path = scp.groups()
    else:
        try:
            parsed = urlsplit(remote.strip())
            host, path = parsed.hostname or "", parsed.path
        except ValueError:
            return None
        if parsed.scheme not in {"https", "http", "ssh", "git"}:
            return None
    path = path.strip("/").removesuffix(".git")
    template = _HOSTS.get(host.lower())
    if template is None or len(path.split("/")) < 2 or ".." in path.split("/"):
        return None
    repository = f"https://{host.lower()}/{quote(path, safe='/')}"
    return template.format(repo=repository, sha=sha)


def permalink(base: str, path: str, start: int, end: int) -> str | None:
    """Link one reference under a permalink base; None for paths that leave the repository."""
    path = path.removeprefix("./")
    if not path or path.startswith("/") or ".." in path.split("/"):
        return None
    if "/-/blob/" in base:
        anchor = f"#L{start}" if start == end else f"#L{start}-{end}"
    else:
        anchor = f"#L{start}" if start == end else f"#L{start}-L{end}"
    return base + quote(path, safe="/") + anchor
