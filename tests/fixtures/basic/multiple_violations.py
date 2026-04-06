"""
Multiple violations fixtures.

This file contains multiple @nodiscard violations on different lines.
"""

from nodiscard import nodiscard


class ImmutableList:
    """An immutable list class with @nodiscard methods."""

    def __init__(self, items: list[int]) -> None:
        """Initialize with items."""
        self._items = items

    @nodiscard
    def append(self, item: int) -> "ImmutableList":
        """Return a new list with item appended."""
        return ImmutableList(self._items + [item])

    @nodiscard
    def remove(self, item: int) -> "ImmutableList":
        """Return a new list with item removed."""
        return ImmutableList([x for x in self._items if x != item])

    @nodiscard
    def reverse(self) -> "ImmutableList":
        """Return a reversed copy."""
        return ImmutableList(list(reversed(self._items)))

    @nodiscard
    def sort(self) -> "ImmutableList":
        """Return a sorted copy."""
        return ImmutableList(sorted(self._items))

    @nodiscard
    def filter(self, predicate: callable) -> "ImmutableList":  # noqa: A002
        """Return a filtered copy."""
        return ImmutableList([x for x in self._items if predicate(x)])

    @nodiscard
    def map(self, fn: callable) -> "ImmutableList":  # noqa: A002
        """Return a mapped copy."""
        return ImmutableList([fn(x) for x in self._items])


class Builder:
    """A builder class with multiple @nodiscard chain methods."""

    def __init__(self) -> None:
        """Initialize builder."""
        self.value: dict[str, str] = {}

    @nodiscard
    def with_name(self, name: str) -> "Builder":
        """Set name."""
        builder = Builder()
        builder.value = self.value.copy()
        builder.value["name"] = name
        return builder

    @nodiscard
    def with_age(self, age: int) -> "Builder":
        """Set age."""
        builder = Builder()
        builder.value = self.value.copy()
        builder.value["age"] = str(age)
        return builder

    @nodiscard
    def with_email(self, email: str) -> "Builder":
        """Set email."""
        builder = Builder()
        builder.value = self.value.copy()
        builder.value["email"] = email
        return builder

    def build(self) -> dict[str, str]:
        """Build the result."""
        return self.value


def multiple_violations_in_sequence() -> None:
    """Multiple violations one after another."""
    lst = ImmutableList([1, 2, 3])

    lst.append(4)  # VIOLATION 1
    lst.remove(1)  # VIOLATION 2
    lst.reverse()  # VIOLATION 3
    lst.sort()  # VIOLATION 4


def violations_in_branches() -> None:
    """Violations in different branches."""
    lst = ImmutableList([1, 2, 3])

    if True:
        lst.append(5)  # VIOLATION 5

    if False:
        lst.remove(2)  # VIOLATION 6
    else:
        lst.reverse()  # VIOLATION 7


def violations_in_loop() -> None:
    """Violations in loop."""
    lst = ImmutableList([1, 2, 3])

    for _ in range(3):
        lst.append(0)  # VIOLATION 8
        lst.sort()  # VIOLATION 9


def violations_in_function_calls() -> None:
    """Violations in function calls."""

    def process(l: ImmutableList) -> None:
        pass

    lst = ImmutableList([1, 2, 3])

    # These pass a result, but the result is discarded
    process(lst.append(10))  # VIOLATION 10 (if analysis tracks through calls)


def violations_with_methods() -> None:
    """Violations with builder methods."""
    builder = Builder()

    builder.with_name("Alice")  # VIOLATION 11
    builder.with_age(30)  # VIOLATION 12
    builder.with_email("alice@example.com")  # VIOLATION 13


def violations_mixed() -> None:
    """Mixed violations with some correct usage."""
    lst = ImmutableList([1, 2, 3])

    # Correct usage
    result = lst.append(4)

    # Violation
    lst.remove(2)  # VIOLATION 14

    # Correct usage
    if lst:
        pass

    # Violation
    lst.reverse()  # VIOLATION 15


def violations_in_try_except() -> None:
    """Violations in exception handling."""
    lst = ImmutableList([1, 2, 3])

    try:
        lst.append(100)  # VIOLATION 16
    except Exception:
        lst.sort()  # VIOLATION 17


def violations_with_chained_calls() -> None:
    """Violations where only last call is discarded."""
    lst = ImmutableList([1, 2, 3])

    # The intermediate results are used, but final is discarded
    lst.append(4).remove(1)  # VIOLATION 18 (final remove result discarded)


def correct_chaining() -> ImmutableList:
    """Correct chaining with assignment."""
    lst = ImmutableList([1, 2, 3])
    return lst.append(4).remove(1).sort()  # OK: returned


def violations_in_nested_calls() -> None:
    """Violations in nested function calls."""

    def process(l: ImmutableList) -> str:
        return str(l)

    lst = ImmutableList([1, 2, 3])

    # Result is passed to process but the value from lst methods is discarded
    process(lst)  # OK: passing existing variable
    lst.append(5)  # VIOLATION 19


def lambda_with_violations() -> None:
    """Lambda functions with violations."""
    lst = ImmutableList([1, 2, 3])

    fn = lambda x: lst.append(x)  # OK: fn stores function, but when called:
    fn(10)  # VIOLATION 20 (fn result discarded)
