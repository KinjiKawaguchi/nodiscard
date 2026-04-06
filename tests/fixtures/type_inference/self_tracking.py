"""
Type inference: self tracking patterns (T-5).

Tests type tracking: self.method() within class
The checker must track that self refers to the enclosing class instance.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nodiscard import nodiscard

if TYPE_CHECKING:
    from typing import Self


class ChainableModel:
    """A model with chainable @nodiscard methods."""

    def __init__(self, name: str = "") -> None:
        """Initialize."""
        self._name = name

    @nodiscard
    def with_name(self, name: str) -> ChainableModel:
        """Set name and return self."""
        self._name = name
        return self

    @nodiscard
    def validate(self) -> bool:
        """Validate and return result."""
        return len(self._name) > 0

    @nodiscard
    def clone(self) -> Self:
        """Clone self."""
        return ChainableModel(self._name)

    def process(self) -> None:
        """Process the model."""
        # Violation: result from self.with_name is discarded
        self.with_name("processed")  # VIOLATION 1

    def chain_correctly(self) -> ChainableModel:
        """Chain methods correctly."""
        # OK: result is returned
        return self.with_name("chained")

    def multiple_calls(self) -> None:
        """Multiple self method calls."""
        # Violation 1: with_name result discarded
        self.with_name("first")  # VIOLATION 2

        # Violation 2: validate result discarded
        self.validate()  # VIOLATION 3

        # Violation 3: clone result discarded
        self.clone()  # VIOLATION 4

    def conditional_call(self, condition: bool) -> None:
        """Conditional self method call."""
        if condition:
            # Violation: result discarded in condition
            self.with_name("conditional")  # VIOLATION 5


class NestedModel:
    """Model with nested methods calling self."""

    def __init__(self) -> None:
        """Initialize."""
        self._value = 0

    @nodiscard
    def increment(self) -> NestedModel:
        """Increment and return self."""
        self._value += 1
        return self

    def outer_method(self) -> None:
        """Outer method."""

        def inner_function() -> None:
            # Note: 'self' here refers to NestedModel instance
            # Violation: result discarded
            self.increment()  # VIOLATION 6

        inner_function()

    def call_inner(self) -> None:
        """Call inner correctly."""

        def get_incremented() -> NestedModel:
            # OK: result returned
            return self.increment()

        result = get_incremented()
        assert result is not None


class MethodChaining:
    """Model with method chaining patterns."""

    @nodiscard
    def step1(self) -> MethodChaining:
        """Step 1."""
        return self

    @nodiscard
    def step2(self) -> MethodChaining:
        """Step 2."""
        return self

    @nodiscard
    def step3(self) -> MethodChaining:
        """Step 3."""
        return self

    def chain_all(self) -> MethodChaining:
        """Chain all steps correctly."""
        # OK: all results in chain, final returned
        return self.step1().step2().step3()

    def chain_with_violation(self) -> None:
        """Chain with violation at the end."""
        # Violation: final step3 result discarded
        self.step1().step2().step3()  # VIOLATION 7

    def partial_chain(self) -> MethodChaining:
        """Partial chain, then violation."""
        intermediate = self.step1().step2()  # OK: assigned
        intermediate.step3()  # VIOLATION 8
        return intermediate


class StatefulModel:
    """Model with state and self methods."""

    def __init__(self) -> None:
        """Initialize."""
        self._data: list[int] = []

    @nodiscard
    def append(self, value: int) -> StatefulModel:
        """Append and return self."""
        self._data.append(value)
        return self

    @nodiscard
    def extend(self, values: list[int]) -> StatefulModel:
        """Extend and return self."""
        self._data.extend(values)
        return self

    def fluent_api(self) -> StatefulModel:
        """Use fluent API."""
        # OK: returned
        return self.append(1).append(2).extend([3, 4])

    def fluent_with_violation(self) -> None:
        """Fluent API with violation."""
        # Violation: result discarded
        self.append(1).append(2).extend([3, 4])  # VIOLATION 9

    def loop_with_self(self) -> None:
        """Loop with self method calls."""
        for i in range(3):
            # Violation: result discarded each iteration
            self.append(i)  # VIOLATION 10


class MixedCalls:
    """Mix of self and local variable calls."""

    @nodiscard
    def transform(self) -> MixedCalls:
        """Transform."""
        return self

    def mixed_usage(self) -> None:
        """Mixed usage of self and variables."""
        local = MixedCalls()

        # Violation 1: self method result discarded
        self.transform()  # VIOLATION 11

        # Violation 2: local method result discarded
        local.transform()  # VIOLATION 12

        # OK: self method result assigned
        result1 = self.transform()
        assert result1 is not None

        # OK: local method result assigned
        result2 = local.transform()
        assert result2 is not None
