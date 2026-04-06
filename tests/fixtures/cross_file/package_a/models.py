"""
Package A models.

Defines FrozenModel with @nodiscard methods for immutable data patterns.
"""

from nodiscard import nodiscard


class FrozenModel:
    """
    A frozen (immutable) model class.

    Methods that return modified copies use @nodiscard to ensure the
    returned value is not discarded.
    """

    def __init__(self, name: str = "", value: int = 0) -> None:
        """Initialize the frozen model."""
        self._name = name
        self._value = value

    @property
    def name(self) -> str:
        """Get the name."""
        return self._name

    @property
    def value(self) -> int:
        """Get the value."""
        return self._value

    @nodiscard
    def model_copy(self, **kwargs) -> "FrozenModel":
        """
        Create a copy with optional field updates.

        Returns a new FrozenModel instance. Return value must not be discarded.
        """
        name = kwargs.get("name", self._name)
        value = kwargs.get("value", self._value)
        return FrozenModel(name=name, value=value)

    @nodiscard
    def replace(self, **kwargs) -> "FrozenModel":
        """
        Replace fields and return a new instance.

        This is an alias for model_copy. Return value must not be discarded.
        """
        return self.model_copy(**kwargs)

    @nodiscard
    def with_name(self, name: str) -> "FrozenModel":
        """Return a copy with the name changed."""
        return FrozenModel(name=name, value=self._value)

    @nodiscard
    def with_value(self, value: int) -> "FrozenModel":
        """Return a copy with the value changed."""
        return FrozenModel(name=self._name, value=value)

    @nodiscard
    def increment(self, amount: int = 1) -> "FrozenModel":
        """Return a copy with the value incremented."""
        return FrozenModel(name=self._name, value=self._value + amount)

    def __repr__(self) -> str:
        """Return a string representation."""
        return f"FrozenModel(name={self._name!r}, value={self._value!r})"
