# nodiscard — Test Cases (110 cases)

## D: デコレータ (9 cases)

| ID | テストケース | 期待結果 |
|----|------------|---------|
| D-1 | `@nodiscard` を付けた関数が正常に呼び出せる | 返却値が変わらない |
| D-2 | デコレータが `__name__`, `__doc__` を保持する | メタデータ維持 |
| D-3 | `@nodiscard` 付きメソッドの `__wrapped__` が元関数を指す | inspect互換 |
| D-4 | 通常メソッドに適用 | 動作する |
| D-5 | `async def` メソッドに適用 | 動作する |
| D-6 | `@classmethod` と併用 | 動作する |
| D-7 | `@staticmethod` と併用 | 動作する |
| D-8 | `@property` には適用しない | 明確なエラー |
| D-9 | `NoDiscard` マーカーが `Annotated` で使える | 有効 |

## B: 基本検出 — 違反ケース (7 cases)

| ID | コードパターン | 期待結果 |
|----|--------------|---------|
| B-1 | `obj.method()` — 返却値を捨てている | **検出** |
| B-2 | `self.method()` — クラス内でselfに対して | **検出** |
| B-3 | 1ファイルに複数違反 | **全て検出**、各行番号を正確に報告 |
| B-4 | `@nodiscard` のないメソッド `obj.other()` | 検出しない |
| B-5 | 違反ゼロのファイル | 報告なし |
| B-6 | `await obj.async_method()` — async返却値未使用 | **検出** |
| B-7 | `try: obj.method() except: ...` — try内のexpression statement | **検出** |

## U: 基本検出 — 正しい使用パターン (25 cases)

| ID | コードパターン | 期待結果 |
|----|--------------|---------|
| U-1 | `x = obj.method()` — 変数に代入 | OK |
| U-2 | `obj = obj.method()` — 同名変数に再代入 | OK |
| U-3 | `return obj.method()` — return 文 | OK |
| U-4 | `yield obj.method()` — yield 文 | OK |
| U-5 | `func(obj.method())` — 関数の引数として使用 | OK |
| U-6 | `if obj.method():` — 条件式 | OK |
| U-7 | `while obj.method():` — while条件 | OK |
| U-8 | `assert obj.method()` — assert文 | OK |
| U-9 | `[obj.method() for x in items]` — リスト内包表記の要素 | OK |
| U-10 | `x = obj.method() if cond else other` — 三項演算子 | OK |
| U-11 | `a, b = obj.method()` — タプルアンパック | OK |
| U-12 | `if (x := obj.method()):` — walrus operator | OK |
| U-13 | `obj.method().chained()` — メソッドチェーン | OK |
| U-14 | `await obj.async_method()` が代入されている | OK |
| U-15 | `_ = obj.method()` — 明示的な破棄 | OK |
| U-16 | `for x in obj.method():` — forループのイテラブル | OK |
| U-17 | `with obj.method() as x:` — context manager | OK |
| U-18 | `match obj.method():` — match文の対象 | OK |
| U-19 | `raise E() from obj.method()` — 例外チェーン | OK |
| U-20 | `x = a or obj.method()` — boolean演算の一部 | OK |
| U-21 | `x = [obj.method()]` — リストリテラルの要素 | OK |
| U-22 | `f"{obj.method()}"` — f-string内 | OK |
| U-23 | `d[key] = obj.method()` — 添字への代入 | OK |
| U-24 | `obj.method() + other` — 二項演算の一部（代入あり） | OK |
| U-25 | `not obj.method()` — 単項演算（代入あり） | OK |

## C: コレクター (13 cases)

| ID | テストケース | 期待結果 |
|----|------------|---------|
| C-1 | `@nodiscard` デコレータ付きメソッドを収集 | 収集される |
| C-2 | `@nodiscard` なしのメソッドは除外 | 除外される |
| C-3 | 複数クラスにまたがる収集 | 全クラス分を収集 |
| C-4 | `from nodiscard import nodiscard` 形式を認識 | 収集される |
| C-5 | `import nodiscard` → `@nodiscard.nodiscard` 形式を認識 | 収集される |
| C-6 | エイリアス `from nodiscard import nodiscard as nd` → `@nd` | 収集される |
| C-7 | `Annotated[Self, NoDiscard]` 返却型から収集 | 収集される |
| C-8 | `from __future__ import annotations` 下での文字列アノテーション | 収集される |
| C-9 | 継承: 親の `@nodiscard` が子でも有効 | 子でも検出対象 |
| C-10 | デコレータファクトリ `@nodiscard()` (括弧あり) | 収集される |
| C-11 | `@functools.cache` と `@nodiscard` の併用 | 収集される |
| C-12 | `@abstractmethod` + `@nodiscard` | 収集される |
| C-13 | `@overload` + `@nodiscard` | 実装メソッド側で検出 |

## T: 型推論 (14 cases)

| ID | コードパターン | 推論結果 |
|----|--------------|---------|
| T-1 | `x = Foo()` | `x: Foo` |
| T-2 | `x = Foo.create()` — classmethod返却型から | `x: Foo` |
| T-3 | `def f(x: Foo):` — パラメータ型アノテーション | `x: Foo` |
| T-4 | `x = x.method()` — 再代入（method returns Self） | `x: Foo` 維持 |
| T-5 | `x: Foo = get_something()` — 明示的型アノテーション | `x: Foo` |
| T-6 | `x = unknown_func()` — 型不明 | `Unknown`（スキップ） |
| T-7 | `if x is not None:` の分岐内 | 型維持 |
| T-8 | 関数スコープを超えない | スコープ外は追跡しない |
| T-9 | `self` の型をクラス定義から推論 | `self: OwnerClass` |
| T-10 | ループ内の再代入 | 型維持 |
| T-11 | `x = cast(Foo, something)` | `x: Foo` |
| T-12 | `isinstance(x, Foo)` 後のブロック内 | `x: Foo` |
| T-13 | `x: Foo | None` → `if x:` ブロック内 | `x: Foo` |
| T-14 | `super().method()` — super呼び出し | 親クラスの型で検出 |

