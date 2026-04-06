"""
Collector: Annotated return types.

Tests @nodiscard using Annotated[T, NoDiscard] style annotations.
"""

from __future__ import annotations

from typing import Annotated, TYPE_CHECKING

from nodiscard import NoDiscard
from nodiscard import nodiscard

if TYPE_CHECKING:
    from typing import Self


class AnnotatedStyle:
    """Class using Annotated[T, NoDiscard] for return types."""

    def method_with_decorator(self) -> AnnotatedStyle:
        """Using @nodiscard decorator."""
        return self

    def method_with_annotated(self) -> Annotated[AnnotatedStyle, NoDiscard]:
        """Using Annotated[Self, NoDiscard]."""
        return self

    def method_with_annotated_bool(self) -> Annotated[bool, NoDiscard]:
        """Using Annotated[bool, NoDiscard]."""
        return True

    def method_without_nodiscard(self) -> AnnotatedStyle:
        """No @nodiscard marker."""
        return self


class MixedStyle:
    """Class mixing decorator and Annotated styles."""

    @nodiscard
    def decorated_method(self) -> MixedStyle:
        """Using @nodiscard decorator."""
        return self

    def annotated_method(self) -> Annotated[MixedStyle, NoDiscard]:
        """Using Annotated."""
        return self

    def normal_method(self) -> MixedStyle:
        """No marker."""
        return self


def test_annotated_violation() -> None:
    """Test violation with Annotated style."""
    obj = AnnotatedStyle()

    # Violations: return values discarded
    obj.method_with_annotated()  # VIOLATION 1
    obj.method_with_annotated_bool()  # VIOLATION 2

    # OK: not marked with @nodiscard
    obj.method_without_nodiscard()


def test_mixed_violations() -> None:
    """Test mixed style violations."""
    obj = MixedStyle()

    # Violations
    obj.decorated_method()  # VIOLATION 3
    obj.annotated_method()  # VIOLATION 4

    # OK: not marked
    obj.normal_method()


def test_correct_usage() -> None:
    """Test correct usage."""
    obj = AnnotatedStyle()
    r1 = obj.method_with_annotated()
    r2 = obj.method_with_annotated_bool()

    mixed = MixedStyle()
    r3 = mixed.decorated_method()
    r4 = mixed.annotated_method()

    assert r1 is not None
    assert r2 is not None
    assert r3 is not None
    assert r4 is not None


class SelfAnnotated:
    """Using Self in Annotated."""

    def copy(self) -> Annotated[Self, NoDiscard]:
        """Return a copy marked with Annotated[Self, NoDiscard]."""
        return self

    def process(self) -> None:
        """Process with violation."""
        self.copy()  # VIOLATION 5


def test_self_annotated() -> None:
    """Test Self in Annotated."""
    obj = SelfAnnotated()
    result = obj.copy()
    assert result is not None
