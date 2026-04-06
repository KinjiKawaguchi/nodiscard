"""
Type inference: constructor patterns (T-1).

Tests type tracking: x = Foo(); x.method()
The checker must track that x is of type Foo and detect violations.
"""

from nodiscard import nodiscard


class Schema:
    """Schema with @nodiscard methods."""

    @nodiscard
    def merge(self, other: "Schema") -> "Schema":
        """Merge with another schema."""
        return self

    @nodiscard
    def validate(self) -> bool:
        """Validate the schema."""
        return True

    def normal(self) -> str:
        """Normal method without @nodiscard."""
        return "ok"


class Builder:
    """Builder with @nodiscard methods."""

    @nodiscard
    def build(self) -> "Builder":
        """Build and return self."""
        return self


def test_simple_constructor() -> None:
    """T-1a: Simple constructor assignment."""
    schema = Schema()  # x = Schema()
    schema.merge(schema)  # VIOLATION: x.method()


def test_constructor_in_condition() -> None:
    """T-1b: Constructor in if condition."""
    if (schema := Schema()):  # walrus
        schema.merge(schema)  # VIOLATION


def test_constructor_in_loop() -> None:
    """T-1c: Constructor in loop."""
    for _ in range(3):
        schema = Schema()
        schema.validate()  # VIOLATION


def test_multiple_assignments() -> None:
    """T-1d: Multiple assignments of same variable."""
    x = Schema()
    x.merge(x)  # VIOLATION 1

    x = Schema()
    x.validate()  # VIOLATION 2


def test_correct_usage() -> None:
    """T-1e: Correct usage (assigned)."""
    schema = Schema()
    result = schema.merge(schema)  # OK: assigned
    assert result is not None


def test_constructor_call_chain() -> None:
    """T-1f: Constructor followed by chained calls."""

    def factory() -> Schema:
        return Schema()

    schema = factory()
    schema.merge(schema)  # VIOLATION


def test_constructor_with_type_narrowing() -> None:
    """T-1g: Constructor with isinstance narrowing."""
    obj: object = Schema()
    if isinstance(obj, Schema):
        obj.merge(obj)  # VIOLATION (type narrowed to Schema)


def test_builder_pattern() -> None:
    """T-1h: Builder pattern."""
    builder = Builder()

    # Violation: result discarded
    builder.build()  # VIOLATION

    # Correct: result assigned
    result = builder.build()
    assert result is not None


def test_reassignment_after_construction() -> None:
    """T-1i: Reassignment after construction."""
    schema = Schema()
    schema = Schema()  # reassigned
    schema.validate()  # VIOLATION


def test_optional_pattern() -> None:
    """T-1j: Constructor in optional context."""
    maybe_schema = Schema()
    if maybe_schema:
        maybe_schema.merge(maybe_schema)  # VIOLATION
