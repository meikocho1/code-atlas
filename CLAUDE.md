# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 概要

Code Atlas は、コードや変更を BUSINESS / SYSTEM / CODE の視点で説明する6つの Agent Skills と、分類・解析履歴のローカルCLI。Skill は Markdown、CLI は Python 標準ライブラリで動く。

## コマンド

```bash
# 試用用の一時 Git リポジトリを作る（既存パスは拒否して exit 2。サンドボックス内では $TMPDIR 配下に作る）
bash scripts/make-fixture.sh "$TMPDIR/code-atlas-demo"

# fixture 側のテスト（fixture ディレクトリ内で実行。Python 標準ライブラリのみ）
python3 -m unittest -v
python3 -m unittest test_order.OrderCancellationTests.test_paid_order_needs_refund -v

# リポジトリルートで
python3 scripts/check-skills.py
python3 -m unittest discover -s tests -v
python3 -m code_atlas --help
```

Skill の動作確認は、fixture の `.claude/skills/`（Codex は `.agents/skills/`）へ該当Skillをコピーしてから依頼する。fixture は `.git/info/exclude` でこの2ディレクトリを除外しているため、導入した Skill は変更セットに混ざらない。このリポジトリ自体では `skills/` 配下の Skill は起動しない。

## 構造と制約

- **配布単位は `skills/<name>/`。** 利用者はフォルダごと対象リポジトリへコピーするので、各 Skill は単体で完結させる。`SKILL.md` からのリンクは Skill 内 `references/` への相対パスに限り、ルートの `references/` を参照しない。
- 6つのSkillが独立して起動する。役割を混ぜず、ほかのSkillへ案内する。
- 同じ `SKILL.md` を Claude Code と Codex の両方で使う。特定ホストのツールを前提にせず、使えない場合の手順も書く（例: `skills/understand-change/references/code-reading.md` の CodeGraph あり/なし分岐）。frontmatter の `description` が起動判定に使われる。
- **図の選択ルールは2箇所にある。** `understand-change` 用の正本は同Skill内の `references/diagram-selection.md`。ルートの `references/diagram-selection.md` はSkill横断の設計索引。ルール変更時は矛盾を確認する。
- **`examples/sample-explanation.md` は fixture の行番号に依存する**（`order.py:21-27`、`test_order.py:7-23`、`README.md:4` など）。`scripts/make-fixture.sh` の生成内容を変えたら、サンプル出力と `examples/fixture-walkthrough.md` の期待観点も合わせて直す。
- グローバル分類・履歴は `code_atlas/` のSQLite実装。利用者の保存先は `CODE_ATLAS_DATA_DIR` で差し替えられる。CLIのテストは一時ディレクトリを使い、実データへ書かない。

## Skill 本文を書くときの方針

- `SKILL.md`・`references/`・`examples/` は英語、`README.md` は日本語。
- Skill 間の責務を混ぜない。`understand-change` は変更説明、`review-change` は不具合発見、`understand-project` は全体把握。索引や Wiki の生成は前提にしない。
- 既存ガイドの原則に合わせる: 差分から始める / 主張と図のノード・エッジはすべて差分か関連コードで裏付ける / 図なしを正しい選択肢として扱う / 裏付けのない実行時の挙動は推測と明記する。
