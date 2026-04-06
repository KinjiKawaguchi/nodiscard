"""
Basic violation fixtures.

This file contains classes with @nodiscard methods that are called as
expression statements (violations).
"""

from nodiscard import nodiscard


class Schema:
    """A schema class with @nodiscard methods."""

    @nodiscard
    def merge(self, other: "Schema") -> "Schema":
        """Merge with another schema. Return value must be captured."""
        return self

    @nodiscard
    def validate(self) -> bool:
        """Validate the schema. Return value must be captured."""
        return True

    def normal_method(self) -> str:
        """Normal method without @nodiscard."""
        return "hello"


class Processor:
    """A processor class with multiple @nodiscard methods."""

    def __init__(self) -> None:
        """Initialize the processor."""
        self.data: str = ""

    @nodiscard
    def transform(self) -> "Processor":
        """Transform the data. Return value must be captured."""
        return self

    @nodiscard
    async def async_process(self) -> "Processor":
        """Asynchronously process data. Return value must be captured."""
        return self

    def side_effect_method(self) -> None:
        """This method has side effects and doesn't need a return value."""
        self.data = "modified"


# Violations: these calls discard the return value
def test_violations() -> None:
    """Demonstrate various violations."""
    schema = Schema()
    schema.merge(schema)  # VIOLATION: return value discarded

    schema.validate()  # VIOLATION: return value discarded

    processor = Processor()
    processor.transform()  # VIOLATION: return value discarded

    processor.side_effect_method()  # OK: returns None