## I: import 解決 (5 cases)

| ID | テストケース | 期待結果 |
|----|------------|---------|
| I-1 | `from pkg.mod import Foo` → 定義ファイル特定 | 正しいパス |
| I-2 | `from pkg import Foo` → `__init__.py` 経由 | 正しいパス |
| I-3 | 相対import `from .mod import Foo` | 正しいパス |
| I-4 | 存在しないモジュールの import | スキップ |
| I-5 | サードパーティの import | スキップ |

## X: クロスファイル + クラス階層 (8 cases)

| ID | テストケース | 期待結果 |
|----|------------|---------|
| X-1 | FileA で定義、FileB で違反呼び出し | **検出** |
| X-2 | FileA で定義、FileB で正しい呼び出し | OK |
| X-3 | `__init__.py` 経由の再export | **検出** |
| X-4 | 複数ディレクトリにまたがるプロジェクト | 全ファイル横断で検出 |
| X-5 | 親の `@nodiscard` を子がオーバーライド（デコレータなし） | **検出**（LSP） |
| X-6 | Mixin 経由で `@nodiscard` が伝播 | **検出** |
| X-7 | Protocol 定義上の `@nodiscard` | 実装クラスに伝播 |
| X-8 | 多重継承で MRO が関わるケース | 正しい解決順で判定 |

## E: エッジケース (18 cases)

| ID | コードパターン | 期待結果 |
|----|--------------|---------|
| E-1 | `@nodiscard` 付きだが返却型が `None` | 警告（矛盾） |
| E-2 | 空ファイル | エラーなし |
| E-3 | 構文エラーのあるファイル | スキップ + 警告 |
| E-4 | バイナリファイル | スキップ |
| E-5 | デコレータのネスト `@other @nodiscard` | 正しく認識 |
| E-6 | 同名メソッドが異なるクラス（片方だけ `@nodiscard`） | 型推論で区別 |
| E-7 | `exec()` / `eval()` 内の呼び出し | 検出しない |
| E-8 | 巨大ファイル（1000行超） | 正常動作 + 許容範囲の速度 |
| E-9 | `try: obj.method() except: ...` — try文内 | **検出** |
| E-10 | `# noqa: ND001` 的な抑制コメント | 将来サポート |
| E-11 | `obj.m1().m2()` — チェーン途中が `@nodiscard` | OK（使用されている） |
| E-12 | `obj.m1().m2()` — 最終が `@nodiscard`、全体が式文 | **検出** |
| E-13 | `lambda: obj.method()` — lambda本体 | OK |
| E-14 | `.pyi` スタブに `@nodiscard` がある場合 | スタブから収集 |
| E-15 | 循環 import が存在するプロジェクト | エラーなしで処理 |
| E-16 | symlink先のファイル | 重複検出しない |
| E-17 | `# nodiscard: ignore` インラインコメントで抑制 | 抑制される |
| E-18 | `_ = obj.method()` と `_result = obj.method()` | 両方OK |

## CLI (11 cases)

| ID | テストケース | 期待結果 |
|----|------------|---------|
| CLI-1 | 違反なしのディレクトリ | exit code 0 |
| CLI-2 | 違反ありのディレクトリ | exit code 1 |
| CLI-3 | ファイルパス指定 | 指定ファイルのみ |
| CLI-4 | ディレクトリパス指定 | 再帰的にチェック |
| CLI-5 | `--help` | ヘルプ表示 |
| CLI-6 | 出力フォーマット | `path:line:col: ND001 ...` |
| CLI-7 | `--exclude` で除外 | スキップ |
| CLI-8 | 存在しないパス | エラー + exit code 2 |
| CLI-9 | `--format json` | JSON出力 |
| CLI-10 | `--src` でソースルート指定 | import解決に使用 |
| CLI-11 | `pyproject.toml` の `[tool.nodiscard]` 読み込み | 設定反映 |

## テスト構造

```
tests/
├── conftest.py
├── test_decorator.py          # D-1〜D-9
├── test_detection_basic.py    # B-1〜B-7
├── test_detection_usage.py    # U-1〜U-25
├── test_collector.py          # C-1〜C-13
├── test_type_tracker.py       # T-1〜T-14
├── test_import_resolver.py    # I-1〜I-5
├── test_cross_file.py         # X-1〜X-8
├── test_edge_cases.py         # E-1〜E-18
├── test_cli.py                # CLI-1〜CLI-11
└── fixtures/
    ├── basic/
    ├── cross_file/
    │   ├── package_a/
    │   └── package_b/
    ├── type_inference/
    └── edge_cases/
```

### テスト作成の原則

- 1 テスト関数 = 1 シナリオ
- フィクスチャは実際の Python ソースファイルとして `tests/fixtures/` に配置
- テスト名は `test_<カテゴリID>_<説明>` 形式（例: `test_b1_discarded_return_detected`）
- カバレッジ目標: 95%+
