# Code Atlas

**コードを、人が検証できる地図にする。** Code Atlas は、既存プロジェクトや変更を根拠付きで説明する Agent Skills 集と、プロジェクト分類・解析履歴を一元管理するローカルCLIです。Claude Code と Codex の両方で使えます。

## できること

用途ごとに独立した6つのSkillがあります。

| Skill | 用途 |
| --- | --- |
| `understand-project` | リポジトリ全体の目的・入口・構造を把握する |
| `understand-change` | Git差分から今回の変更を説明する |
| `visualize-architecture` | コンポーネントと境界を図にする |
| `visualize-data-flow` | データの出所・変換・保存先を追う |
| `review-change` | 変更に起因する具体的な不具合を調べる |
| `explain-business` | コードの意味を利用者・運用の言葉に翻訳する |

説明では必要に応じて次の3レイヤーを使います。

| レイヤー | 読者が知りたいこと |
| --- | --- |
| BUSINESS | 利用者や運用の仕事はどう変わるか |
| SYSTEM | コンポーネント、データ、実行時の流れはどう変わるか |
| CODE | どの条件や処理が変更を実現するか |

図は説明に必要な場合だけ選びます。候補は Business Flow、Sequence、State、ER、Architecture/Component、Before/After です。小さな変更や図より文章が明快な変更には図を作りません。各主張と図の関係は差分または関連コードで裏付けます。

## 構成

```text
code-atlas/
├── skills/
│   ├── understand-project/
│   ├── understand-change/
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── code-reading.md
│   │       └── diagram-selection.md
│   ├── visualize-architecture/
│   ├── visualize-data-flow/
│   ├── review-change/
│   └── explain-business/
├── references/
│   ├── diagram-selection.md
│   ├── sequence.md
│   ├── er.md
│   ├── state.md
│   └── c4.md
├── code_atlas/                 # 分類・履歴CLI
├── bin/code-atlas              # 依存パッケージ不要の実行入口
├── tests/                      # CLIの振る舞いテスト
├── scripts/make-fixture.sh
└── examples/
    ├── fixture-walkthrough.md
    └── sample-explanation.md
```

`skills/<name>/` が単体の配布単位です。ルートの `references/` は設計ガイドであり、Skillが実行時に必要とする参照はSkillフォルダ内に収めています。

## 使い方

**個人利用ではSkillをグローバル管理**します。このリポジトリを開発元にし、CodexとClaude Codeの個人用Skillディレクトリから参照します。解析対象ごとにSkillを作り直す必要はありません。両ツールはSkillフォルダへのシンボリックリンクを読み込めます。

```bash
# 一度だけ設定する。/path/to/code-atlas は実際の保存先に置き換える
mkdir -p "$HOME/.agents/skills" "$HOME/.claude/skills"
for skill in /path/to/code-atlas/skills/*; do
  name=$(basename "$skill")
  ln -s "$skill" "$HOME/.agents/skills/$name"
  ln -s "$skill" "$HOME/.claude/skills/$name"
done
```

Codexの個人用配置先は `~/.agents/skills/`、Claude Codeは `~/.claude/skills/` です。Skillを更新すると、両ツールが同じ開発元を参照します。反映されない場合はセッションを再起動します。

**チームで共有する場合**は、必要なSkillだけを対象リポジトリへコピーしてコミットします。この場合は各プロジェクトで使う版を固定できます。

```bash
# Codex: 対象リポジトリのルートで
mkdir -p .agents/skills
cp -R /path/to/code-atlas/skills/understand-change .agents/skills/

# Claude Code: 対象リポジトリのルートで
mkdir -p .claude/skills
cp -R /path/to/code-atlas/skills/understand-change .claude/skills/
```

同名Skillを個人用とプロジェクト用の両方に置くと選択が紛らわしくなるため、同じ環境ではどちらを使うか決めてください。複数Skillを配布する場合はプラグイン化も可能です。

対象リポジトリで「`understand-change` を使い、今の変更を BUSINESS / SYSTEM / CODE で説明して」と依頼します。Claude Code では `/understand-change` でも呼び出せます。Codex では `$understand-change` を明示できます。コミットやブランチを指定したいときは依頼文に含めます。

```text
$understand-change 直近のコミットを説明して。必要なら図を選んでください。
$understand-change main との差分を、業務影響から説明してください。
```

