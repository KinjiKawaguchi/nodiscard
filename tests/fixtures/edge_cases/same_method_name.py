"""
Same method name in different classes (only one marked @nodiscard).

Tests that the checker correctly distinguishes between classes.
"""

from nodiscard import nodiscard


class ClassA:
    """First class with @nodiscard method."""

    @nodiscard
    def process(self) -> "ClassA":
        """Process in ClassA (marked with @nodiscard)."""
        return self


class ClassB:
    """Second class without @nodiscard on same method."""

    def process(self) -> "ClassB":
        """Process in ClassB (NOT marked with @nodiscard)."""
        return self


class ClassC:
    """Third class with different @nodiscard method."""

    @nodiscard
    def process(self) -> "ClassC":
        """Process in ClassC (also marked with @nodiscard)."""
        return self

    @nodiscard
    def transform(self) -> "ClassC":
        """Transform in ClassC."""
        return self


def test_class_a_violation() -> None:
    """Test ClassA with @nodiscard."""
    a = ClassA()
    a.process()  # VIOLATION 1: ClassA.process is marked


def test_class_b_no_violation() -> None:
    """Test ClassB without @nodiscard."""
    b = ClassB()
    b.process()  # OK: ClassB.process is NOT marked


def test_class_c_violations() -> None:
    """Test ClassC with multiple @nodiscard methods."""
    c = ClassC()
    c.process()  # VIOLATION 2: ClassC.process is marked
    c.transform()  # VIOLATION 3: ClassC.transform is marked


def test_correct_usage() -> None:
    """Test correct usage of marked methods."""
    a = ClassA()
    result_a = a.process()  # OK: assigned

    b = ClassB()
    result_b = b.process()  # OK: no @nodiscard, but assigned anyway

    c = ClassC()
    result_c = c.process()  # OK: assigned
    result_c2 = c.transform()  # OK: assigned

    assert result_a is not None
    assert result_b is not None
    assert result_c is not None
    assert result_c2 is not None


def test_mixed_calls() -> None:
    """Test mixed calls to marked and unmarked methods."""
    a = ClassA()
    b = ClassB()
    c = ClassC()

    # Violations
    a.process()  # VIOLATION 4
    b.process()  # OK
    c.process()  # VIOLATION 5
    c.transform()  # VIOLATION 6

    # All correct
    _ = a.process()
    _ = b.process()
    _ = c.process()
    _ = c.transform()


class ChildA(ClassA):
    """Child of ClassA inheriting @nodiscard method."""

    pass


class ChildB(ClassB):
    """Child of ClassB (no @nodiscard)."""

    pass


def test_inherited_violations() -> None:
    """Test inherited @nodiscard methods."""
    child_a = ChildA()
    child_a.process()  # VIOLATION 7: inherited from ClassA

    child_b = ChildB()
    child_b.process()  # OK: inherited from ClassB (no @nodiscard)


def test_polymorphic_call() -> None:
    """Test polymorphic calls."""

    def process_all(objects: list[ClassA | ClassB | ClassC]) -> None:
        for obj in objects:
            if isinstance(obj, ClassA):
                obj.process()  # VIOLATION 8

            elif isinstance(obj, ClassB):
                obj.process()  # OK

            elif isinstance(obj, ClassC):
                obj.process()  # VIOLATION 9

    objects: list[ClassA | ClassB | ClassC] = [
        ClassA(),
        ClassB(),
        ClassC(),
    ]
    process_all(objects)
