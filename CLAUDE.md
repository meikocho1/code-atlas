# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 概要

Code Atlas は、コードや変更を BUSINESS / SYSTEM / CODE の視点で説明する6つの Agent Skills と、プロジェクト分類・解析履歴のローカルCLI（`code_atlas/`）。Skill は Markdown、CLI は Python 3.9 以上の標準ライブラリだけで動く。Codex 向けの `AGENTS.md` と内容を揃える。

## コマンド

```bash
# リポジトリルートで
python3 scripts/check-skills.py                          # Skill の frontmatter とリンクを検証
python3 -m unittest discover -s tests -v                 # CLI のテスト
python3 -m unittest discover -s tests -k relocation -v   # テスト名の一部で絞り込む
python3 -m code_atlas --help                             # bin/code-atlas も同じ入口
# CI（.github/workflows/test.yml）は上の2つを Python 3.9 / 3.13、Ubuntu / macOS で実行する

# 評価シナリオ（eval/scenarios/）。build は既存パスを拒否して exit 2。サンドボックス内では $TMPDIR 配下に作る
python3 eval/harness.py list [--split train|val|test]
python3 eval/harness.py build schema "$TMPDIR/code-atlas-demo"   # = bash scripts/make-fixture.sh DIR schema
python3 eval/harness.py score schema "$TMPDIR/code-atlas-demo" report.md
python3 eval/harness.py run tiny --model sonnet                  # claude -p を実際に呼ぶ。トークンを消費する
```

Skill の動作確認は、fixture の `.claude/skills/`（Claude Code）か `.agents/skills/`（Codex・pi・OpenCode・Gemini CLI・Cursor）へ該当Skillをコピーしてから依頼する。fixture は `.git/info/exclude` でこの2ディレクトリを除外しているため、導入した Skill は変更セットに混ざらない。このリポジトリ自体では `skills/` 配下の Skill は起動しない。

## Skill（`skills/<name>/`）

- **配布単位。** 利用者はフォルダごと対象リポジトリや個人用Skillディレクトリへ置くので、各 Skill は単体で完結させる。`SKILL.md` からのリンクは Skill 内 `references/` への相対パスに限り、ルートの `references/` を参照しない。
- `scripts/check-skills.py` が検証する条件: 6つの Skill が揃っている（`EXPECTED` に列挙。追加・改名時は更新）、frontmatter は `name`（フォルダ名と一致、小文字・数字・ハイフンで64字以内）と `description`（1024字以内）だけ、相対リンクは Skill フォルダ内に解決する。形式が崩れた Skill を黙って読み飛ばすエージェント（pi など）があるため。
- 6つとも末尾に同じ2段落（報告前の `code-atlas check-refs` と、依頼時の `code-atlas history add ... --report -`）を持ち、違いは `--skill` だけ。CLI の引数を変えたら6つとも直す。`check-skills.py` が「Before delivering, if the `code-atlas` CLI is installed」以降の一致を検証する。
- 共通の末尾段落から `references/report-components.md`（`code-atlas render` が HTML コンポーネントに変える Markdown 記法）へリンクするため、6つの Skill が同一内容のコピーを持つ。`check-skills.py` が一致を検証するので、直すときは6つとも揃える。記法を変えたら `code_atlas/components.py` とテストも合わせる。
- 同じ `SKILL.md` を Agent Skills 標準に対応したエージェント（Claude Code・Codex・pi・OpenCode・Gemini CLI・Cursor）で使う。導入先は共通の `~/.agents/skills` と Claude Code 用の `~/.claude/skills` の2箇所（README の表を参照）。特定ホストの frontmatter やツールを前提にせず、使えない場合の手順も書く（例: `skills/understand-change/references/code-reading.md` の CodeGraph あり/なし分岐、`review-change` の `ocr` あり/なし分岐）。frontmatter の `description` が起動判定に使われる。
- **図の選択ルールは2箇所にある。** `understand-change` 用の正本は同Skill内の `references/diagram-selection.md`。ルートの `references/diagram-selection.md` はSkill横断の設計索引。ルール変更時は矛盾を確認する。
- 変更理由は差分から確定できないので、Skill はコミットメッセージ・PR本文・Issue・ユーザー提供の文脈を出典付きで使い、なければ「未確定」と書く。`schema` シナリオはこの挙動を試すため、理由をコミットメッセージにだけ書いている。

