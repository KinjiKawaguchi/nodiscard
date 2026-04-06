"""
Cross-file inheritance fixtures.

Demonstrates parent class with @nodiscard, child class inheriting,
mixin patterns, and Protocol definitions.
"""

from typing import Protocol

from nodiscard import nodiscard


class BaseModel:
    """Base class with @nodiscard methods."""

    @nodiscard
    def clone(self) -> "BaseModel":
        """Create a clone. Return value must not be discarded."""
        return BaseModel()

    @nodiscard
    def validate(self) -> bool:
        """Validate the model. Return value must not be discarded."""
        return True


class DerivedModel(BaseModel):
    """
    Derived class that inherits @nodiscard methods.

    Inherits clone() and validate() from BaseModel.
    """

    @nodiscard
    def process(self) -> "DerivedModel":
        """Process the model. Return value must not be discarded."""
        return DerivedModel()


class DataMixin:
    """Mixin providing @nodiscard methods."""

    @nodiscard
    def copy(self) -> "DataMixin":
        """Create a copy. Return value must not be discarded."""
        return DataMixin()

    @nodiscard
    def transform(self) -> "DataMixin":
        """Transform the data. Return value must not be discarded."""
        return DataMixin()


class MixedModel(BaseModel, DataMixin):
    """
    Model using multiple inheritance.

    Has @nodiscard methods from both BaseModel and DataMixin.
    """

    pass


class Updatable(Protocol):
    """Protocol defining updatable interface with @nodiscard method."""

    @nodiscard
    def update(self, value: str) -> "Updatable":
        """Update and return new instance."""
        ...


class ConcreteUpdatable:
    """Concrete implementation of Updatable protocol."""

    def __init__(self, value: str = "") -> None:
        """Initialize with value."""
        self._value = value

    @nodiscard
    def update(self, value: str) -> "ConcreteUpdatable":
        """Update and return new instance."""
        return ConcreteUpdatable(value)


def test_parent_method() -> None:
    """Test parent @nodiscard method."""
    derived = DerivedModel()

    # Correct: inherited parent method, result assigned
    cloned = derived.clone()

    # Violation: inherited parent method, result discarded
    derived.clone()  # VIOLATION 1

    # Violation: inherited parent method
    derived.validate()  # VIOLATION 2


def test_child_method() -> None:
    """Test child @nodiscard method."""
    derived = DerivedModel()

    # Correct: child method, result assigned
    processed = derived.process()

    # Violation: child method, result discarded
    derived.process()  # VIOLATION 3


def test_mixin_methods() -> None:
    """Test mixin @nodiscard methods."""
    mixed = MixedModel()

    # Correct: mixin method, result assigned
    copied = mixed.copy()

    # Violation: mixin method, result discarded
    mixed.copy()  # VIOLATION 4

    # Violation: mixin method, result discarded
    mixed.transform()  # VIOLATION 5


def test_protocol_method() -> None:
    """Test protocol @nodiscard method."""
    obj = ConcreteUpdatable("initial")

    # Correct: protocol method, result assigned
    updated = obj.update("new")

    # Violation: protocol method, result discarded
    obj.update("discarded")  # VIOLATION 6


def test_method_chaining_inheritance() -> DerivedModel:
    """Test method chaining with inheritance."""
    derived = DerivedModel()

    # Correct: chained methods, result returned
    return derived.clone().process()  # type: ignore


def test_multiple_inheritance() -> None:
    """Test multiple inheritance patterns."""
    mixed = MixedModel()

    # Correct: multiple inheritance, result assigned
    result1 = mixed.clone()  # from BaseModel
    result2 = mixed.copy()  # from DataMixin

    # Violations: multiple inheritance
    mixed.clone()  # VIOLATION 7
    mixed.copy()  # VIOLATION 8


def test_subclass_override() -> None:
    """Test subclass overriding @nodiscard method."""

    class CustomDerived(DerivedModel):
        @nodiscard
        def clone(self) -> "CustomDerived":
            """Override parent clone."""
            return CustomDerived()

    custom = CustomDerived()

    # Correct: overridden method, result assigned
    cloned = custom.clone()

    # Violation: overridden method, result discarded
    custom.clone()  # VIOLATION 9
