"""Test the runtime @nodiscard decorator behavior."""

from __future__ import annotations

import asyncio
from typing import Annotated

import pytest

from nodiscard import NoDiscard, nodiscard


class TestDecoratorBasics:
    """Tests D-1 through D-9 for @nodiscard decorator behavior."""

    def test_d1_nodiscard_function_returns_normally(self) -> None:
        """D-1: @nodiscard function returns normally."""

        @nodiscard
        def create_value() -> int:
            return 42

        result = create_value()
        assert result == 42

    def test_d2_preserves_name_and_doc(self) -> None:
        """D-2: @nodiscard preserves __name__ and __doc__."""

        @nodiscard
        def my_function() -> str:
            """A test function."""
            return "test"

        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "A test function."

    def test_d3_wrapped_points_to_original(self) -> None:
        """D-3: __wrapped__ points to the original function."""

        def original() -> int:
            return 1

        decorated = nodiscard(original)
        assert hasattr(decorated, "__wrapped__")
        assert decorated.__wrapped__ is original

    def test_d4_works_on_regular_method(self) -> None:
        """D-4: @nodiscard works on regular methods."""

        class Foo:
            @nodiscard
            def method(self) -> str:
                return "result"

        obj = Foo()
        result = obj.method()
        assert result == "result"

    def test_d5_works_on_async_def(self) -> None:
        """D-5: @nodiscard works on async def."""

        @nodiscard
        async def async_func() -> str:
            return "async_result"

        result = asyncio.run(async_func())
        assert result == "async_result"

    def test_d6_works_with_classmethod(self) -> None:
        """D-6: @nodiscard works with @classmethod."""

        class MyClass:
            @classmethod
            @nodiscard
            def from_string(cls, _s: str) -> MyClass:
                return cls()

        result = MyClass.from_string("test")
        assert isinstance(result, MyClass)

    def test_d7_works_with_staticmethod(self) -> None:
        """D-7: @nodiscard works with @staticmethod."""

        class MyClass:
            @staticmethod
            @nodiscard
            def static_method() -> int:
                return 42

        result = MyClass.static_method()
        assert result == 42

    def test_d8_raises_typeerror_on_property(self) -> None:
        """D-8: @nodiscard raises TypeError on @property."""

        with pytest.raises(TypeError, match="cannot be applied to a property"):

            class MyClass:
                @nodiscard
                @property
                def prop(self) -> int:
                    return 1

    def test_d9_nodiscard_marker_works_with_annotated(self) -> None:
        """D-9: NoDiscard marker works with Annotated."""

        class Schema:
            def copy(self) -> Annotated[Schema, NoDiscard]:
                return Schema()

        obj = Schema()
        result = obj.copy()
        assert isinstance(result, Schema)

    def test_nodiscard_with_reason(self) -> None:
        """@nodiscard with reason parameter."""

        @nodiscard(reason="Use the return value")
        def critical_func() -> int:
            return 1

        result = critical_func()
        assert result == 1
        assert hasattr(critical_func, "__nodiscard_reason__")

    def test_nodiscard_as_decorator_factory(self) -> None:
        """@nodiscard() called with parentheses."""

        @nodiscard()
        def my_func() -> str:
            return "test"

        result = my_func()
        assert result == "test"
