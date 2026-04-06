"""
Collector: future annotations.

Tests @nodiscard with 'from __future__ import annotations' string annotations.
"""

from __future__ import annotations

from nodiscard import nodiscard


class FutureAnnotated:
    """Class with all annotations as strings (via __future__)."""

    @nodiscard
    def method1(self) -> FutureAnnotated:
        """Return type as string annotation."""
        return self

    @nodiscard
    def method2(self, other: FutureAnnotated) -> FutureAnnotated:
        """Parameter and return types as strings."""
        return self

    @nodiscard
    def validate(self) -> bool:
        """String annotation for bool."""
        return True


class ChainableFuture:
    """Chainable class with future annotations."""

    @nodiscard
    def step1(self) -> ChainableFuture:
        """Step 1."""
        return self

    @nodiscard
    def step2(self) -> ChainableFuture:
        """Step 2."""
        return self

    @nodiscard
    def step3(self) -> ChainableFuture:
        """Step 3."""
        return self


def test_future_annotations_violation() -> None:
    """Test violations with future annotations."""
    obj = FutureAnnotated()

    # VIOLATION 1: method with string annotation
    obj.method1()

    # VIOLATION 2: method with parameter string annotation
    obj.method2(obj)

    # VIOLATION 3: bool return string annotation
    obj.validate()


def test_chainable_future_violation() -> None:
    """Test chainable with future annotations."""
    obj = ChainableFuture()

    # VIOLATION 4: chain result discarded
    obj.step1().step2().step3()


def test_correct_usage_future() -> None:
    """Test correct usage with future annotations."""
    obj = FutureAnnotated()

    # OK
    r1 = obj.method1()
    r2 = obj.method2(obj)
    r3 = obj.validate()

    assert r1 is not None
    assert r2 is not None
    assert r3 is True


def test_correct_chain_future() -> None:
    """Test correct chaining with future annotations."""
    obj = ChainableFuture()

    # OK
    result = obj.step1().step2().step3()
    assert result is not None


class ComplexTypesWithFuture:
    """Complex types using future annotations."""

    from typing import List, Dict, Optional, Union

    @nodiscard
    def get_list(self) -> List[int]:
        """Return type with generic string annotation."""
        return [1, 2, 3]

    @nodiscard
    def get_dict(self) -> Dict[str, int]:
        """Return dict type string annotation."""
        return {"a": 1}

    @nodiscard
    def get_optional(self) -> Optional[str]:
        """Return optional string annotation."""
        return "value"

    @nodiscard
    def get_union(self) -> Union[int, str]:
        """Return union string annotation."""
        return 42


def test_complex_types_future() -> None:
    """Test complex types with future annotations."""
    obj = ComplexTypesWithFuture()

    # VIOLATIONS
    obj.get_list()  # VIOLATION 5
    obj.get_dict()  # VIOLATION 6
    obj.get_optional()  # VIOLATION 7
    obj.get_union()  # VIOLATION 8


def test_complex_types_correct() -> None:
    """Test complex types correct usage."""
    obj = ComplexTypesWithFuture()

    # OK
    l = obj.get_list()
    d = obj.get_dict()
    o = obj.get_optional()
    u = obj.get_union()

    assert len(l) == 3
    assert len(d) == 1
    assert o == "value"
    assert u == 42
