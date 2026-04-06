"""Collect methods marked with @nodiscard from AST trees."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Protocol

from nodiscard._models import NodiscardMethod

# Decorator names recognised as nodiscard markers.
_NODISCARD_NAMES = frozenset({"nodiscard"})
_NODISCARD_QUALNAMES = frozenset({"nodiscard.nodiscard"})
_NODISC_MARKER = "NoDiscard"


class MethodCollector(Protocol):
    """Protocol for collecting @nodiscard methods."""

    def collect(
        self,
        tree: ast.Module,
        file_path: Path,
    ) -> list[NodiscardMethod]: ...


class ASTMethodCollector:
    """Collect @nodiscard methods via AST inspection."""

    def collect(
        self,
        tree: ast.Module,
        file_path: Path,
    ) -> list[NodiscardMethod]:
        """Return all @nodiscard-marked methods in *tree*."""
        aliases = _resolve_decorator_aliases(tree)
        class_bases = _collect_class_bases(tree)
        methods: list[NodiscardMethod] = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            methods.extend(
                self._collect_from_class(node, file_path, aliases, class_bases),
            )
        return methods

    def _collect_from_class(
        self,
        cls: ast.ClassDef,
        file_path: Path,
        aliases: set[str],
        class_bases: dict[str, list[str]],
    ) -> list[NodiscardMethod]:
        results: list[NodiscardMethod] = []
        own_methods = set[str]()

        for item in cls.body:
            if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if _is_nodiscard_decorated(item, aliases) or _has_nodiscard_return(item):
                own_methods.add(item.name)
                results.append(
                    NodiscardMethod(
                        class_name=cls.name,
                        method_name=item.name,
                        file_path=file_path,
                        line=item.lineno,
                        is_inherited=False,
                    ),
                )
        return results


def _resolve_decorator_aliases(tree: ast.Module) -> set[str]:
    """Find all local names that refer to the nodiscard decorator."""
    aliases: set[str] = set()
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and "nodiscard" in node.module:
                for alias in node.names:
                    if alias.name == "nodiscard":
                        aliases.add(alias.asname or alias.name)
                    if alias.name == _NODISC_MARKER:
                        aliases.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "nodiscard":
                    aliases.add(alias.asname or alias.name)
    return aliases


def _collect_class_bases(tree: ast.Module) -> dict[str, list[str]]:
    """Map class name → list of base class names for inheritance tracking."""
    bases: dict[str, list[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            base_names: list[str] = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    base_names.append(base.id)
                elif isinstance(base, ast.Attribute):
                    base_names.append(base.attr)
            bases[node.name] = base_names
    return bases


def _is_nodiscard_decorated(
    func: ast.FunctionDef | ast.AsyncFunctionDef,
    aliases: set[str],
) -> bool:
    """Check if a function has a @nodiscard decorator (or alias)."""
    for dec in func.decorator_list:
        if _matches_decorator(dec, aliases):
            return True
    return False


def _matches_decorator(node: ast.expr, aliases: set[str]) -> bool:
    """Check whether a decorator node matches a known nodiscard name."""
    # @nodiscard
    if isinstance(node, ast.Name):
        return node.id in aliases or node.id in _NODISCARD_NAMES

    # @nodiscard()  or  @nodiscard(reason="...")
    if isinstance(node, ast.Call):
        return _matches_decorator(node.func, aliases)

    # @nodiscard.nodiscard  or  @module.nodiscard
    if isinstance(node, ast.Attribute):
        if isinstance(node.value, ast.Name):
            qualname = f"{node.value.id}.{node.attr}"
            return qualname in _NODISCARD_QUALNAMES or node.attr in aliases
    return False


def _has_nodiscard_return(
    func: ast.FunctionDef | ast.AsyncFunctionDef,
) -> bool:
    """Check if the return annotation uses ``Annotated[T, NoDiscard]``."""
    ann = func.returns
    if ann is None:
        return False
    return _annotation_has_nodiscard(ann)


def _annotation_has_nodiscard(node: ast.expr) -> bool:
    """Recursively check for NoDiscard in an Annotated type."""
    # Annotated[T, NoDiscard] appears as Subscript(Name("Annotated"), Tuple(...))
    if isinstance(node, ast.Subscript):
        if isinstance(node.value, ast.Name) and node.value.id == "Annotated":
            return _tuple_contains_nodiscard(node.slice)
        if isinstance(node.value, ast.Attribute) and node.value.attr == "Annotated":
            return _tuple_contains_nodiscard(node.slice)

    # String annotation: "Annotated[Self, NoDiscard]"
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return _NODISC_MARKER in node.value

    return False


def _tuple_contains_nodiscard(node: ast.expr) -> bool:
    """Check if a tuple slice contains a NoDiscard reference."""
    if isinstance(node, ast.Tuple):
        return any(_is_nodiscard_ref(elt) for elt in node.elts)
    return _is_nodiscard_ref(node)


def _is_nodiscard_ref(node: ast.expr) -> bool:
    """Check if a node references NoDiscard."""
    if isinstance(node, ast.Name):
        return node.id == _NODISC_MARKER
    if isinstance(node, ast.Attribute):
        return node.attr == _NODISC_MARKER
    if isinstance(node, ast.Call):
        return _is_nodiscard_ref(node.func)
    return False
