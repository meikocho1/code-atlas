"""SQLite persistence for projects and immutable analysis runs."""

from __future__ import annotations

import os
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .git import Repo


def data_dir() -> Path:
    override = os.environ.get("CODE_ATLAS_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Code Atlas"
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", str(Path.home()))) / "Code Atlas"
    return Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))) / "code-atlas"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Store:
    def __init__(self, location: Path | None = None):
        folder = location or data_dir()
        folder.mkdir(parents=True, exist_ok=True)
        self.path = folder / "atlas.sqlite3"
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys=ON")
        self._create_schema()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "Store":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def _create_schema(self) -> None:
        version = self.connection.execute("PRAGMA user_version").fetchone()[0]
        if version > 1:
            raise ValueError(f"Database version {version} is newer than this Code Atlas release")
        with self.connection:
            self.connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    kind TEXT NOT NULL DEFAULT 'unspecified',
                    common_dir TEXT NOT NULL UNIQUE,
                    remote TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS project_paths (
                    root_path TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS project_tags (
                    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    tag TEXT NOT NULL,
                    PRIMARY KEY(project_id, tag)
                );
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    skill TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    base_ref TEXT,
                    head_sha TEXT,
                    worktree_hash TEXT,
                    report TEXT NOT NULL,
                    report_sha256 TEXT NOT NULL,
                    atlas_version TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS runs_project_time ON runs(project_id, created_at DESC);
                """
            )
            self.connection.execute("PRAGMA user_version=1")

    def register(self, repo: Repo, *, name: str | None = None, kind: str | None = None) -> sqlite3.Row:
        common_dir = str(repo.common_dir)
        root = str(repo.root)
        now = utc_now()
        with self.connection:
            existing = self.connection.execute(
                "SELECT * FROM projects WHERE common_dir=?", (common_dir,)
            ).fetchone()
            if existing is None:
                project_id = str(uuid.uuid4())
                self.connection.execute(
                    "INSERT INTO projects VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (project_id, name or repo.root.name, kind or "unspecified", common_dir, repo.remote, now, now),
                )
            else:
                project_id = existing["id"]
                self.connection.execute(
                    "UPDATE projects SET name=?, kind=?, remote=?, updated_at=? WHERE id=?",
                    (name or existing["name"], kind or existing["kind"], repo.remote or existing["remote"], now, project_id),
                )
            self.connection.execute(
                "INSERT INTO project_paths(root_path, project_id) VALUES (?, ?) "
                "ON CONFLICT(root_path) DO UPDATE SET project_id=excluded.project_id",
                (root, project_id),
            )
        return self.get_project(project_id)

    def get_project(self, identifier: str) -> sqlite3.Row:
        row = self.connection.execute(
            "SELECT * FROM projects WHERE id=? OR common_dir=?", (identifier, identifier)
        ).fetchone()
        if row is None:
            row = self.connection.execute(
                "SELECT p.* FROM projects p JOIN project_paths x ON x.project_id=p.id WHERE x.root_path=?",
                (str(Path(identifier).expanduser().resolve()),),
            ).fetchone()
        if row is None:
            raise ValueError(f"Unknown project: {identifier}")
        return row

    def relocate(self, project_id: str, repo: Repo) -> sqlite3.Row:
        self.get_project(project_id)
        owner = self.connection.execute(
            "SELECT id FROM projects WHERE common_dir=?", (str(repo.common_dir),)
        ).fetchone()
        if owner and owner["id"] != project_id:
            raise ValueError("New repository path is already registered to another project")
        path_owner = self.connection.execute(
            "SELECT project_id FROM project_paths WHERE root_path=?", (str(repo.root),)
        ).fetchone()
        if path_owner and path_owner["project_id"] != project_id:
            raise ValueError("New root path is already registered to another project")
        with self.connection:
            self.connection.execute(
                "UPDATE projects SET common_dir=?, remote=?, updated_at=? WHERE id=?",
                (str(repo.common_dir), repo.remote, utc_now(), project_id),
            )
            self.connection.execute(
                "INSERT OR IGNORE INTO project_paths(root_path, project_id) VALUES (?, ?)",
                (str(repo.root), project_id),
            )
            for old_path in self.paths(project_id):
                if old_path != str(repo.root) and not Path(old_path).exists():
                    self.connection.execute(
                        "DELETE FROM project_paths WHERE root_path=?", (old_path,)
                    )
        return self.get_project(project_id)

    def list_projects(self, *, kind: str | None = None, tag: str | None = None) -> list[sqlite3.Row]:
        query = "SELECT p.* FROM projects p"
        values: list[str] = []
        conditions = []
        if tag:
            query += " JOIN project_tags t ON t.project_id=p.id"
            conditions.append("t.tag=?")
            values.append(tag)
        if kind:
            conditions.append("p.kind=?")
            values.append(kind)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY p.name COLLATE NOCASE, p.id"
        return self.connection.execute(query, values).fetchall()

    def paths(self, project_id: str) -> list[str]:
        return [r[0] for r in self.connection.execute(
            "SELECT root_path FROM project_paths WHERE project_id=? ORDER BY root_path", (project_id,)
        )]

    def tags(self, project_id: str) -> list[str]:
        return [r[0] for r in self.connection.execute(
            "SELECT tag FROM project_tags WHERE project_id=? ORDER BY tag", (project_id,)
        )]

    def add_tag(self, project_id: str, tag: str) -> None:
        with self.connection:
            self.connection.execute("INSERT OR IGNORE INTO project_tags VALUES (?, ?)", (project_id, tag))

    def remove_tag(self, project_id: str, tag: str) -> None:
        with self.connection:
            self.connection.execute("DELETE FROM project_tags WHERE project_id=? AND tag=?", (project_id, tag))

    def set_kind(self, project_id: str, kind: str) -> None:
        with self.connection:
            self.connection.execute(
                "UPDATE projects SET kind=?, updated_at=? WHERE id=?", (kind, utc_now(), project_id)
            )

    def add_run(
        self, project_id: str, *, skill: str, scope: str, report: str,
        base_ref: str | None, head_sha: str | None, worktree_hash: str | None,
    ) -> sqlite3.Row:
        import hashlib

        run_id = str(uuid.uuid4())
        report_sha = hashlib.sha256(report.encode("utf-8")).hexdigest()
        with self.connection:
            self.connection.execute(
                "INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (run_id, project_id, skill, scope, base_ref, head_sha, worktree_hash,
                 report, report_sha, __version__, utc_now()),
            )
        return self.get_run(run_id)

    def get_run(self, run_id: str) -> sqlite3.Row:
        row = self.connection.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        if row is None:
            raise ValueError(f"Unknown run: {run_id}")
        return row

    def list_runs(self, *, project_id: str | None = None, skill: str | None = None) -> list[sqlite3.Row]:
        conditions = []
        values = []
        if project_id:
            conditions.append("project_id=?")
            values.append(project_id)
        if skill:
            conditions.append("skill=?")
            values.append(skill)
        query = "SELECT id, project_id, skill, scope, base_ref, head_sha, worktree_hash, report_sha256, atlas_version, created_at FROM runs"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY created_at DESC, id DESC"
        return self.connection.execute(query, values).fetchall()
