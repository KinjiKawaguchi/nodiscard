"""
Collector: import aliases.

Tests different ways of importing @nodiscard decorator.
"""

from nodiscard import nodiscard
from nodiscard import nodiscard as nd
import nodiscard


# Using direct import
@nodiscard
class DirectImport:
    @nodiscard
    def method(self) -> "DirectImport":
        return self


# Using alias import
@nd
class AliasImport:
    @nd
    def method(self) -> "AliasImport":
        return self


# Using module import
class ModuleImport:
    @nodiscard.nodiscard
    def method(self) -> "ModuleImport":
        return self


def test_direct_import_violation() -> None:
    """Test with direct import."""
    obj = DirectImport()
    obj.method()  # VIOLATION 1


def test_alias_import_violation() -> None:
    """Test with alias import."""
    obj = AliasImport()
    obj.method()  # VIOLATION 2


def test_module_import_violation() -> None:
    """Test with module import."""
    obj = ModuleImport()
    obj.method()  # VIOLATION 3


def test_correct_usage() -> None:
    """Test correct usage with different imports."""
    d = DirectImport()
    r1 = d.method()

    a = AliasImport()
    r2 = a.method()

    m = ModuleImport()
    r3 = m.method()

    assert r1 is not None
    assert r2 is not None
    assert r3 is not None
