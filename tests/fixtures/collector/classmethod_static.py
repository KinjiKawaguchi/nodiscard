"""
Collector: classmethod and staticmethod with @nodiscard.

Tests @nodiscard stacked with @classmethod and @staticmethod.
"""

from nodiscard import nodiscard


class WithStaticMethod:
    """Class with static method marked @nodiscard."""

    @staticmethod
    @nodiscard
    def static_process() -> str:
        """Static method with @nodiscard."""
        return "processed"

    @nodiscard
    @staticmethod
    def static_validate() -> bool:
        """Static method with @nodiscard (decorator order reversed)."""
        return True


class WithClassMethod:
    """Class with class method marked @nodiscard."""

    _cache: dict[str, "WithClassMethod"] = {}

    @classmethod
    @nodiscard
    def from_cache(cls, key: str) -> "WithClassMethod":
        """Create from cache with @nodiscard."""
        if key not in cls._cache:
            cls._cache[key] = cls()
        return cls._cache[key]

    @classmethod
    @nodiscard
    def clear_and_new(cls) -> "WithClassMethod":
        """Clear cache and create new with @nodiscard."""
        cls._cache.clear()
        return cls()


class WithMixedMethods:
    """Class with mixed method types."""

    def __init__(self, name: str = "") -> None:
        """Initialize."""
        self._name = name

    @nodiscard
    def instance_method(self) -> "WithMixedMethods":
        """Instance method with @nodiscard."""
        return self

    @staticmethod
    @nodiscard
    def static_method() -> str:
        """Static method with @nodiscard."""
        return "result"

    @classmethod
    @nodiscard
    def class_method(cls) -> "WithMixedMethods":
        """Class method with @nodiscard."""
        return cls()


def test_static_method_violation() -> None:
    """Test static method violation."""
    # VIOLATION 1: static method result discarded
    WithStaticMethod.static_process()

    # VIOLATION 2: static method result discarded
    WithStaticMethod.static_validate()


def test_class_method_violation() -> None:
    """Test class method violation."""
    # VIOLATION 3: class method result discarded
    WithClassMethod.from_cache("key1")

    # VIOLATION 4: class method result discarded
    WithClassMethod.clear_and_new()


def test_mixed_violations() -> None:
    """Test mixed method type violations."""
    obj = WithMixedMethods()

    # VIOLATION 5: instance method
    obj.instance_method()

    # VIOLATION 6: static method
    WithMixedMethods.static_method()

    # VIOLATION 7: class method
    WithMixedMethods.class_method()


def test_correct_usage() -> None:
    """Test correct usage of static/class methods."""
    # OK: static method result assigned
    s_result = WithStaticMethod.static_process()
    assert s_result == "processed"

    # OK: class method result assigned
    c_result = WithClassMethod.from_cache("key2")
    assert c_result is not None

    # OK: mixed methods result assigned
    obj = WithMixedMethods()
    i_result = obj.instance_method()
    sm_result = WithMixedMethods.static_method()
    cm_result = WithMixedMethods.class_method()

    assert i_result is not None
    assert sm_result == "result"
    assert cm_result is not None


class AlternateDecoratorOrder:
    """Test alternative decorator ordering."""

    @nodiscard
    @staticmethod
    def alt_static() -> str:
        """@nodiscard before @staticmethod."""
        return "alt"

    @nodiscard
    @classmethod
    def alt_classmethod(cls) -> "AlternateDecoratorOrder":
        """@nodiscard before @classmethod."""
        return cls()


def test_alternate_order() -> None:
    """Test alternate decorator ordering."""
    # VIOLATION 8
    AlternateDecoratorOrder.alt_static()

    # VIOLATION 9
    AlternateDecoratorOrder.alt_classmethod()


def test_alternate_order_correct() -> None:
    """Test correct usage with alternate ordering."""
    s = AlternateDecoratorOrder.alt_static()
    c = AlternateDecoratorOrder.alt_classmethod()

    assert s == "alt"
    assert c is not None
