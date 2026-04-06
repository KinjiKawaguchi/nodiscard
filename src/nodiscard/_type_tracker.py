"""Simple local-scope type inference for receiver type tracking."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING, Protocol

from nodiscard._models import TypeInfo

if TYPE_CHECKING:
    from pathlib import Path

_UNKNOWN = TypeInfo(name="Unknown", module_path=None)


class TypeTracker(Protocol):
    """Protocol for type tracking."""

    def infer_types(
        self,
        tree: ast.Module,
        file_path: Path,
    ) -> dict[str, TypeInfo]: ...


class LocalTypeTracker:
    """Infer types for local variables within function scopes."""

    def infer_types(
        self,
        tree: ast.Module,
        file_path: Path,
    ) -> dict[str, TypeInfo]:
        """Return a mapping of variable_name → TypeInfo."""
        scope: dict[str, TypeInfo] = {}
        self._collect_module_level(tree, file_path, scope)
        return scope

    def _collect_module_level(
        self,
        tree: ast.Module,
        file_path: Path,
        scope: dict[str, TypeInfo],
    ) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self._register_class_self(node, file_path, scope)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._infer_function_scope(node, file_path, scope)

    def _register_class_self(
        self,
        cls: ast.ClassDef,
        file_path: Path,
        scope: dict[str, TypeInfo],
    ) -> None:
        """Register self -> ClassName for all methods in a class."""
        for item in cls.body:
            if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if item.args.args:
                first_arg = item.args.args[0].arg
                key = f"{cls.name}.{item.name}:{first_arg}"
                scope[key] = TypeInfo(name=cls.name, module_path=file_path)

    def _infer_function_scope(
        self,
        func: ast.FunctionDef | ast.AsyncFunctionDef,
        file_path: Path,
        scope: dict[str, TypeInfo],
    ) -> None:
        """Infer types from assignments and parameter annotations."""
        self._infer_params(func, file_path, scope)
        self._infer_body(func.body, file_path, scope)

    def _infer_params(
        self,
        func: ast.FunctionDef | ast.AsyncFunctionDef,
        file_path: Path,
        scope: dict[str, TypeInfo],
    ) -> None:
        for arg in func.args.args:
            if arg.annotation is None:
                continue
            type_name = _extract_type_name(arg.annotation)
            if type_name is not None:
                scope[arg.arg] = TypeInfo(name=type_name, module_path=file_path)

    def _infer_body(
        self,
        stmts: list[ast.stmt],
        file_path: Path,
        scope: dict[str, TypeInfo],
    ) -> None:
        for stmt in stmts:
            self._infer_stmt(stmt, file_path, scope)

    def _infer_stmt(
        self,
        stmt: ast.stmt,
        file_path: Path,
        scope: dict[str, TypeInfo],
    ) -> None:
        if isinstance(stmt, ast.Assign):
            self._infer_assign(stmt, file_path, scope)
        elif isinstance(stmt, ast.AnnAssign):
            self._infer_ann_assign(stmt, file_path, scope)
        elif isinstance(stmt, ast.If):
            self._handle_if(stmt, file_path, scope)
        elif isinstance(stmt, (ast.For, ast.While)):
            self._infer_body(stmt.body, file_path, scope)
            self._infer_body(stmt.orelse, file_path, scope)
        elif isinstance(stmt, (ast.Try, ast.TryStar)):
            self._infer_body(stmt.body, file_path, scope)
            for handler in stmt.handlers:
                if handler.body:
                    self._infer_body(handler.body, file_path, scope)
            self._infer_body(stmt.orelse, file_path, scope)
            self._infer_body(stmt.finalbody, file_path, scope)
        elif isinstance(stmt, ast.With):
            self._infer_body(stmt.body, file_path, scope)

    def _infer_assign(
        self,
        stmt: ast.Assign,
        file_path: Path,
        scope: dict[str, TypeInfo],
    ) -> None:
        if len(stmt.targets) != 1:
            return
        target = stmt.targets[0]
        if not isinstance(target, ast.Name):
            return
        info = _infer_from_value(stmt.value, file_path)
        if info is not None:
            scope[target.id] = info

    def _infer_ann_assign(
        self,
        stmt: ast.AnnAssign,
        file_path: Path,
        scope: dict[str, TypeInfo],
    ) -> None:
        if not isinstance(stmt.target, ast.Name):
            return
        type_name = _extract_type_name(stmt.annotation)
        if type_name is not None:
            scope[stmt.target.id] = TypeInfo(name=type_name, module_path=file_path)

    def _handle_if(
        self,
        stmt: ast.If,
        file_path: Path,
        scope: dict[str, TypeInfo],
    ) -> None:
        narrowed = _isinstance_narrowing(stmt.test)
        if narrowed:
            var_name, type_name = narrowed
            scope[var_name] = TypeInfo(name=type_name, module_path=file_path)
        self._infer_body(stmt.body, file_path, scope)
        self._infer_body(stmt.orelse, file_path, scope)


def resolve_variable_type(
    scope: dict[str, TypeInfo],
    var_name: str,
    class_name: str | None = None,
    method_name: str | None = None,
) -> TypeInfo:
    """Look up a variable's type in the scope, including self references."""
    if class_name and method_name and var_name in ("self", "cls"):
        key = f"{class_name}.{method_name}:{var_name}"
        if key in scope:
            return scope[key]
    return scope.get(var_name, _UNKNOWN)


