"""Facade that orchestrates the full check pipeline."""

from __future__ import annotations

import ast
import logging
import os
from fnmatch import fnmatch
from pathlib import Path
from typing import TYPE_CHECKING

from nodiscard._collector import ASTMethodCollector
from nodiscard._detector import ExpressionStatementDetector
from nodiscard._import_resolver import FileSystemImportResolver
from nodiscard._models import CheckResult, NodiscardMethod, Violation
from nodiscard._type_tracker import LocalTypeTracker

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)

_MAX_IMPORT_DEPTH = 20


def check(
    paths: Sequence[Path],
    *,
    src_roots: Sequence[Path] | None = None,
    exclude: Sequence[str] = (),
) -> CheckResult:
    """Run the full nodiscard check on the given paths."""
    effective_src = list(src_roots) if src_roots else _infer_src_roots(paths)
    files = _collect_files(paths, exclude)

    collector = ASTMethodCollector()
    tracker = LocalTypeTracker()
    detector = ExpressionStatementDetector()
    resolver = FileSystemImportResolver(effective_src)

    all_methods: list[NodiscardMethod] = []
    parsed_trees: dict[Path, ast.Module] = {}
    skipped: list[tuple[Path, str]] = []

    # Phase 1: parse all files and collect @nodiscard methods
    for file_path in files:
        tree = _safe_parse(file_path, skipped)
        if tree is None:
            continue
        parsed_trees[file_path] = tree
        all_methods.extend(collector.collect(tree, file_path))

    # Phase 1.5: resolve cross-file inheritance
    all_methods = _resolve_inheritance(all_methods, parsed_trees, collector, resolver)

    # Phase 2: detect violations in each file
    all_violations: list[Violation] = []
    for file_path, tree in parsed_trees.items():
        # Merge methods from all files + imported modules
        relevant_methods = _gather_relevant_methods(
            tree, file_path, all_methods, resolver,
        )
        type_scope = tracker.infer_types(tree, file_path)
        all_violations.extend(
            detector.detect(tree, file_path, relevant_methods, type_scope),
        )

    all_violations.sort(key=lambda v: (str(v.file_path), v.line, v.col))

    return CheckResult(
        violations=tuple(all_violations),
        files_checked=len(parsed_trees),
        files_skipped=len(skipped),
        skipped_reasons=tuple(skipped),
    )


def _infer_src_roots(paths: Sequence[Path]) -> list[Path]:
    """Infer source roots from the given paths."""
    roots: list[Path] = []
    for p in paths:
        resolved = p.resolve()
        if resolved.is_dir():
            roots.append(resolved)
        elif resolved.is_file():
            roots.append(resolved.parent)
    return roots if roots else [Path.cwd()]


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
            for root, _dirs, filenames in os.walk(resolved):
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
) -> ast.Module | None:
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

    # Attach source lines for inline suppress comments
    tree._source_lines = source.splitlines()  # type: ignore[attr-defined]  # noqa: SLF001
    return tree


def _gather_relevant_methods(
    tree: ast.Module,
    file_path: Path,
    all_methods: list[NodiscardMethod],
    resolver: FileSystemImportResolver,
) -> list[NodiscardMethod]:
    """Gather @nodiscard methods relevant to this file (local + imported)."""
    resolved_file = file_path.resolve()
    local = [m for m in all_methods if m.file_path.resolve() == resolved_file]

    imports = resolver.resolve_imports(tree, file_path)
    imported_files = {imp.resolved_file for imp in imports if imp.resolved_file}

    cross_file = [
        m for m in all_methods
        if m.file_path.resolve() in {f.resolve() for f in imported_files}
    ]

    return local + cross_file


def _resolve_inheritance(
    methods: list[NodiscardMethod],
    parsed_trees: dict[Path, ast.Module],
    collector: ASTMethodCollector,
    resolver: FileSystemImportResolver,
) -> list[NodiscardMethod]:
    """Propagate @nodiscard from parent classes to subclasses."""
    nodiscard_by_class: dict[str, set[str]] = {}
    for m in methods:
        nodiscard_by_class.setdefault(m.class_name, set()).add(m.method_name)

    class_bases: dict[str, list[str]] = {}
    class_locations: dict[str, tuple[Path, int]] = {}

    for file_path, tree in parsed_trees.items():
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        bases.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        bases.append(base.attr)
                class_bases[node.name] = bases
                class_locations[node.name] = (file_path, node.lineno)

    inherited: list[NodiscardMethod] = list(methods)
    visited: set[str] = set()

    for class_name, bases in class_bases.items():
        _propagate(
            class_name, bases, nodiscard_by_class, class_bases,
            class_locations, inherited, visited,
        )

    return inherited


def _propagate(
    class_name: str,
    bases: list[str],
    nodiscard_by_class: dict[str, set[str]],
    class_bases: dict[str, list[str]],
    class_locations: dict[str, tuple[Path, int]],
    result: list[NodiscardMethod],
    visited: set[str],
) -> None:
    if class_name in visited:
        return
    visited.add(class_name)

    own_methods = nodiscard_by_class.get(class_name, set())
    location = class_locations.get(class_name)

    for base_name in bases:
        # Recurse into base first
        if base_name in class_bases:
            _propagate(
                base_name, class_bases[base_name], nodiscard_by_class,
                class_bases, class_locations, result, visited,
            )

        parent_methods = nodiscard_by_class.get(base_name, set())
        for method_name in parent_methods:
            if method_name not in own_methods and location is not None:
                file_path, line = location
                inherited_method = NodiscardMethod(
                    class_name=class_name,
                    method_name=method_name,
                    file_path=file_path,
                    line=line,
                    is_inherited=True,
                )
                result.append(inherited_method)
                own_methods.add(method_name)

    nodiscard_by_class[class_name] = own_methods
