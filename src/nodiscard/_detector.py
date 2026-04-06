"""Detect violations where @nodiscard return values are discarded."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from nodiscard._models import NodiscardMethod, TypeInfo, Violation
from nodiscard._type_tracker import resolve_variable_type

if TYPE_CHECKING:
    from pathlib import Path

_INLINE_SUPPRESS = "nodiscard: ignore"


@dataclass
class _DetectionContext:
    """Bundle of state passed through the detection walk."""

    file_path: Path
    method_index: dict[str, set[str]]
    type_scope: dict[str, TypeInfo]
    source_lines: tuple[str, ...]
    violations: list[Violation] = field(default_factory=list)


class ExpressionStatementDetector:
    """Detect @nodiscard method calls used as bare expression statements."""

    def detect(
        self,
        tree: ast.Module,
        file_path: Path,
        methods: list[NodiscardMethod],
        type_scope: dict[str, TypeInfo],
        source_lines: tuple[str, ...] = (),
    ) -> list[Violation]:
        """Find all violations in *tree*."""
        ctx = _DetectionContext(
            file_path=file_path,
            method_index=_build_method_index(methods),
            type_scope=type_scope,
            source_lines=source_lines,
        )
        _walk_stmts(tree.body, ctx)
        return ctx.violations


def _walk_stmts(stmts: list[ast.stmt], ctx: _DetectionContext) -> None:
    for stmt in stmts:
        if isinstance(stmt, ast.Expr):
            _check_expr_stmt(stmt, ctx)
        _recurse_into(stmt, ctx)


def _check_expr_stmt(stmt: ast.Expr, ctx: _DetectionContext) -> None:
    call = _unwrap_await(stmt.value)
    if not isinstance(call, ast.Call):
        return
    if _has_suppress_comment(stmt.lineno, ctx.source_lines):
        return
    match = _match_nodiscard_call(call, ctx.method_index, ctx.type_scope)
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


def _recurse_into(stmt: ast.stmt, ctx: _DetectionContext) -> None:
    """Recurse into compound statements (if, for, try, with, etc.)."""
    child_bodies: list[list[ast.stmt]] = []
    if isinstance(stmt, (ast.If, ast.For, ast.While)):
        child_bodies.append(stmt.body)
        child_bodies.append(stmt.orelse)
    elif isinstance(stmt, ast.With):
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

    # Fallback: check all classes when type is unknown
    for class_name, methods in method_index.items():
        if method_name in methods:
            return (method_name, class_name)

    return None


def _resolve_receiver_type(
    receiver: ast.expr,
    type_scope: dict[str, TypeInfo],
) -> str | None:
    """Resolve the type name of a method call receiver."""
    if isinstance(receiver, ast.Name):
        info = resolve_variable_type(type_scope, receiver.id)
        return info.name if info.name != "Unknown" else None

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