def _infer_from_value(value: ast.expr, file_path: Path) -> TypeInfo | None:
    """Infer type from a value expression."""
    if isinstance(value, ast.Call):
        return _infer_from_call(value, file_path)
    return None


def _infer_from_call(call: ast.Call, file_path: Path) -> TypeInfo | None:
    """Infer type from a call expression like ``Foo()`` or ``Foo.create()``."""
    if _is_cast_call(call):
        return _infer_from_cast(call, file_path)

    func = call.func
    if isinstance(func, ast.Name) and func.id[0:1].isupper():
        return TypeInfo(name=func.id, module_path=file_path)
    if (
        isinstance(func, ast.Attribute)
        and isinstance(func.value, ast.Name)
        and func.value.id[0:1].isupper()
    ):
        return TypeInfo(name=func.value.id, module_path=file_path)
    return None


def _is_cast_call(call: ast.Call) -> bool:
    """Check if a call is ``cast(T, x)``."""
    func = call.func
    min_args = 2
    if isinstance(func, ast.Name) and func.id == "cast":
        return len(call.args) >= min_args
    if isinstance(func, ast.Attribute) and func.attr == "cast":
        return len(call.args) >= min_args
    return False


def _infer_from_cast(call: ast.Call, file_path: Path) -> TypeInfo | None:
    """Extract type from ``cast(Foo, expr)``."""
    min_args = 2
    if len(call.args) < min_args:
        return None
    type_arg = call.args[0]
    name = _extract_type_name(type_arg)
    if name is not None:
        return TypeInfo(name=name, module_path=file_path)
    return None


def _extract_type_name(node: ast.expr) -> str | None:
    """Extract a simple type name from a type annotation node."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value.split("[")[0].strip()
    if (
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and node.value.id == "Optional"
    ):
        return _extract_type_name(node.slice)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        left = _extract_type_name(node.left)
        if left and left != "None":
            return left
        return _extract_type_name(node.right)
    return None


def _isinstance_narrowing(test: ast.expr) -> tuple[str, str] | None:
    """Extract (var_name, type_name) from isinstance(x, Foo) tests."""
    if not isinstance(test, ast.Call):
        return None
    func = test.func
    if not (isinstance(func, ast.Name) and func.id == "isinstance"):
        return None
    expected_args = 2
    if len(test.args) != expected_args:
        return None
    var_arg, type_arg = test.args
    if not isinstance(var_arg, ast.Name):
        return None
    type_name = _extract_type_name(type_arg)
    if type_name is None:
        return None
    return (var_arg.id, type_name)