`understand-change` の既定対象は作業ツリーの staged、unstaged、関連する untracked の変更です。作業ツリーが空なら直近コミットを対象として明示します。リポジトリ全体の説明には `understand-project` を使います。

## プロジェクト分類と履歴

個人のユーザー領域に**1つのSQLiteデータベース**を置き、各GitリポジトリにプロジェクトIDを割り当てます。同じリポジトリのworktreeは同一プロジェクトにまとまります。分類は自由な `kind` と複数のタグで管理します。解析レポートはプロジェクトID、Skill、対象範囲、コミット、日時とともに追記保存し、過去の記録を上書きしません。対象リポジトリには自動でファイルを書きません。

CLIはPython標準ライブラリだけで動きます。開発元リポジトリ内では `python3 -m code_atlas` を使えます。どのディレクトリからも `code-atlas` と呼びたい場合は、実行ファイルにリンクします（`~/.local/bin` をPATHに含めてください）。

```bash
mkdir -p "$HOME/.local/bin"
ln -s /path/to/code-atlas/bin/code-atlas "$HOME/.local/bin/code-atlas"
```

```bash
python3 -m code_atlas project add /path/to/repository --kind service --tag customer-a
python3 -m code_atlas project list --tag customer-a
python3 -m code_atlas history add --repo /path/to/repository \
  --skill understand-change --scope worktree --report /path/to/report.md
python3 -m code_atlas history list --project /path/to/repository
python3 -m code_atlas history show RUN_ID
python3 -m code_atlas project relocate PROJECT_ID /new/repository/path
```

レポートの履歴保存は明示的に行います。Skillへ「この説明をCode Atlasの履歴に保存して」と依頼しても構いません。`CODE_ATLAS_DATA_DIR` でデータベースの保存先を変更できます。未コミット変更の履歴には差分本体を保存せず、その時点の内容のハッシュを記録します。そのため後からコードが変わると同じ状態を完全には再現できません。共有したいレポートは `history export` で書き出せます。

## 設計思想

1. **差分から始める。** 変更前後を確定し、関連コードを必要な範囲だけ追います。実装が示していない業務効果やシステム間の通信は描きません。
2. **説明の問いから図を選ぶ。** 順序なら Sequence、状態遷移なら State、データ関係なら ER など、読者の疑問と証拠に合わせます。ひとつの巨大な図に詰め込みません。
3. **図なしを正しい選択肢にする。** 文章や小さな Before/After 表が十分なら、図は省きます。
4. **根拠と不確実性を残す。** 重要な説明にファイル位置を添え、コードで確認できない実行結果は推測として扱います。
5. **必要なコードだけ読む。** 先に差分の概要と変更シンボルを掴み、構造索引があれば関連する呼び出し経路を一度に取得します。Code Wiki は該当モジュールへの案内に使い、現在のコードで裏付けます。索引がない場合も検索範囲と読み取り範囲を段階的に広げます。

この考え方は [diagramming](https://github.com/arjunprabhulal/agent-skills/blob/main/skills/docs/diagramming/SKILL.md) の「問いに合う図」、[architecture-diagram-generator](https://github.com/imtiazrayhan/agentscamp-library/blob/main/skills/architecture-diagram-generator/SKILL.md) の「実コードから関係を確かめる」、[CodeGraph](https://github.com/colbymchenry/codegraph/blob/main/site/src/content/docs/reference/mcp-server.md) のシンボル単位の探索、[code-wiki](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/software-development/code-wiki/SKILL.md) の読み取り範囲の制御を参考にしています。Code Atlas はこれらを複製せず、**コードに根拠のある説明**と **BUSINESS / SYSTEM / CODE** に絞っています。構造索引やWikiがなくても動きます。

## 試す・検証する

追加の Python パッケージは不要です。次のスクリプトは一時的な Git リポジトリを作り、注文キャンセルの状態遷移を変更した差分を残します。

```bash
bash scripts/make-fixture.sh /tmp/code-atlas-demo
cd /tmp/code-atlas-demo
git diff
# このリポジトリ内で Skill を使い、変更を説明する
```

期待する観点と試用手順は [fixture walkthrough](examples/fixture-walkthrough.md)、出力例は [sample explanation](examples/sample-explanation.md) を参照してください。スクリプトは既存ディレクトリを上書きしません。

```bash
python3 scripts/check-skills.py
python3 -m unittest discover -s tests -v
```
