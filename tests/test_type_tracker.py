"""Test the LocalTypeTracker for type inference."""

from __future__ import annotations

import ast
from pathlib import Path

from nodiscard._models import TypeInfo
from nodiscard._type_tracker import LocalTypeTracker, resolve_variable_type


def _infer_types(source: str) -> dict[str, TypeInfo]:
    """Parse source and infer types."""
    tree = ast.parse(source)
    fp = Path("test.py")
    tracker = LocalTypeTracker()
    return tracker.infer_types(tree, fp)


class TestLocalTypeTracker:
    """Tests for LocalTypeTracker type inference."""

    def test_infer_class_self_reference(self) -> None:
        """Self in class methods maps to class name."""
        source = """class Foo:
    def method(self):
        pass
"""
        types = _infer_types(source)
        key = "Foo.method:self"
        assert key in types
        assert types[key].name == "Foo"

    def test_infer_parameter_annotation(self) -> None:
        """Parameter with type annotation is tracked."""
        source = """def func(x: Foo):
    pass
"""
        types = _infer_types(source)
        assert types.get("x") is not None

    def test_infer_assignment_from_constructor(self) -> None:
        """Assignment from constructor call infers type."""
        source = """def func():
    obj = Foo()
    pass
"""
        types = _infer_types(source)
        assert types.get("obj") is not None
        assert types["obj"].name == "Foo"

    def test_infer_annotated_assignment(self) -> None:
        """Annotated assignment tracks type."""
        source = """def func():
    x: Bar = Bar()
    pass
"""
        types = _infer_types(source)
        assert types.get("x") is not None
        assert types["x"].name == "Bar"

    def test_infer_isinstance_narrowing(self) -> None:
        """isinstance() narrowing updates type."""
        source = """def func(obj):
    if isinstance(obj, MyClass):
        pass
"""
        types = _infer_types(source)
        # isinstance narrowing in if block adds type info
        assert "MyClass" in str(types)

    def test_resolve_variable_type_unknown(self) -> None:
        """Unknown variable returns Unknown type."""
        scope: dict[str, TypeInfo] = {}
        info = resolve_variable_type(scope, "nonexistent")
        assert info.name == "Unknown"

    def test_resolve_variable_type_self_in_class(self) -> None:
        """resolve_variable_type with class context."""
        scope: dict[str, TypeInfo] = {
            "MyClass.method:self": TypeInfo(name="MyClass", module_path=None)
        }
        info = resolve_variable_type(
            scope, "self", class_name="MyClass", method_name="method"
        )
        assert info.name == "MyClass"

    def test_assignment_in_if_block(self) -> None:
        """Assignment in if block is tracked."""
        source = """def func():
    if True:
        x = Foo()
    pass
"""
        types = _infer_types(source)
        assert types.get("x") is not None

    def test_assignment_in_try_block(self) -> None:
        """Assignment in try block is tracked."""
        source = """def func():
    try:
        x = Foo()
    except:
        pass
"""
        types = _infer_types(source)
        assert types.get("x") is not None

    def test_assignment_in_for_loop(self) -> None:
        """Assignment in for loop is tracked."""
        source = """def func():
    for _ in range(1):
        x = Foo()
"""
        types = _infer_types(source)
        assert types.get("x") is not None

    def test_assignment_in_with_block(self) -> None:
        """Assignment in with block is tracked."""
        source = """def func():
    with open('file') as f:
        x = Foo()
"""
        types = _infer_types(source)
        assert types.get("x") is not None

    def test_cast_type_extraction(self) -> None:
        """cast(Foo, expr) extracts Foo as type."""
        source = """from typing import cast
def func():
    x = cast(Foo, None)
"""
        types = _infer_types(source)
        assert types.get("x") is not None
        assert types["x"].name == "Foo"

    def test_optional_type_extraction(self) -> None:
        """Optional[Foo] extracts Foo as type."""
        source = """from typing import Optional
def func(x: Optional[MyClass]):
    pass
"""
        types = _infer_types(source)
        assert types.get("x") is not None

    def test_async_function_type_inference(self) -> None:
        """Type inference works in async functions."""
        source = """async def func():
    obj = Foo()
"""
        types = _infer_types(source)
        assert types.get("obj") is not None

    def test_nested_class_not_traversed(self) -> None:
        """Nested class detection (walker traverses all)."""
        source = """class Outer:
    class Inner:
        def method(self):
            pass
"""
        types = _infer_types(source)
        key = "Inner.method:self"
        assert key in types
        assert types[key].name == "Inner"
