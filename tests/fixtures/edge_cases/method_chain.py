"""
Method chain patterns.

Tests obj.m1().m2() chains with @nodiscard methods.
"""

from nodiscard import nodiscard


class ChainedBuilder:
    """Builder with chainable @nodiscard methods."""

    def __init__(self, name: str = "") -> None:
        """Initialize."""
        self._name = name
        self._steps: list[str] = []

    @nodiscard
    def add_step(self, step: str) -> "ChainedBuilder":
        """Add a step and return self."""
        self._steps.append(step)
        return self

    @nodiscard
    def set_name(self, name: str) -> "ChainedBuilder":
        """Set name and return self."""
        self._name = name
        return self

    @nodiscard
    def validate(self) -> bool:
        """Validate and return result."""
        return len(self._name) > 0

    @nodiscard
    def build(self) -> dict[str, object]:
        """Build and return result."""
        return {"name": self._name, "steps": self._steps}

    def get_name(self) -> str:
        """Get name (no @nodiscard)."""
        return self._name


def test_simple_chain_correct() -> None:
    """Test simple chain with correct usage."""
    builder = ChainedBuilder()

    # OK: all in chain, result assigned
    result = builder.set_name("test").add_step("step1").add_step("step2")
    assert result is not None


def test_simple_chain_violation() -> None:
    """Test simple chain with violation."""
    builder = ChainedBuilder()

    # VIOLATION: chain result discarded
    builder.set_name("test").add_step("step1").add_step("step2")


def test_chain_with_assignment() -> None:
    """Test chain with intermediate assignment."""
    builder = ChainedBuilder()

    # OK: intermediate result assigned
    intermediate = builder.set_name("test")
    final = intermediate.add_step("step1")
    assert final is not None


def test_chain_return() -> dict[str, object]:
    """Test chain with return."""
    builder = ChainedBuilder()

    # OK: chained build result returned
    return builder.set_name("test").add_step("step1").build()  # type: ignore


def test_chain_violation_at_end() -> None:
    """Test chain where only final call is discarded."""
    builder = ChainedBuilder()

    # VIOLATION: even though add_step result is used in chain,
    # the final set_name result is discarded
    builder.set_name("test").add_step("step1")


def test_chain_with_non_nodiscard() -> None:
    """Test chain ending with non-@nodiscard method."""
    builder = ChainedBuilder()

    # OK: get_name() doesn't have @nodiscard
    name = builder.set_name("test").get_name()
    assert name == "test"


def test_chain_with_boolean_result() -> None:
    """Test chain with @nodiscard boolean method."""
    builder = ChainedBuilder()

    # VIOLATION: chain ends with validate() which returns bool
    builder.set_name("test").add_step("step1").validate()  # VIOLATION 1


def test_chain_with_dict_result() -> None:
    """Test chain with @nodiscard dict result."""
    builder = ChainedBuilder()

    # VIOLATION: chain ends with build() which returns dict
    builder.set_name("test").add_step("step1").build()  # VIOLATION 2


def test_chain_in_function_call() -> None:
    """Test chain passed to function."""

    def process(b: ChainedBuilder) -> bool:
        return True

    builder = ChainedBuilder()

    # OK: chain result passed to function
    result = process(builder.set_name("test").add_step("step1"))  # type: ignore
    assert result


def test_multiple_independent_chains() -> None:
    """Test multiple independent chains."""
    b1 = ChainedBuilder()
    b2 = ChainedBuilder()

    # VIOLATION 1: chain result discarded
    b1.set_name("first").add_step("a")

    # VIOLATION 2: chain result discarded
    b2.set_name("second").add_step("b")

    # OK: assigned
    b3 = ChainedBuilder()
    result = b3.set_name("third").add_step("c")
    assert result is not None


def test_chain_in_condition() -> None:
    """Test chain in if condition."""
    builder = ChainedBuilder()

    # OK: chain result used in condition
    if builder.set_name("test").validate():  # type: ignore
        pass


def test_chain_in_loop() -> None:
    """Test chain in loop."""
    builders = [ChainedBuilder() for _ in range(3)]

    for builder in builders:
        # VIOLATION: chain result discarded each iteration
        builder.set_name(f"builder_{id(builder)}").add_step("step1")


def test_long_chain() -> None:
    """Test very long chain."""
    builder = ChainedBuilder()

    # VIOLATION: long chain discarded
    builder.set_name("start").add_step("1").add_step("2").add_step("3").add_step(
        "4"
    ).add_step("5")


def test_chain_with_variable_extraction() -> None:
    """Test extracting variables from chain."""
    builder = ChainedBuilder()

    # Extract intermediate result
    named = builder.set_name("test")  # OK: assigned

    # Violation: then discard continuation
    named.add_step("step1").add_step("step2")  # VIOLATION 3


class DeepChain:
    """Class for testing deep nesting chains."""

    @nodiscard
    def level1(self) -> "DeepChain":
        return self

    @nodiscard
    def level2(self) -> "DeepChain":
        return self

    @nodiscard
    def level3(self) -> "DeepChain":
        return self

    @nodiscard
    def level4(self) -> "DeepChain":
        return self


def test_deep_chain_correct() -> None:
    """Test deep chain with correct usage."""
    chain = DeepChain()

    # OK: result returned
    def get_chain() -> DeepChain:
        return chain.level1().level2().level3().level4()

    result = get_chain()
    assert result is not None


def test_deep_chain_violation() -> None:
    """Test deep chain with violation."""
    chain = DeepChain()

    # VIOLATION: deep chain discarded
    chain.level1().level2().level3().level4()  # VIOLATION 4
