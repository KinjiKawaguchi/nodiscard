"""
Decorator nesting patterns.

Tests stacking of @nodiscard with other decorators.
"""

from functools import wraps
from typing import Callable, TypeVar

from nodiscard import nodiscard

T = TypeVar("T")


def custom_decorator(fn: Callable[..., T]) -> Callable[..., T]:
    """Custom decorator for testing."""

    @wraps(fn)
    def wrapper(*args: object, **kwargs: object) -> T:
        return fn(*args, **kwargs)

    return wrapper


class Schema:
    """Schema with decorated @nodiscard methods."""

    @nodiscard
    @custom_decorator
    def merge(self, other: "Schema") -> "Schema":
        """Merge with @nodiscard first, then @custom_decorator."""
        return self

    @custom_decorator
    @nodiscard
    def validate(self) -> bool:
        """Validate with @custom_decorator first, then @nodiscard."""
        return True

    @nodiscard
    def simple(self) -> "Schema":
        """Simple @nodiscard method."""
        return self


def test_nodiscard_then_custom() -> None:
    """Test @nodiscard then @custom_decorator."""
    schema = Schema()

    # Should detect: merge is marked with @nodiscard
    schema.merge(schema)  # VIOLATION 1


def test_custom_then_nodiscard() -> None:
    """Test @custom_decorator then @nodiscard."""
    schema = Schema()

    # Should detect: validate is marked with @nodiscard
    schema.validate()  # VIOLATION 2


def test_correct_usage() -> None:
    """Test correct usage with decorated methods."""
    schema = Schema()

    # OK: both assigned
    m = schema.merge(schema)
    v = schema.validate()

    assert m is not None
    assert v is not None


class MultiDecorated:
    """Multiple decorators on same method."""

    @property
    def prop(self) -> str:
        """This is a property, not @nodiscard."""
        return "value"

    @nodiscard
    def method1(self) -> "MultiDecorated":
        """Decorated with @nodiscard."""
        return self

    @staticmethod
    @nodiscard
    def static_method() -> "MultiDecorated":
        """Static method with @nodiscard."""
        return MultiDecorated()

    @classmethod
    @nodiscard
    def class_method(cls) -> "MultiDecorated":
        """Classmethod with @nodiscard."""
        return cls()


def test_property() -> None:
    """Test property access (should be OK)."""
    obj = MultiDecorated()
    value = obj.prop  # OK: property access


def test_static_method() -> None:
    """Test static method with @nodiscard."""
    # Violation: static method result discarded
    MultiDecorated.static_method()  # VIOLATION 3


def test_class_method() -> None:
    """Test classmethod with @nodiscard."""
    # Violation: classmethod result discarded
    MultiDecorated.class_method()  # VIOLATION 4


def test_static_method_correct() -> None:
    """Test static method with correct usage."""
    result = MultiDecorated.static_method()  # OK: assigned
    assert result is not None
