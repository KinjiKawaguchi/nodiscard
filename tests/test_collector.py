"""Test the ASTMethodCollector for collecting @nodiscard methods."""

from __future__ import annotations

import ast
from pathlib import Path

from nodiscard._collector import ASTMethodCollector
from nodiscard._models import NodiscardMethod


def _collect_methods(source: str) -> list[NodiscardMethod]:
    """Parse source and collect @nodiscard methods."""
    tree = ast.parse(source)
    fp = Path("test.py")
    collector = ASTMethodCollector()
    return collector.collect(tree, fp)


class TestCollector:
    """Tests C-1 through C-13 for ASTMethodCollector."""

    def test_c1_collects_decorated_method(self) -> None:
        """C-1: Collects @nodiscard decorated method."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42
"""
        methods = _collect_methods(source)
        assert len(methods) == 1
        assert methods[0].class_name == "Foo"
        assert methods[0].method_name == "method"
        assert methods[0].is_inherited is False

    def test_c2_skips_non_decorated_method(self) -> None:
        """C-2: Skips non-decorated method."""
        source = """
class Foo:
    def method(self):
        return 42
"""
        methods = _collect_methods(source)
        assert len(methods) == 0

    def test_c3_collects_across_multiple_classes(self) -> None:
        """C-3: Collects across multiple classes."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

class Bar:
    @nodiscard
    def method(self):
        return 43

    def other(self):
        return 44
"""
        methods = _collect_methods(source)
        assert len(methods) == 2
        class_names = {m.class_name for m in methods}
        assert class_names == {"Foo", "Bar"}

    def test_c4_recognizes_simple_import(self) -> None:
        """C-4: Recognizes `from nodiscard import nodiscard`."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42
"""
        methods = _collect_methods(source)
        assert len(methods) == 1

    def test_c5_recognizes_module_import(self) -> None:
        """C-5: Recognizes `import nodiscard` → `@nodiscard.nodiscard`."""
        source = """
import nodiscard

class Foo:
    @nodiscard.nodiscard
    def method(self):
        return 42
"""
        methods = _collect_methods(source)
        assert len(methods) == 1

    def test_c6_recognizes_alias(self) -> None:
        """C-6: Alias `from nodiscard import nodiscard as nd` → `@nd`."""
        source = """
from nodiscard import nodiscard as nd

class Foo:
    @nd
    def method(self):
        return 42
"""
        methods = _collect_methods(source)
        assert len(methods) == 1

    def test_c7_annotated_return_type(self) -> None:
        """C-7: `Annotated[Self, NoDiscard]` return type."""
        source = """
from typing import Annotated
from nodiscard import NoDiscard

class Foo:
    def method(self) -> Annotated[int, NoDiscard]:
        return 42
"""
        methods = _collect_methods(source)
        assert len(methods) == 1
        assert methods[0].method_name == "method"

    def test_c8_string_annotation_with_future_import(self) -> None:
        """C-8: `from __future__ import annotations` with string annotation."""
        source = """
from __future__ import annotations
from typing import Annotated
from nodiscard import NoDiscard

class Foo:
    def method(self) -> Annotated[int, NoDiscard]:
        return 42
"""
        methods = _collect_methods(source)
        assert len(methods) == 1

    def test_c10_nodiscard_with_parens(self) -> None:
        """C-10: `@nodiscard()` with parens."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard()
    def method(self):
        return 42
"""
        methods = _collect_methods(source)
        assert len(methods) == 1

    def test_c11_stacked_decorators(self) -> None:
        """C-11: `@functools.cache` + `@nodiscard` stacked."""
        source = """
import functools
from nodiscard import nodiscard

class Foo:
    @functools.cache
    @nodiscard
    def method(self):
        return 42
"""
        methods = _collect_methods(source)
        assert len(methods) == 1

    def test_c12_abstractmethod_with_nodiscard(self) -> None:
        """C-12: `@abstractmethod` + `@nodiscard`."""
        source = """
from abc import abstractmethod
from nodiscard import nodiscard

class Foo:
    @abstractmethod
    @nodiscard
    def method(self):
        pass
"""
        methods = _collect_methods(source)
        assert len(methods) == 1

    def test_c13_overload_with_nodiscard(self) -> None:
        """C-13: `@overload` + `@nodiscard`."""
        source = """from typing import overload
from nodiscard import nodiscard

class Foo:
    @overload
    @nodiscard
    def method(self, x: int) -> int: ...

    @overload
    @nodiscard
    def method(self, x: str) -> str: ...

    def method(self, x):
        return x
"""
        methods = _collect_methods(source)
        # The collector identifies overloaded signatures only by @nodiscard decorator
        # Both overload variants have @nodiscard, but the implementation doesn't
        assert len(methods) == 2

    def test_multiple_methods_same_class(self) -> None:
        """Multiple @nodiscard methods in same class."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method1(self):
        return 1

    @nodiscard
    def method2(self):
        return 2

    def method3(self):
        return 3
"""
        methods = _collect_methods(source)
        assert len(methods) == 2
        method_names = {m.method_name for m in methods}
        assert method_names == {"method1", "method2"}

    def test_async_method_collected(self) -> None:
        """Async methods are collected."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    async def async_method(self):
        return 42
"""
        methods = _collect_methods(source)
        assert len(methods) == 1
        assert methods[0].method_name == "async_method"

    def test_line_number_accurate(self) -> None:
        """Line number in collected method is accurate."""
        source = """from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42
"""
        methods = _collect_methods(source)
        assert methods[0].line == 5

    def test_annotated_with_module_prefix(self) -> None:
        """NoDiscard referenced with typing module prefix."""
        source = """
from typing import Annotated
import nodiscard

class Foo:
    def method(self) -> Annotated[int, nodiscard.NoDiscard]:
        return 42
"""
        methods = _collect_methods(source)
        assert len(methods) == 1

    def test_multiple_markers_in_annotation(self) -> None:
        """Annotated with multiple markers including NoDiscard."""
        source = """
from typing import Annotated
from nodiscard import NoDiscard

class Foo:
    def method(self) -> Annotated[int, "doc", NoDiscard]:
        return 42
"""
        methods = _collect_methods(source)
        assert len(methods) == 1

    def test_does_not_collect_module_functions(self) -> None:
        """Does not collect module-level functions (only class methods)."""
        source = """
from nodiscard import nodiscard

@nodiscard
def module_func():
    return 42

class Foo:
    @nodiscard
    def method(self):
        return 43
"""
        methods = _collect_methods(source)
        assert len(methods) == 1
        assert methods[0].class_name == "Foo"

    def test_nested_class_methods(self) -> None:
        """Methods in nested classes are collected."""
        source = """
from nodiscard import nodiscard

class Outer:
    class Inner:
        @nodiscard
        def method(self):
            return 42
"""
        methods = _collect_methods(source)
        assert len(methods) == 1
        assert methods[0].class_name == "Inner"
