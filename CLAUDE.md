# nodiscard — Project Instructions

Python 向け `@nodiscard` デコレータ + 静的チェッカー。
Rust の `#[must_use]` / C++ の `[[nodiscard]]` に相当する機能を Python に提供する。

**関連ドキュメント:**
- [docs/spec.md](docs/spec.md) — スコープ、フェーズ定義、受入条件、データモデル、設定スキーマ
- [docs/test-cases.md](docs/test-cases.md) — テストケース全量リスト (110 cases)

## Project Overview

`@nodiscard` でマークされたメソッドの返却値が破棄（代入されず式文として実行）されている箇所を静的解析で検出する CLI ツール。PyPI (`pip install nodiscard`) で公開。ライセンスは MIT。

### 想定ユースケース

- Pydantic frozen model の mutation メソッド（`model_copy` で新インスタンスを返すパターン）
- イミュータブルなドメインモデルのメソッドチェーン
- 関数型スタイルの API（元オブジェクトを変更せず新オブジェクトを返す）

## Architecture

### コンポーネント構成

```
src/nodiscard/
├── __init__.py             # Public API: @nodiscard, NoDiscard, __version__
├── _marker.py              # NoDiscard マーカー、デコレータ実装
├── checker.py              # 静的チェッカーのファサード
├── _collector.py           # @nodiscard メソッド収集（AST 解析）
├── _detector.py            # 違反検出（expression statement 解析）
├── _type_tracker.py        # 簡易型推論（ローカルスコープ）
├── _import_resolver.py     # import パス解決
└── cli.py                  # CLI エントリーポイント
```

### 設計原則

**インターフェースに依存する設計（Protocol ベース DI）**

各コンポーネントは `typing.Protocol` で依存先を定義し、具象実装を直接 import しない。

```python
# 良い例: Protocol に依存
class MethodCollector(Protocol):
    def collect(self, source: ast.Module, file_path: Path) -> list[NodiscardMethod]: ...

class Detector:
    def __init__(self, collector: MethodCollector) -> None: ...

# 悪い例: 具象クラスに直接依存
from nodiscard._collector import ASTMethodCollector
class Detector:
    def __init__(self) -> None:
        self.collector = ASTMethodCollector()  # テスト困難
```

**依存方向**

```
cli.py → checker.py → _detector.py → _collector.py
                     → _type_tracker.py
                     → _import_resolver.py
```

`_marker.py` は他のモジュールに依存しない（leaf module）。
`checker.py` がファサードとして各コンポーネントを組み立てる。

## Quality Rules

### Ruff — 全ルール適用、抑制を最小化

```toml
[tool.ruff.lint]
select = ["ALL"]
ignore = ["D1", "ANN101", "ANN102", "COM812", "ISC001"]
```

**原則: `# noqa` を書く前に設計を見直す。** ruff の警告はコードの設計・構造で解決する。`# noqa` は「ルールが文脈的に不適切」な場合のみ、理由コメント付きで使用。ignore への追加は PR で理由を明記する。

### ty / pyright — 厳格な型チェック

ty (Astral製) を優先。利用不可なら pyright strict で代替。

**型に関する原則:**
- 全 public 関数・メソッドに型アノテーション
- `Any` 禁止 — `object` または Protocol を使う
- `cast()` は最小限、理由をコメントで明記
- `type: ignore` 禁止 — 型エラーは設計で解決
- Union より Protocol / Overload を優先

## Coding Style

### 全般

- **イミュータビリティ優先**: `@dataclass(frozen=True)` / `NamedTuple` でデータを表現
- **1 ファイル 200〜400 行**、上限 800 行
- **1 関数 50 行以内**、ネスト 4 段以内。早期 return
- **副作用を最小化**し、純粋関数を優先

### 命名

- 意図を明確に表現。省略より可読性
- boolean は `is_`, `has_`, `should_`, `can_` で始める
- `_` prefix の private モジュールは内部実装。public API は `__init__.py` で re-export

### エラー処理

- 外部入力はシステム境界でバリデーション
- 内部コード間は Protocol の型で保証（余分なバリデーション不要）
- 構文エラーファイルはスキップ + 警告（全体を止めない）

### 依存管理

- ランタイム依存: **ゼロ**（標準ライブラリのみ）
- 開発依存: `pytest`, `pytest-cov`, `ruff`, `ty`/`pyright`, `pip-audit`

## Git Conventions

- Conventional Commits: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`
- コミットメッセージは目的（why）を簡潔に
- main への直接 push 禁止

## CI/CD

### CI (`.github/workflows/ci.yml`)

PR ごとに lint / typecheck / test / audit を並列実行。`all-checks-pass` をブランチ保護の required check にする。Python 3.11 + 3.12 + 3.13 + 3.14 マトリクステスト。開発は 3.14。

### CD (`.github/workflows/release.yml`)

Release Please + PyPI Trusted Publisher:
1. Conventional Commits → Release Please が CHANGELOG + バージョンバンプ PR 自動作成
2. Release PR マージ → GitHub Release + tag
3. `publish` ジョブが OIDC 認証で PyPI に自動公開

### Versioning Policy (SemVer)

v1.0.0 未満: `feat:` → minor, `fix:` → patch, breaking change は避ける
v1.0.0 以降: breaking change は `feat!:` で major バンプ

### pre-commit

ruff check/format + ty check をローカルでも実行。

## Development Commands

```bash
uv sync                                    # セットアップ
uv run ruff check src/ tests/ --fix        # lint
uv run ruff format src/ tests/             # format
uv run ty check src/                       # 型チェック
uv run pytest --cov=nodiscard              # テスト + カバレッジ
uv run pip-audit                           # セキュリティ監査
```

## Public API

```python
from nodiscard import nodiscard, NoDiscard

@nodiscard
def merge(self, other: Schema) -> Schema: ...

# または Annotated マーカー
from typing import Annotated
def merge(self, other: Schema) -> Annotated[Schema, NoDiscard]: ...
```

### CLI

```bash
nodiscard check src/                       # 基本
nodiscard check src/ --src src/            # import 解決用ルート
nodiscard check src/ --exclude "tests/*"   # 除外
nodiscard check src/ --format json         # JSON 出力
```

### 出力

```
src/app/usecase.py:42:5: ND001 Return value of '@nodiscard' method 'merge' is discarded
Found 1 error.
```
