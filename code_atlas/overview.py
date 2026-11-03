"""Build a change overview from Git counts: stat tiles and charts that need no model judgment."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

from .git import FileChange

TOP_FILES = 8

_TEXT = {
    "ja": {
        "overview": "変更の概要", "files": "変更ファイル", "added": "追加行", "removed": "削除行",
        "breakdown": "追加 {A}・変更 {M}・削除 {D}", "binary": "バイナリ {n} 件は行数なし",
        "per_file": "ファイル別の変更行数", "others": "ほか {n} ファイル", "kinds": "変更行の内訳（パスから分類）",
        "code": "コード", "test": "テスト", "docs": "ドキュメント", "config": "設定・依存",
    },
    "en": {
        "overview": "Change overview", "files": "Files changed", "added": "Lines added", "removed": "Lines removed",
        "breakdown": "{A} added, {M} modified, {D} deleted", "binary": "{n} binary without line counts",
        "per_file": "Changed lines per file", "others": "{n} more files", "kinds": "Changed lines by kind (from paths)",
        "code": "Code", "test": "Tests", "docs": "Docs", "config": "Config & deps",
    },
}
_TEST_DIRS = {"test", "tests", "spec", "specs", "__tests__", "testing"}
_TEST_FILE = re.compile(r"(^test_.+|.+_test|.+\.(?:test|spec)|.+Tests?)\.\w+$")
_DOC_EXTENSIONS = {".md", ".mdx", ".rst", ".adoc", ".txt"}
_CONFIG_EXTENSIONS = {".json", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".conf", ".lock", ".xml", ".properties"}
_CONFIG_FILES = {"dockerfile", "makefile", "go.sum", "go.mod", "gemfile", ".gitignore", ".editorconfig", "procfile"}


def kind(path: str) -> str:
    """Classify a path as code, test, docs, or config by its name alone."""
    parts = PurePosixPath(path).parts
    name = parts[-1]
    if _TEST_DIRS & {part.lower() for part in parts[:-1]} or _TEST_FILE.match(name):
        return "test"
    suffix = PurePosixPath(name).suffix.lower()
    if suffix in _DOC_EXTENSIONS or parts[0].lower() in {"docs", "doc"}:
        return "docs"
    if suffix in _CONFIG_EXTENSIONS or name.lower() in _CONFIG_FILES or parts[0] == ".github":
        return "config"
    return "code"


def _fence(info: str, lines: list[str]) -> str:
    return "\n".join([f"```{info}", *lines, "```"])


def build(changes: list[FileChange], language: str = "en") -> str:
    """Return Markdown components summarizing the changes; charts appear only when they compare something."""
    if not changes:
        raise ValueError("No changes to summarize")
    words = _TEXT.get(language, _TEXT["en"])
    counted = [change for change in changes if change.added is not None]
    added = sum(change.added or 0 for change in counted)
    removed = sum(change.removed or 0 for change in counted)
    statuses = {status: sum(change.status == status for change in changes) for status in "AMD"}
    notes = [words["breakdown"].format(**statuses)]
    if len(counted) < len(changes):
        notes.append(words["binary"].format(n=len(changes) - len(counted)))
    blocks = [_fence(f"atlas-stats {words['overview']}", [
        f"{words['files']}: {len(changes)} | {' / '.join(notes)}",
        f"{words['added']}: +{added:,}",
        f"{words['removed']}: −{removed:,}",
    ])]

    ranked = sorted((change for change in counted if change.added or change.removed),
                    key=lambda change: (-(change.added + change.removed), change.path))
    if len(ranked) >= 2:
        rows = [f"`{change.path}`: +{change.added:,} −{change.removed:,}" for change in ranked[:TOP_FILES]]
        rest = ranked[TOP_FILES:]
        if rest:
            rows.append(f"{words['others'].format(n=len(rest))}: "
                        f"+{sum(c.added for c in rest):,} −{sum(c.removed for c in rest):,}")
        blocks.append(_fence(f"atlas-chart diff {words['per_file']}", rows))

    totals: dict[str, int] = {}
    for change in ranked:
        totals[kind(change.path)] = totals.get(kind(change.path), 0) + change.added + change.removed
    if len(totals) >= 2:
        order = ("code", "test", "docs", "config")
        blocks.append(_fence(f"atlas-chart share {words['kinds']}",
                             [f"{words[name]}: {totals[name]:,}" for name in order if name in totals]))
    return "\n\n".join(blocks) + "\n"
