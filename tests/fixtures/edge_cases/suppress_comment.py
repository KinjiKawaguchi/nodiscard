"""
Suppress comment patterns.

Tests handling of suppression directives (if implemented).
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


def test_with_suppression_comment() -> None:
    """Test with suppression comments."""
    schema = Schema()

    # This might be suppressed depending on implementation
    schema.merge(schema)  # nodiscard: ignore

    # Regular violation
    schema.validate()  # VIOLATION


def test_without_suppression() -> None:
    """Test without suppression."""
    schema = Schema()

    # VIOLATION: no suppression comment
    schema.merge(schema)

    # VIOLATION: no suppression comment
    schema.validate()


def test_inline_comments() -> None:
    """Test inline comment style."""
    schema = Schema()

    schema.merge(schema)  # nodiscard: ignore

    # This one should be detected
    schema.validate()  # VIOLATION
