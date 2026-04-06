"""
Package B usage.

Imports from package_a and demonstrates both correct and incorrect usage
of @nodiscard methods.
"""

from nodiscard.models import FrozenModel


def process_model(model: FrozenModel) -> FrozenModel:
    """
    Process a model correctly.

    Demonstrates correct usage: return value is assigned and returned.
    """
    updated = model.with_name("processed")
    return updated


def use_model_with_violations() -> None:
    """
    Demonstrate violations across packages.

    These violations should be detected even though the @nodiscard
    decorator is defined in package_a.
    """
    model = FrozenModel(name="original", value=10)

    # VIOLATION 1: return value discarded
    model.with_name("updated")

    # VIOLATION 2: return value discarded
    model.with_value(20)

    # VIOLATION 3: return value discarded
    model.increment(5)

    # VIOLATION 4: return value discarded
    model.model_copy(name="copy")

    # VIOLATION 5: return value discarded
    model.replace(value=99)

    # OK: return value assigned
    result = model.with_name("assigned")
    assert result is not None

    # OK: return value used in chain
    final = model.with_name("start").with_value(30)
    assert final is not None


def use_model_in_conditions() -> None:
    """Use model methods in conditions."""
    model = FrozenModel(name="test", value=5)

    # OK: result used in condition
    if model.with_value(10):
        pass

    # OK: result used in assignment
    updated = model.with_name("new_name")
    if updated:
        pass


def use_model_in_loop() -> None:
    """Use model methods in loops."""
    models = [FrozenModel(name=f"m{i}", value=i) for i in range(3)]

    for model in models:
        # OK: result used in loop
        updated = model.increment(10)
        assert updated is not None

    # VIOLATION 6: result discarded in loop
    for model in models:
        model.with_value(100)


def chain_correctly() -> FrozenModel:
    """Chain methods correctly."""
    model = FrozenModel(name="start", value=0)

    # OK: chained and returned
    return model.with_name("chained").increment(5).with_value(42)


def chain_with_violations() -> None:
    """Chain with violations."""
    model = FrozenModel(name="start", value=0)

    # VIOLATION 7: intermediate chain result discarded
    model.with_name("intermediate").increment(5)

    # VIOLATION 8: only final result discarded
    model.increment(1).with_value(100)
