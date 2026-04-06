"""Detect violations where @nodiscard return values are discarded."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Protocol

from nodiscard._models import NodiscardMethod, TypeInfo, Violation
from nodiscard._type_tracker import resolve_variable_type

_INLINE_SUPPRESS = "nodiscard: ignore"


class ViolationDetector(Protocol):
    """Protocol for violation detection."""

    def detect(
        self,
        tree: ast.Module,
        file_path: Path,
        methods: list[NodiscardMethod],
        type_scope: dict[str, TypeInfo],
    ) -> list[Violation]: ...


class ExpressionStatementDetector:
    """Detect @nodiscard method calls used as bare expression statements."""

    def detect(
        self,
        tree: ast.Module,
        file_path: Path,
        methods: list[NodiscardMethod],
        type_scope: dict[str, TypeInfo],
    ) -> list[Violation]:
        """Find all violations in *tree*."""
        method_index = _build_method_index(methods)
        source_lines = _get_source_lines(tree)
        violations: list[Violation] = []
        self._walk_stmts(
            tree.body, file_path, method_index, type_scope, source_lines, violations,
        )
        return violations

    def _walk_stmts(
        self,
        stmts: list[ast.stmt],
        file_path: Path,
        method_index: dict[str, set[str]],
        type_scope: dict[str, TypeInfo],
        source_lines: list[str],
        violations: list[Violation],
    ) -> None:
        for stmt in stmts:
            if isinstance(stmt, ast.Expr):
                self._check_expr_stmt(
                    stmt, file_path, method_index, type_scope, source_lines, violations,
                )
            self._recurse_into(
                stmt, file_path, method_index, type_scope, source_lines, violations,
            )

    def _check_expr_stmt(
        self,
        stmt: ast.Expr,
        file_path: Path,
        method_index: dict[str, set[str]],
        type_scope: dict[str, TypeInfo],
        source_lines: list[str],
        violations: list[Violation],
    ) -> None:
        call = _unwrap_await(stmt.value)
        if not isinstance(call, ast.Call):
            return
        if _has_suppress_comment(stmt.lineno, source_lines):
            return
        match = _match_nodiscard_call(call, method_index, type_scope)
        if match is not None:
            method_name, receiver_type = match
            violations.append(
                Violation(
                    file_path=file_path,
                    line=stmt.lineno,
                    col=stmt.col_offset + 1,
                    method_name=method_name,
                    receiver_type=receiver_type,
                    code="ND001",
                    message=(
                        f"Return value of '@nodiscard' method '{method_name}' is discarded"
                    ),
                ),
            )

    def _recurse_into(
        self,
        stmt: ast.stmt,
        file_path: Path,
        method_index: dict[str, set[str]],
        type_scope: dict[str, TypeInfo],
        source_lines: list[str],
        violations: list[Violation],
    ) -> None:
        """Recurse into compound statements (if, for, try, with, etc.)."""
        child_bodies: list[list[ast.stmt]] = []
        if isinstance(stmt, (ast.If, ast.For, ast.While, ast.With)):
            child_bodies.append(stmt.body)
            child_bodies.append(stmt.orelse)
        elif isinstance(stmt, (ast.Try, ast.TryStar)):
            child_bodies.append(stmt.body)
            for handler in stmt.handlers:
                child_bodies.append(handler.body)
            child_bodies.append(stmt.orelse)
            child_bodies.append(stmt.finalbody)
        elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            child_bodies.append(stmt.body)
        elif isinstance(stmt, ast.ClassDef):
            child_bodies.append(stmt.body)
        elif isinstance(stmt, ast.Match):
            for case in stmt.cases:
                child_bodies.append(case.body)

        for body in child_bodies:
            self._walk_stmts(
                body, file_path, method_index, type_scope, source_lines, violations,
            )


def _build_method_index(
    methods: list[NodiscardMethod],
) -> dict[str, set[str]]:
    """Build class_name → {method_names} index."""
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
    """Check if a call targets a @nodiscard method. Returns (method_name, receiver_type)."""
    func = call.func
    if not isinstance(func, ast.Attribute):
        return None

    method_name = func.attr

    # obj.method() — resolve obj's type
    receiver = func.value
    receiver_type = _resolve_receiver_type(receiver, type_scope)

    if receiver_type is not None:
        methods = method_index.get(receiver_type)
        if methods and method_name in methods:
            return (method_name, receiver_type)

    # Fallback: check all classes for this method name (when type is unknown)
    if receiver_type is None:
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
        if info.name != "Unknown":
            return info.name
        return None

    # Foo() .method() — direct constructor call
    if isinstance(receiver, ast.Call) and isinstance(receiver.func, ast.Name):
        name = receiver.func.id
        if name[0:1].isupper():
            return name

    # super() — handled at the class level
    if isinstance(receiver, ast.Call) and isinstance(receiver.func, ast.Name):
        if receiver.func.id == "super":
            return None

    return None


def _get_source_lines(tree: ast.Module) -> list[str]:
    """Extract source lines from the AST if available."""
    if hasattr(tree, "_source_lines"):
        return tree._source_lines  # type: ignore[attr-defined]  # noqa: SLF001
    return []


def _has_suppress_comment(lineno: int, source_lines: list[str]) -> bool:
    """Check for ``# nodiscard: ignore`` on the given line."""
    if not source_lines:
        return False
    idx = lineno - 1
    if 0 <= idx < len(source_lines):
        return _INLINE_SUPPRESS in source_lines[idx]
    return False
