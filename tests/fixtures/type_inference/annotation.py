"""
Type inference: annotation patterns (T-2).

Tests type tracking: x: Foo = ...; def f(x: Foo):
The checker must track types from annotations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nodiscard import nodiscard

if TYPE_CHECKING:
    from typing import Self


class Result:
    """Result class with @nodiscard methods."""

    @nodiscard
    def map(self, fn: callable) -> Result:  # noqa: A002
        """Map over result."""
        return self

    @nodiscard
    def filter(self, predicate: callable) -> Result:  # noqa: A002
        """Filter result."""
        return self

    @nodiscard
    def unwrap(self) -> object:
        """Unwrap the result."""
        return None


def test_type_annotation_assignment() -> None:
    """T-2a: Type annotation in assignment."""
    x: Result = Result()
    x.map(lambda y: y)  # VIOLATION


def test_annotation_in_function_param() -> None:
    """T-2b: Type annotation in function parameter."""

    def process(result: Result) -> None:
        result.map(lambda y: y)  # VIOLATION

    process(Result())


def test_annotation_with_union() -> None:
    """T-2c: Union type annotation."""
    x: Result | None = Result()
    if x:
        x.map(lambda y: y)  # VIOLATION


def test_multiple_annotations() -> None:
    """T-2d: Multiple parameters with annotations."""

    def combine(a: Result, b: Result) -> Result:
        a.map(lambda y: y)  # VIOLATION
        return b.filter(lambda y: True)  # VIOLATION

    combine(Result(), Result())


def test_return_annotation() -> None:
    """T-2e: Return type annotation."""

    def factory() -> Result:
        x: Result = Result()
        x.map(lambda y: y)  # VIOLATION
        return x  # OK: returned

    factory()


def test_annotation_correct_usage() -> None:
    """T-2f: Correct usage with annotation."""
    x: Result = Result()
    y = x.map(lambda a: a)  # OK: assigned
    assert y is not None


def test_annotation_in_lambda() -> None:
    """T-2g: Annotation in lambda."""

    def apply_fn(result: Result, fn: callable) -> Result:  # noqa: A002
        return result.map(fn)  # OK: returned

    fn = lambda x: x
    apply_fn(Result(), fn)


def test_self_annotation() -> None:
    """T-2h: Self type annotation in method."""

    class Chain:
        @nodiscard
        def step(self) -> Self:
            return self

        def process(self) -> None:
            self.step()  # VIOLATION


def test_generic_annotation() -> None:
    """T-2i: Generic type annotation."""
    from typing import Generic, TypeVar

    T = TypeVar("T")

    class Container(Generic[T]):
        def __init__(self, value: T) -> None:
            self.value = value

    results: list[Result] = [Result(), Result()]
    for r in results:
        r.map(lambda x: x)  # VIOLATION


def test_forward_ref_annotation() -> None:
    """T-2j: Forward reference annotation."""

    def use_result(r: "Result") -> None:
        r.map(lambda x: x)  # VIOLATION

    use_result(Result())