## 評価（`eval/`）

- シナリオは `eval/scenarios/<id>/` に1件ずつ置く。`base/` が最初のコミット、`change/` はその上に重ねる**ファイル全体**（差分ではない）、`scenario.json` が依頼文・`commit_message`（null なら未コミットのまま）・`expect`（`scope` / `visual` / `facts` / `forbidden` / `motivation`）と `split`（train / val / test）。`scripts/make-fixture.sh` は `harness.py build` の薄いラッパー。
- シナリオを足したら、模範解答を書いて `harness.py score` が `"hard": 1.0` になること、わざと誤った回答で下がることを確かめる。期待値が満たせないシナリオは学習を壊す。
- **`examples/sample-explanation.md` は `eval/scenarios/state/` のファイルの行番号に依存する**（`order.py:21-27`、`test_order.py:7-23`、`README.md:4` など）。`state` を変えたらサンプル出力と `examples/fixture-walkthrough.md` も直す。
- `harness.py run` は個人設定を読まない（`--setting-sources project,local`）で `claude -p` を呼び、Skill を `<name>-under-test` の名前で対象リポジトリの `.claude/skills/` に入れる。個人用に同名の Skill がリンクされていても、評価対象がすり替わらないようにするため。
- Skill は既定で HTML ファイルを渡すが、`run` は書き込みツールを許可せず Markdown を採点するので、依頼文の末尾に `OUTPUT_INSTRUCTION`（Markdown で返答し、ファイルを作らない）を足す。`visuals()` は `code-atlas render` 後の `<pre class="mermaid">` も数える。
- 採点は英語の正規表現（`MOTIVATION` など）なので、依頼文は英語回答を指定する。test 分割は Skill の改善（SkillOpt など）に使わず、最後の確認用に残す。

## CLI（`code_atlas/`）

- `git.py` は読み取り専用の git コマンドだけを使い、解析対象リポジトリへ書き込まない。すべての呼び出しに `-c core.fsmonitor=false` を付け、対象リポジトリの設定にあるコマンドを実行させない。作業ツリーの指紋は `git diff` の出力ではなく変更ファイルの中身から作る（diff の出力は `diff.noprefix` などの個人設定で変わるため）。
- プロジェクトの同一性は `git rev-parse --git-common-dir` の絶対パスで決まる。同じリポジトリの worktree は1プロジェクトにまとまり、リポジトリを移動したら `project relocate` で付け替える。
- `runs` は追記のみで、更新・削除のコマンドを持たない。スキーマを変えるときは `PRAGMA user_version`（現在 1。より新しい DB は拒否）を上げ、既存 DB の移行を `Store._create_schema` に書く。
- 保存先は `CODE_ATLAS_DATA_DIR` で差し替えられる。テストは一時ディレクトリを使い、実データへ書かない。
- `render`（`html_report.py`・`components.py`・`report.css`）は Markdown を正本のまま HTML に変える。コンポーネントは解釈できなければ通常のコードとして表示し、内容を落とさない。レポート由来の文字列はすべてエスケープし、生の HTML を通さない。チャートは JS なしの HTML/CSS で、値ラベルと表ビューを必ず付ける（ライトの一部系列色は背景とのコントラストが3:1未満のため）。
- `check-refs`（`refs.py`）は DB を開かない。参照の抽出は正規表現で、ドットかスラッシュを含む語だけをパスとみなす（`10:52` や URL は除外、本文中にそのまま書いた `example.com:443` は誤検出する。`path:1, 5` の `5` のような列挙の2つ目以降は拾わない。引用符なしの `app/[id]/page.tsx:3` のように記号を含むパスは、末尾だけを誤って照合しないよう拾わない。バッククォートで囲めば拾う）。リポジトリ外を指すパスは読まずに「見つからない」扱いにする。

## Skill 本文を書くときの方針

- `SKILL.md`・`references/`・`examples/` は英語、`README.md` は日本語。
- Skill 間の責務を混ぜない。`understand-change` は変更説明、`review-change` は不具合発見、`understand-project` は全体把握。索引や Wiki の生成は前提にしない。
- 既存ガイドの原則に合わせる: 差分から始める / 主張と図のノード・エッジはすべて差分か関連コードで裏付ける / 図なしを正しい選択肢として扱う / 裏付けのない実行時の挙動は推測と明記する。
