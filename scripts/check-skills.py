#!/usr/bin/env python3
"""Check distributable Skill metadata and local reference links."""

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
EXPECTED = {
    "understand-project", "understand-change", "visualize-architecture",
    "visualize-data-flow", "review-change", "explain-business",
}


def main() -> int:
    errors = []
    found = {path.parent.name for path in SKILLS.glob("*/SKILL.md")}
    if found != EXPECTED:
        errors.append(f"Expected {sorted(EXPECTED)}, found {sorted(found)}")
    for skill_file in SKILLS.glob("*/SKILL.md"):
        content = skill_file.read_text(encoding="utf-8")
        match = re.match(r"\A---\n(.*?)\n---\n", content, re.DOTALL)
        if not match:
            errors.append(f"{skill_file}: missing frontmatter")
            continue
        metadata = {}
        for line in match.group(1).splitlines():
            if ":" not in line:
                errors.append(f"{skill_file}: malformed frontmatter line")
                continue
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip()
        if metadata.get("name") != skill_file.parent.name:
            errors.append(f"{skill_file}: name must match folder")
        if not metadata.get("description") or len(metadata["description"]) > 1024:
            errors.append(f"{skill_file}: missing or long description")
        if set(metadata) != {"name", "description"}:
            errors.append(f"{skill_file}: unexpected frontmatter keys")
        if "[TODO:" in content:
            errors.append(f"{skill_file}: unfinished TODO")
        for link in re.findall(r"\[[^]]+\]\(([^)]+)\)", content):
            if "://" in link or link.startswith("#"):
                continue
            target = (skill_file.parent / link.split("#", 1)[0]).resolve()
            if not target.exists() or not target.is_relative_to(skill_file.parent.resolve()):
                errors.append(f"{skill_file}: nonportable reference {link}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Validated {len(found)} standalone skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
