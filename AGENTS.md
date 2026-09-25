# Code Atlas development

- Maintain each `skills/<name>/` as a self-contained Agent Skill for Codex and Claude Code. Keep local references inside that skill folder; root `references/` is an authoring guide.
- Keep skill prompts evidence-based and scoped. Use diagrams only when they answer a real question. Preserve the BUSINESS / SYSTEM / CODE lenses where relevant, and mark unsupported business effects explicitly.
- The global catalog and immutable analysis history live in `code_atlas/`. Keep runtime dependencies in the Python standard library and never write into an analyzed repository merely to inspect it.
- Validate changes with `python3 scripts/check-skills.py` and `python3 -m unittest discover -s tests -v`. If the fixture generator changes, check `examples/sample-explanation.md` line references and run its generated tests.
- Follow the user's language in output; the skills and internal references are written in English, the README in Japanese.
