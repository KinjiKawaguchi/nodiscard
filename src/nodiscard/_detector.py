"""Detect violations where @nodiscard return values are discarded."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from nodiscard._models import NodiscardMethod, TypeInfo, Violation
from nodiscard._type_tracker import resolve_attribute_type, resolve_variable_type

if TYPE_CHECKING:
    from pathlib import Path

_INLINE_SUPPRESS = "nodiscard: ignore"


@dataclass
class DetectionContext:
    """Bundle of state for the detection walk. Built by the checker facade."""

    tree: ast.Module
    file_path: Path
    method_index: dict[str, set[str]]
    all_class_methods: dict[str, set[str]]
    type_scope: dict[str, TypeInfo]
    source_lines: tuple[str, ...]
    violations: list[Violation] = field(default_factory=list)


class ExpressionStatementDetector:
    """Detect @nodiscard method calls used as bare expression statements."""

    def detect(self, ctx: DetectionContext) -> list[Violation]:
        """Find all violations using the provided detection context."""
        _walk_stmts(ctx.tree.body, ctx)
        return ctx.violations


def _walk_stmts(stmts: list[ast.stmt], ctx: DetectionContext) -> None:
    for stmt in stmts:
        if isinstance(stmt, ast.Expr):
            _check_expr_stmt(stmt, ctx)
        _recurse_into(stmt, ctx)


def _check_expr_stmt(stmt: ast.Expr, ctx: DetectionContext) -> None:
    call = _unwrap_await(stmt.value)
    if not isinstance(call, ast.Call):
        return
    if _has_suppress_comment(stmt.lineno, ctx.source_lines):
        return
    match = _match_nodiscard_call(call, ctx.method_index, ctx.type_scope, ctx.all_class_methods)
    if match is not None:
        method_name, receiver_type = match
        ctx.violations.append(
            Violation(
                file_path=ctx.file_path,
                line=stmt.lineno,
                col=stmt.col_offset + 1,
                method_name=method_name,
                receiver_type=receiver_type,
                code="ND001",
                message=f"Return value of '@nodiscard' method '{method_name}' is discarded",
            ),
        )


def _recurse_into(stmt: ast.stmt, ctx: DetectionContext) -> None:
    """Recurse into compound statements (if, for, try, with, etc.)."""
    child_bodies: list[list[ast.stmt]] = []
    if isinstance(stmt, (ast.If, ast.For, ast.AsyncFor, ast.While)):
        child_bodies.append(stmt.body)
        child_bodies.append(stmt.orelse)
    elif isinstance(stmt, (ast.With, ast.AsyncWith)):
        child_bodies.append(stmt.body)
    elif isinstance(stmt, (ast.Try, ast.TryStar)):
        child_bodies.append(stmt.body)
        child_bodies.extend(h.body for h in stmt.handlers)
        child_bodies.append(stmt.orelse)
        child_bodies.append(stmt.finalbody)
    elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        child_bodies.append(stmt.body)
    elif isinstance(stmt, ast.Match):
        child_bodies.extend(case.body for case in stmt.cases)

    for body in child_bodies:
        _walk_stmts(body, ctx)


def _build_method_index(methods: list[NodiscardMethod]) -> dict[str, set[str]]:
    """Build class_name -> {method_names} index."""
    index: dict[str, set[str]] = {}
    for m in methods:
        index.setdefault(m.class_name, set()).add(m.method_name)
    return index


def _unwrap_await(node: ast.expr) -> ast.expr:
    """Unwrap ``await expr`` to get the inner expression."""
    if isinstance(node, ast.Await):
        return node.value
    return node


def _match_nodiscard_call(
    call: ast.Call,
    method_index: dict[str, set[str]],
    type_scope: dict[str, TypeInfo],
    all_class_methods: dict[str, set[str]],
) -> tuple[str, str | None] | None:
    """Return (method_name, receiver_type) if the call targets a @nodiscard method."""
    func = call.func
    if not isinstance(func, ast.Attribute):
        return None

    method_name = func.attr
    receiver_type = _resolve_receiver_type(func.value, type_scope)

    if receiver_type is not None:
        methods = method_index.get(receiver_type)
        if methods and method_name in methods:
            return (method_name, receiver_type)
        return None

    # Fallback: check all classes when type is unknown.
    # Skip if the method name also exists on a non-@nodiscard class
    # (ambiguous — could be a false positive).
    if _is_ambiguous_method(method_name, method_index, all_class_methods):
        return None

    for class_name, methods in method_index.items():
        if method_name in methods:
            return (method_name, class_name)

    return None


def _is_ambiguous_method(
    method_name: str,
    method_index: dict[str, set[str]],
    all_class_methods: dict[str, set[str]],
) -> bool:
    """Check if *method_name* exists on both @nodiscard and non-@nodiscard classes."""
    nodiscard_classes = {cls for cls, methods in method_index.items() if method_name in methods}
    all_classes = {cls for cls, methods in all_class_methods.items() if method_name in methods}
    non_nodiscard_classes = all_classes - nodiscard_classes
    return len(non_nodiscard_classes) > 0


def _resolve_receiver_type(
    receiver: ast.expr,
    type_scope: dict[str, TypeInfo],
) -> str | None:
    """Resolve the type name of a method call receiver.

    Handles:
    - Simple names: ``obj.method()`` → look up obj's type
    - Attribute chains: ``obj.attr.method()`` → resolve obj's type, then attr's type
    - Constructor calls: ``Foo().method()`` → Foo
    """
    if isinstance(receiver, ast.Name):
        info = resolve_variable_type(type_scope, receiver.id)
        return info.name if info.name != "Unknown" else None

    # obj.attr → resolve obj first, then look up attr's type annotation
    if isinstance(receiver, ast.Attribute):
        parent_type = _resolve_receiver_type(receiver.value, type_scope)
        if parent_type is not None:
            attr_info = resolve_attribute_type(type_scope, parent_type, receiver.attr)
            if attr_info.name != "Unknown":
                return attr_info.name
        return None

    if isinstance(receiver, ast.Call) and isinstance(receiver.func, ast.Name):
        name = receiver.func.id
        if name[0:1].isupper():
            return name

    return None


def _has_suppress_comment(lineno: int, source_lines: tuple[str, ...]) -> bool:
    """Check for ``# nodiscard: ignore`` on the given line."""
    if not source_lines:
        return False
    idx = lineno - 1
    if 0 <= idx < len(source_lines):
        return _INLINE_SUPPRESS in source_lines[idx]
    return False
