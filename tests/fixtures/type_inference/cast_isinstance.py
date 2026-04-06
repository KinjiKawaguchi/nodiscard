"""
Type inference: cast and isinstance patterns (T-3, T-4).

Tests type tracking: cast(Foo, x), isinstance narrowing
The checker must track types through cast and isinstance.
"""

from __future__ import annotations

from typing import Any, cast

from nodiscard import nodiscard


class Handler:
    """Handler with @nodiscard methods."""

    @nodiscard
    def handle(self, msg: str) -> Handler:
        """Handle a message."""
        return self

    @nodiscard
    def process(self) -> bool:
        """Process."""
        return True


def test_cast_pattern() -> None:
    """T-3a: cast() type narrowing."""
    obj: Any = Handler()
    h = cast(Handler, obj)
    h.handle("test")  # VIOLATION


def test_isinstance_narrowing() -> None:
    """T-3b: isinstance() type narrowing."""
    obj: object = Handler()
    if isinstance(obj, Handler):
        obj.handle("test")  # VIOLATION


def test_isinstance_else_branch() -> None:
    """T-3c: isinstance() in else branch."""
    obj: object = Handler()
    if isinstance(obj, str):
        pass
    else:
        # Type narrowed to Handler
        if isinstance(obj, Handler):
            obj.handle("test")  # VIOLATION


def test_isinstance_with_multiple_types() -> None:
    """T-3d: isinstance() with multiple types."""
    obj: object = Handler()
    if isinstance(obj, (Handler, str, int)):
        if isinstance(obj, Handler):
            obj.handle("test")  # VIOLATION


def test_cast_with_reassignment() -> None:
    """T-3e: cast() with reassignment."""
    obj: Any = Handler()
    h: Handler = cast(Handler, obj)
    h.process()  # VIOLATION


def test_isinstance_in_loop() -> None:
    """T-3f: isinstance() in loop."""
    objects: list[object] = [Handler(), "string", 42]
    for obj in objects:
        if isinstance(obj, Handler):
            obj.handle("test")  # VIOLATION


def test_cast_in_function() -> None:
    """T-3g: cast() in function."""

    def narrow(obj: Any) -> Handler:
        return cast(Handler, obj)

    h = narrow(Handler())
    h.process()  # VIOLATION


def test_isinstance_correct_usage() -> None:
    """T-3h: isinstance() with correct usage."""
    obj: object = Handler()
    if isinstance(obj, Handler):
        result = obj.handle("test")  # OK: assigned
        assert result is not None


def test_chained_isinstance() -> None:
    """T-3i: Chained isinstance checks."""

    class A:
        @nodiscard
        def method_a(self) -> A:
            return self

    class B(A):
        @nodiscard
        def method_b(self) -> B:
            return self

    obj: object = B()
    if isinstance(obj, B):
        obj.method_b()  # VIOLATION


def test_cast_with_inheritance() -> None:
    """T-3j: cast() with inheritance."""

    class Base:
        @nodiscard
        def base_method(self) -> Base:
            return self

    class Derived(Base):
        @nodiscard
        def derived_method(self) -> Derived:
            return self

    obj: Any = Derived()
    d = cast(Derived, obj)
    d.derived_method()  # VIOLATION


def test_isinstance_return_early() -> None:
    """T-3k: isinstance() with early return."""

    def process(obj: object) -> Handler:
        if not isinstance(obj, Handler):
            raise ValueError("Not a handler")
        # Type is Handler after the check
        return obj  # OK: returned

    process(Handler())


def test_multiple_isinstance_checks() -> None:
    """T-3l: Multiple isinstance checks."""
    objects: list[object] = [Handler(), Handler()]
    for obj in objects:
        if isinstance(obj, Handler):
            obj.handle("a")  # VIOLATION 1
            obj.process()  # VIOLATION 2


def test_isinstance_with_and() -> None:
    """T-3m: isinstance() with 'and' condition."""

    def use(obj: object) -> None:
        if isinstance(obj, Handler) and True:
            obj.handle("test")  # VIOLATION

    use(Handler())


def test_isinstance_with_or() -> None:
    """T-3n: isinstance() with 'or' condition."""

    def use(obj: object) -> None:
        if isinstance(obj, str) or isinstance(obj, Handler):
            if isinstance(obj, Handler):
                obj.handle("test")  # VIOLATION

    use(Handler())
