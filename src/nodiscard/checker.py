"""Facade that orchestrates the full check pipeline."""

from __future__ import annotations

import ast
import os
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path
from typing import TYPE_CHECKING

from nodiscard._collector import ASTMethodCollector
from nodiscard._detector import DetectionContext, ExpressionStatementDetector, _build_method_index
from nodiscard._models import CheckResult, NodiscardMethod, ParsedFile, Violation
from nodiscard._type_tracker import LocalTypeTracker

if TYPE_CHECKING:
    from collections.abc import Sequence


def check(
    paths: Sequence[Path],
    *,
    exclude: Sequence[str] = (),
) -> CheckResult:
    """Run the full nodiscard check on the given paths."""
    files = _collect_files(paths, exclude)

    collector = ASTMethodCollector()
    tracker = LocalTypeTracker()
    detector = ExpressionStatementDetector()

    all_methods: list[NodiscardMethod] = []
    parsed: dict[Path, ParsedFile] = {}
    skipped: list[tuple[Path, str]] = []

    for file_path in files:
        pf = _safe_parse(file_path, skipped)
        if pf is None:
            continue
        parsed[file_path] = pf
        all_methods.extend(collector.collect(pf.tree, file_path))

    all_methods = _resolve_inheritance(all_methods, parsed)
    all_class_methods = _collect_all_class_methods(parsed)
    global_method_index = _build_method_index(all_methods)

    all_violations: list[Violation] = []
    for file_path, pf in parsed.items():
        type_scope = tracker.infer_types(pf.tree, file_path)
        ctx = DetectionContext(
            tree=pf.tree,
            file_path=file_path,
            method_index=global_method_index,
            all_class_methods=all_class_methods,
            type_scope=type_scope,
            source_lines=pf.source_lines,
        )
        all_violations.extend(detector.detect(ctx))

    all_violations.sort(key=lambda v: (str(v.file_path), v.line, v.col))

    return CheckResult(
        violations=tuple(all_violations),
        files_checked=len(parsed),
        files_skipped=len(skipped),
        skipped_reasons=tuple(skipped),
    )


def _collect_files(
    paths: Sequence[Path],
    exclude: Sequence[str],
) -> list[Path]:
    """Collect all .py and .pyi files from the given paths."""
    files: list[Path] = []
    seen: set[Path] = set()

    for path in paths:
        resolved = path.resolve()
        if resolved.is_file():
            real = _safe_realpath(resolved)
            if real not in seen and _is_python_file(resolved):
                seen.add(real)
                files.append(resolved)
        elif resolved.is_dir():
            for root, _, filenames in os.walk(resolved):
                for name in filenames:
                    fp = Path(root) / name
                    if not _is_python_file(fp):
                        continue
                    real = _safe_realpath(fp)
                    if real in seen:
                        continue
                    if _is_excluded(fp, resolved, exclude):
                        continue
                    seen.add(real)
                    files.append(fp)
    return sorted(files)


def _is_python_file(path: Path) -> bool:
    return path.suffix in {".py", ".pyi"}


def _is_excluded(path: Path, base: Path, patterns: Sequence[str]) -> bool:
    try:
        rel = str(path.relative_to(base))
    except ValueError:
        rel = str(path)
    return any(fnmatch(rel, pat) for pat in patterns)


def _safe_realpath(path: Path) -> Path:
    """Resolve symlinks to prevent duplicate processing."""
    try:
        return path.resolve(strict=True)
    except OSError:
        return path.resolve()


def _safe_parse(
    file_path: Path,
    skipped: list[tuple[Path, str]],
) -> ParsedFile | None:
    """Parse a Python file, skipping binary/syntax-error files."""
    try:
        source = file_path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as e:
        skipped.append((file_path, f"Cannot read: {e}"))
        return None

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError as e:
        skipped.append((file_path, f"Syntax error: {e}"))
        return None

    return ParsedFile(
        file_path=file_path,
        tree=tree,
        source_lines=tuple(source.splitlines()),
    )


def _collect_all_class_methods(parsed: dict[Path, ParsedFile]) -> dict[str, set[str]]:
    """Build class_name -> {all method names} for every class in parsed files."""
    result: dict[str, set[str]] = {}
    for pf in parsed.values():
        for node in ast.walk(pf.tree):
            if isinstance(node, ast.ClassDef):
                methods: set[str] = set()
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods.add(item.name)
                result.setdefault(node.name, set()).update(methods)
    return result


@dataclass
class _InheritanceContext:
    """State for propagating @nodiscard across the class hierarchy."""

    nodiscard_by_class: dict[str, set[str]]
    class_bases: dict[str, list[str]]
    class_locations: dict[str, tuple[Path, int]]
    result: list[NodiscardMethod]
    visited: set[str] = field(default_factory=set)


def _resolve_inheritance(
    methods: list[NodiscardMethod],
    parsed: dict[Path, ParsedFile],
) -> list[NodiscardMethod]:
    """Propagate @nodiscard from parent classes to subclasses."""
    nodiscard_by_class: dict[str, set[str]] = {}
    for m in methods:
        nodiscard_by_class.setdefault(m.class_name, set()).add(m.method_name)

    class_bases: dict[str, list[str]] = {}
    class_locations: dict[str, tuple[Path, int]] = {}

    for file_path, pf in parsed.items():
        for node in ast.walk(pf.tree):
            if isinstance(node, ast.ClassDef):
                bases = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        bases.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        bases.append(base.attr)
                class_bases[node.name] = bases
                class_locations[node.name] = (file_path, node.lineno)

    ctx = _InheritanceContext(
        nodiscard_by_class=nodiscard_by_class,
        class_bases=class_bases,
        class_locations=class_locations,
        result=list(methods),
    )

    for class_name, bases in class_bases.items():
        _propagate(class_name, bases, ctx)

    return ctx.result


def _propagate(
    class_name: str,
    bases: list[str],
    ctx: _InheritanceContext,
) -> None:
    if class_name in ctx.visited:
        return
    ctx.visited.add(class_name)

    own_methods = ctx.nodiscard_by_class.get(class_name, set())
    location = ctx.class_locations.get(class_name)

    for base_name in bases:
        if base_name in ctx.class_bases:
            _propagate(base_name, ctx.class_bases[base_name], ctx)

        parent_methods = ctx.nodiscard_by_class.get(base_name, set())
        for method_name in parent_methods:
            if method_name not in own_methods and location is not None:
                file_path, line = location
                ctx.result.append(
                    NodiscardMethod(
                        class_name=class_name,
                        method_name=method_name,
                        file_path=file_path,
                        line=line,
                        is_inherited=True,
                    ),
                )
                own_methods.add(method_name)

    ctx.nodiscard_by_class[class_name] = own_methods
