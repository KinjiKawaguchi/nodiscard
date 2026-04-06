"""
Collector: @abstractmethod and @overload with @nodiscard.

Tests @nodiscard stacked with @abstractmethod and @overload.
"""

from abc import ABC, abstractmethod
from typing import overload

from nodiscard import nodiscard


class AbstractBase(ABC):
    """Abstract base class with @nodiscard abstract method."""

    @abstractmethod
    @nodiscard
    def abstract_method(self) -> "AbstractBase":
        """Abstract method with @nodiscard."""
        ...

    @abstractmethod
    @nodiscard
    def abstract_validate(self) -> bool:
        """Abstract validation method."""
        ...


class ConcreteImpl(AbstractBase):
    """Concrete implementation of abstract methods."""

    @nodiscard
    def abstract_method(self) -> ConcreteImpl:
        """Implement abstract method with @nodiscard."""
        return self

    @nodiscard
    def abstract_validate(self) -> bool:
        """Implement abstract validation."""
        return True


class WithOverload:
    """Class with overloaded methods marked @nodiscard."""

    @overload
    @nodiscard
    def process(self, value: int) -> int: ...

    @overload
    @nodiscard
    def process(self, value: str) -> str: ...

    @nodiscard
    def process(self, value):  # type: ignore
        """Process with overloads."""
        return value


def test_abstract_violation() -> None:
    """Test abstract method violation."""
    obj = ConcreteImpl()

    # VIOLATION 1: abstract_method result discarded
    obj.abstract_method()

    # VIOLATION 2: abstract_validate result discarded
    obj.abstract_validate()


def test_overload_violation() -> None:
    """Test overload violation."""
    obj = WithOverload()

    # VIOLATION 3: overload result discarded
    obj.process(42)

    # VIOLATION 4: overload result discarded
    obj.process("test")


def test_correct_usage() -> None:
    """Test correct usage."""
    obj = ConcreteImpl()

    # OK: results assigned
    m_result = obj.abstract_method()
    v_result = obj.abstract_validate()

    assert m_result is not None
    assert v_result is True

    with_overload = WithOverload()

    # OK: overload results assigned
    p1 = with_overload.process(42)
    p2 = with_overload.process("test")

    assert p1 == 42
    assert p2 == "test"


class MixedAbstractAndOverload:
    """Mix abstract and overload (overload doesn't work on abstract, but test structure)."""

    @abstractmethod
    @overload
    @nodiscard
    def method1(self, x: int) -> int: ...

    @abstractmethod
    @overload
    @nodiscard
    def method1(self, x: str) -> str:  # type: ignore
        ...

    @abstractmethod
    @nodiscard
    def method1(self, x):  # type: ignore
        """Mixed decorators."""
        ...


class MixedImpl(MixedAbstractAndOverload):
    """Implementation of mixed decorators."""

    @overload
    @nodiscard
    def method1(self, x: int) -> int: ...

    @overload
    @nodiscard
    def method1(self, x: str) -> str: ...

    @nodiscard
    def method1(self, x):  # type: ignore
        return x


def test_mixed_violations() -> None:
    """Test mixed decorator violations."""
    obj = MixedImpl()

    # VIOLATION 5
    obj.method1(42)

    # VIOLATION 6
    obj.method1("test")


def test_mixed_correct() -> None:
    """Test mixed decorator correct usage."""
    obj = MixedImpl()

    # OK
    r1 = obj.method1(42)
    r2 = obj.method1("test")

    assert r1 == 42
    assert r2 == "test"


class AlternateDecoratorOrders:
    """Test various decorator orderings with @nodiscard."""

    @nodiscard
    @abstractmethod
    def order1(self) -> "AlternateDecoratorOrders":
        """@nodiscard before @abstractmethod."""
        ...

    @abstractmethod
    @nodiscard
    def order2(self) -> "AlternateDecoratorOrders":
        """@abstractmethod before @nodiscard."""
        ...

    @nodiscard
    @overload
    def order3(self, x: int) -> int: ...

    @overload
    @nodiscard
    def order4(self, x: str) -> str: ...


class AlternateImpl(AlternateDecoratorOrders):
    """Implementation with alternate orders."""

    @nodiscard
    def order1(self) -> AlternateImpl:
        return self

    @nodiscard
    def order2(self) -> AlternateImpl:
        return self

    @nodiscard
    def order3(self, x: int) -> int:  # type: ignore
        return x

    @nodiscard
    def order4(self, x: str) -> str:  # type: ignore
        return x


def test_alternate_orders() -> None:
    """Test alternate decorator orders."""
    obj = AlternateImpl()

    # VIOLATIONS
    obj.order1()  # VIOLATION 7
    obj.order2()  # VIOLATION 8
    obj.order3(42)  # VIOLATION 9
    obj.order4("test")  # VIOLATION 10
