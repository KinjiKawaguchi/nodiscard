[![PyPI version](https://img.shields.io/pypi/v/nodiscard)](https://pypi.org/project/nodiscard/)
[![Python versions](https://img.shields.io/pypi/pyversions/nodiscard)](https://pypi.org/project/nodiscard/)
[![CI](https://github.com/KinjiKawaguchi/nodiscard/actions/workflows/ci.yml/badge.svg)](https://github.com/KinjiKawaguchi/nodiscard/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# nodiscard

A `@nodiscard` decorator and static checker for Python — like Rust's `#[must_use]` or C++'s `[[nodiscard]]`.

## Problem

Frozen/immutable models return new instances from mutation methods. Forgetting to capture the return value is a silent no-op:

```python
user = User(name="Alice")
user.rename("Bob")   # Bug! Returns a new User, but the result is silently discarded.
print(user.name)     # Still "Alice"
```

## Quick Start

```bash
pip install nodiscard
```

```python
from nodiscard import nodiscard

class User:
    @nodiscard
    def rename(self, name: str) -> "User":
        return User(name=name)
```

```bash
nodiscard check src/
# src/app.py:42:5: ND001 Return value of '@nodiscard' method 'rename' is discarded
```

## Usage

### Decorator

```python
from nodiscard import nodiscard, NoDiscard
from typing import Annotated

class Schema:
    @nodiscard
    def merge(self, other: "Schema") -> "Schema": ...

    # Alternative: Annotated marker
    def replace(self, **kwargs: object) -> Annotated["Schema", NoDiscard]: ...
```

Works with `@classmethod`, `@staticmethod`, `@abstractmethod`, `async def`, and decorator stacking.

### CLI

```bash
nodiscard check src/                       # Check a directory
nodiscard check src/models.py              # Check a single file
nodiscard check src/ --src src/            # Set import resolution root
nodiscard check src/ --exclude "tests/*"   # Exclude patterns
nodiscard check src/ --format json         # JSON output
```

**Exit codes:** `0` = no violations, `1` = violations found, `2` = error (e.g. path not found).

## Configuration

```toml
# pyproject.toml
[tool.nodiscard]
src = ["src"]
exclude = ["tests/*", "migrations/*"]
format = "text"  # "text" or "json"
```

CLI arguments override `pyproject.toml` settings.

## Rules

| Code | Name | Description |
|------|------|-------------|
| ND001 | discarded-nodiscard-return | Return value of a `@nodiscard` method is discarded |

### Inline suppression

```python
obj.method()  # nodiscard: ignore
```

## pre-commit

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/KinjiKawaguchi/nodiscard
    rev: v0.1.0
    hooks:
      - id: nodiscard
        args: [check, src/]
```

## Comparison

| Feature | Rust `#[must_use]` | C++ `[[nodiscard]]` | Python `@nodiscard` |
|---------|-------------------|--------------------|--------------------|
| Compile-time | Yes | Yes | Static analysis |
| Functions | Yes | Yes | Methods (v0.1) |
| Custom message | Yes | C++20 | `@nodiscard(reason="...")` |
| Suppressible | `let _ = ...` | `(void)expr` | `_ = expr` / `# nodiscard: ignore` |

## Limitations

- v0.1 detects method calls only (not bare function calls)
- Type inference is local-scope only (no full type resolution like mypy/pyright)
- No IDE integration yet (LSP planned for future)
- `async` task tracking (`asyncio.create_task`) is not analyzed

## Contributing

- [DeepWiki](https://deepwiki.com/KinjiKawaguchi/nodiscard) — AI-generated codebase documentation

```bash
git clone https://github.com/KinjiKawaguchi/nodiscard.git
cd nodiscard
uv sync
uv run pytest --cov=nodiscard
uv run ruff check src/ tests/
```

## License

MIT
