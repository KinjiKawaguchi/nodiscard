"""
Lambda usage patterns.

Tests that lambda functions storing @nodiscard calls are handled correctly.
"""

from nodiscard import nodiscard


class Result:
    """Result with @nodiscard methods."""

    def __init__(self, value: int = 0) -> None:
        """Initialize."""
        self._value = value

    @nodiscard
    def increment(self) -> "Result":
        """Increment and return self."""
        return Result(self._value + 1)

    @nodiscard
    def double(self) -> "Result":
        """Double and return self."""
        return Result(self._value * 2)

    def value(self) -> int:
        """Get the value."""
        return self._value


def test_lambda_storing_function() -> None:
    """Test lambda storing a method reference (OK)."""
    result = Result(5)

    # OK: lambda stores the method, doesn't call it
    fn = lambda r: r.increment()
    assert callable(fn)

    # OK: when called, result is assigned
    new_result = fn(result)
    assert new_result.value() >= result.value()


def test_lambda_with_immediate_call() -> None:
    """Test lambda with immediate invocation."""
    result = Result(5)

    # OK: lambda is defined, then immediately called and result assigned
    new_result = (lambda r: r.increment())(result)
    assert new_result.value() >= result.value()


def test_lambda_result_discarded() -> None:
    """Test lambda result that's discarded."""
    result = Result(5)

    # VIOLATION: lambda result is discarded
    (lambda r: r.increment())(result)


def test_lambda_in_map() -> None:
    """Test lambda in map() function."""
    results = [Result(i) for i in range(3)]

    # OK: map result is assigned
    incremented = list(map(lambda r: r.increment(), results))
    assert len(incremented) == 3


def test_lambda_in_filter() -> None:
    """Test lambda in filter()."""
    results = [Result(i) for i in range(3)]

    # OK: filter result is assigned
    filtered = list(filter(lambda r: r.value() > 1, results))
    assert len(filtered) >= 0


def test_lambda_passed_to_function() -> None:
    """Test lambda passed to a function."""

    def process(fn: callable) -> Result:  # noqa: A002
        return fn(Result(10))

    # OK: lambda result is returned by process
    result = process(lambda r: r.increment())
    assert result is not None


def test_nested_lambda() -> None:
    """Test nested lambda."""
    result = Result(5)

    # OK: nested lambda, result assigned
    fn = lambda r: (lambda x: x.double())(r.increment())
    new_result = fn(result)
    assert new_result is not None


def test_lambda_in_list_comprehension() -> None:
    """Test lambda in list comprehension."""
    results = [Result(i) for i in range(3)]

    # OK: list comprehension result assigned
    incremented = [(lambda r: r.increment())(r) for r in results]
    assert len(incremented) == 3


def test_lambda_with_side_effect() -> None:
    """Test lambda that captures variables."""
    result = Result(5)
    multiplier = 2

    # OK: lambda stores function
    fn = lambda r: Result(r.value() * multiplier)

    # OK: result assigned
    modified = fn(result)
    assert modified is not None


def test_lambda_without_nodiscard() -> None:
    """Test lambda with method that doesn't have @nodiscard."""
    result = Result(5)

    # OK: value() doesn't have @nodiscard
    (lambda r: r.value())(result)

    # OK: even if discarded, no violation
    def discard_fn(x: int) -> None:
        pass

    discard_fn((lambda r: r.value())(result))
