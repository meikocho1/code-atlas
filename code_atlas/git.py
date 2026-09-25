"""Read-only Git identity and worktree fingerprinting."""

from __future__ import annotations

import hashlib
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


class GitError(ValueError):
    pass


def _git(path: Path, *args: str, check: bool = True) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(path), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise GitError(message or f"git {' '.join(args)} failed")
    return result.stdout if result.returncode == 0 else b""


@dataclass(frozen=True)
class Repo:
    root: Path
    common_dir: Path
    remote: str | None
    head: str | None


def inspect_repo(path: str | Path) -> Repo:
    location = Path(path).expanduser().resolve()
    if not location.is_dir():
        raise GitError(f"Repository path is not a directory: {location}")
    root = Path(os.fsdecode(_git(location, "rev-parse", "--show-toplevel")).strip()).resolve()
    common_text = os.fsdecode(_git(root, "rev-parse", "--git-common-dir")).strip()
    common_dir = Path(common_text)
    if not common_dir.is_absolute():
        common_dir = root / common_dir
    remote = _git(location, "config", "--get", "remote.origin.url", check=False).decode(
        "utf-8", errors="replace"
    ).strip() or None
    head = _git(location, "rev-parse", "--verify", "HEAD", check=False).decode().strip() or None
    return Repo(root=root, common_dir=common_dir.resolve(), remote=remote, head=head)


def resolve_ref(repo: Repo, ref: str) -> str:
    if not ref or ref.startswith("-"):
        raise GitError(f"Invalid Git ref: {ref!r}")
    return _git(repo.root, "rev-parse", "--verify", f"{ref}^{{commit}}").decode().strip()


def read_file(repo: Repo, path: str, rev: str | None = None) -> bytes | None:
    """Read a repository file from the working tree or a resolved commit; None if absent or outside."""
    target = Path(os.path.normpath(repo.root / path))
    if not target.is_relative_to(repo.root):
        return None
    if rev is None:
        # Resolve symlinks too, so a link inside the repository cannot expose a file outside it.
        real = target.resolve()
        return real.read_bytes() if real.is_relative_to(repo.root) and real.is_file() else None
    try:
        return _git(repo.root, "cat-file", "blob", f"{rev}:{target.relative_to(repo.root).as_posix()}")
    except GitError:
        return None


def worktree_fingerprint(repo: Repo) -> str | None:
    """Hash tracked changes and untracked file contents without storing their code."""
    status = _git(repo.root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    if not status:
        return None
    digest = hashlib.sha256()
    digest.update(b"code-atlas-worktree-v1\0")
    if repo.head:
        digest.update(_git(repo.root, "diff", "--binary", "HEAD", "--"))
    else:
        digest.update(_git(repo.root, "diff", "--binary", "--cached", "--"))
        digest.update(_git(repo.root, "diff", "--binary", "--"))
    names = _git(repo.root, "ls-files", "--others", "--exclude-standard", "-z").split(b"\0")
    for raw_name in sorted(name for name in names if name):
        digest.update(b"\0path\0")
        digest.update(raw_name)
        file_path = repo.root / os.fsdecode(raw_name)
        if file_path.is_symlink():
            digest.update(b"\0symlink\0")
            digest.update(os.fsencode(os.readlink(file_path)))
        elif file_path.is_file():
            digest.update(b"\0file\0")
            with file_path.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
    return digest.hexdigest()
