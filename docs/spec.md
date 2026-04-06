# nodiscard — Specification

## Scope

### やること

- `@nodiscard` デコレータ / `Annotated[T, NoDiscard]` マーカーの提供
- 静的チェッカー CLI (`nodiscard check`)
- `@nodiscard` メソッドの AST 収集
- 返却値未使用の検出（expression statement 解析）
- ローカルスコープの簡易型推論（レシーバー型の特定）
- import 解決（クロスファイル解析）
- `pyproject.toml` の `[tool.nodiscard]` 設定サポート
- pre-commit hook としての使用

### やらないこと

- ランタイムでの未使用検出（`__del__` ベース等）
- mypy / pyright plugin 統合（将来の拡張候補）
- ruff plugin（Rust 実装が必要、将来の拡張候補）
- IDE 統合（LSP サーバー等）
- フル型推論（mypy / pyright 相当の型解析）
- `async` 固有の特殊解析（`asyncio.create_task` の追跡等）
- メソッド以外の関数呼び出し検出（v0.1 スコープ外）

## Definition of Done (v0.1.0)

全機能を v0.1.0 で一括リリースする。

**受入条件:**
- [ ] D-1〜D-9（デコレータ）全通過
- [ ] B-1〜B-7（違反検出）全通過
- [ ] U-1〜U-25（正しい使用パターン）全通過
- [ ] C-1〜C-13（コレクター）全通過
- [ ] T-1〜T-14（型推論）全通過
- [ ] I-1〜I-5（import解決）全通過
- [ ] X-1〜X-8（クロスファイル + クラス階層）全通過
- [ ] E-1〜E-18（エッジケース）全通過
- [ ] CLI-1〜CLI-11（CLI）全通過
- [ ] `pip install nodiscard` でインストール可能
- [ ] CI 全パス（lint, typecheck, test, audit）
- [ ] カバレッジ 95% 以上
- [ ] README.md 完成

## Non-Functional Requirements

### 性能

- 10,000 行: 1 秒以内
- 100,000 行: 10 秒以内
- メモリ: ファイルサイズの 10 倍以内

### 互換性

- Python: 3.11+
- OS: Linux, macOS, Windows
- パッケージマネージャ: pip, uv, pipx

### 安定性

- 構文エラーファイルでクラッシュしない
- 循環 import で無限ループしない（深さ制限）
- バイナリファイルを安全にスキップ

## Data Model

```python
@dataclass(frozen=True)
class NodiscardMethod:
    """@nodiscard でマークされたメソッドの情報"""
    class_name: str
    method_name: str
    file_path: Path
    line: int
    is_inherited: bool

@dataclass(frozen=True)
class Violation:
    """検出された違反"""
    file_path: Path
    line: int
    col: int
    method_name: str
    receiver_type: str | None
    code: str                  # "ND001"
    message: str

@dataclass(frozen=True)
class CheckResult:
    """チェック結果"""
    violations: tuple[Violation, ...]
    files_checked: int
    files_skipped: int
    skipped_reasons: tuple[tuple[Path, str], ...]

@dataclass(frozen=True)
class TypeInfo:
    """簡易型推論の結果"""
    name: str
    module_path: Path | None

@dataclass(frozen=True)
class ImportedName:
    """import 文から解決された名前"""
    local_name: str
    original_name: str
    module_path: str
    resolved_file: Path | None
```

## Error Code System

| コード | 名前 | 説明 |
|--------|------|------|
| ND001 | discarded-nodiscard-return | `@nodiscard` メソッドの返却値が破棄されている |
| ND002 | nodiscard-on-none-return | `@nodiscard` が `None` 返却メソッドに付与（将来） |

番号体系: ND0xx 返却値未使用系 / ND1xx デコレータ誤用系 / ND9xx 内部エラー系

## Configuration Schema

### pyproject.toml

```toml
[tool.nodiscard]
src = ["src"]                    # import 解決のソースルート
exclude = ["tests/*"]            # 除外パターン（glob）
format = "text"                  # "text" | "json"
```

### CLI 引数と設定ファイルの対応

| CLI | pyproject.toml | デフォルト |
|-----|---------------|-----------|
| `<paths>` | `src` | `.` |
| `--src` | — | — |
| `--exclude` | `exclude` | `[]` |
| `--format` | `format` | `text` |
| `--config` | — | `pyproject.toml` |

CLI 引数は設定ファイルより優先。

## Output Formats

**text (デフォルト):**
```
src/app/usecase.py:42:5: ND001 Return value of '@nodiscard' method 'merge' is discarded
Found 2 errors.
```

**json:**
```json
{
  "violations": [
    {
      "file": "src/app/usecase.py",
      "line": 42,
      "col": 5,
      "code": "ND001",
      "method": "merge",
      "receiver_type": "LearnerSchema",
      "message": "Return value of '@nodiscard' method 'merge' is discarded"
    }
  ],
  "summary": { "files_checked": 15, "files_skipped": 0, "violations": 2 }
}
```

## pyproject.toml 完全版

```toml
[project]
name = "nodiscard"
version = "0.0.0"
description = "A @nodiscard decorator and static checker for Python — detect when return values of marked methods are silently discarded"
readme = "README.md"
license = "MIT"
requires-python = ">=3.11"
authors = [{ name = "KinjiKawaguchi" }]
keywords = ["linter", "static-analysis", "must-use", "nodiscard", "type-safety"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: 3.14",
    "Topic :: Software Development :: Quality Assurance",
    "Typing :: Typed",
]
dependencies = []

[project.urls]
Homepage = "https://github.com/KinjiKawaguchi/nodiscard"
Repository = "https://github.com/KinjiKawaguchi/nodiscard"
Issues = "https://github.com/KinjiKawaguchi/nodiscard/issues"

[project.scripts]
nodiscard = "nodiscard.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/nodiscard"]

[dependency-groups]
dev = ["pytest>=8.0", "pytest-cov>=6.0", "ruff>=0.12", "pip-audit>=2.0"]
```

## README.md 構成仕様

1. バッジ行: PyPI version, Python versions, CI status, License
2. 1行説明
3. Problem: frozen model の return Self で代入忘れが silent no-op になる問題
4. Quick Start: インストール + 最小例（5行以内）
5. Usage: デコレータ + CLI
6. Configuration: pyproject.toml 設定例
7. Rules: ND001 の説明
8. pre-commit: hook 設定例
9. Comparison: Rust `#[must_use]`, C++ `[[nodiscard]]` との比較表
10. Limitations: 現在の制約
11. Contributing: 開発環境セットアップ
12. License: MIT
