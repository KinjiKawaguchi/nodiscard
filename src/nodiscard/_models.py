"""Immutable data models used across the checker pipeline."""

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class NodiscardMethod:
    """A method marked with @nodiscard."""

    class_name: str
    method_name: str
    file_path: Path
    line: int
    is_inherited: bool


@dataclass(frozen=True)
class Violation:
    """A detected violation where a @nodiscard return value is discarded."""

    file_path: Path
    line: int
    col: int
    method_name: str
    receiver_type: str | None
    code: str
    message: str


@dataclass(frozen=True)
class CheckResult:
    """Aggregated result of a check run."""

    violations: tuple[Violation, ...]
    files_checked: int
    files_skipped: int
    skipped_reasons: tuple[tuple[Path, str], ...]


@dataclass(frozen=True)
class TypeInfo:
    """Result of simple type inference."""

    name: str
    module_path: Path | None


@dataclass(frozen=True)
class ImportedName:
    """A name resolved from an import statement."""

    local_name: str
    original_name: str
    module_path: str
    resolved_file: Path | None


@dataclass(frozen=True)
class ParsedFile:
    """A parsed Python source file with its AST and source lines."""

    file_path: Path
    tree: ast.Module
    source_lines: tuple[str, ...]
