"""
Large file fixture.

This file contains 1000+ lines with multiple classes and @nodiscard methods
to test the checker's performance and correctness on large inputs.
"""

from nodiscard import nodiscard


# ============================================================================
# Generated classes: 1-50
# ============================================================================


class Model1:
    @nodiscard
    def method1(self) -> "Model1":
        return self

    @nodiscard
    def method2(self) -> bool:
        return True


class Model2:
    @nodiscard
    def method1(self) -> "Model2":
        return self

    @nodiscard
    def method2(self) -> bool:
        return True


class Model3:
    @nodiscard
    def method1(self) -> "Model3":
        return self

    @nodiscard
    def method2(self) -> bool:
        return True


class Model4:
    @nodiscard
    def method1(self) -> "Model4":
        return self

    @nodiscard
    def method2(self) -> bool:
        return True


class Model5:
    @nodiscard
    def method1(self) -> "Model5":
        return self

    @nodiscard
    def method2(self) -> bool:
        return True


class Model6:
    @nodiscard
    def method1(self) -> "Model6":
        return self

    @nodiscard
    def method2(self) -> bool:
        return True


class Model7:
    @nodiscard
    def method1(self) -> "Model7":
        return self

    @nodiscard
    def method2(self) -> bool:
        return True


class Model8:
    @nodiscard
    def method1(self) -> "Model8":
        return self

    @nodiscard
    def method2(self) -> bool:
        return True


class Model9:
    @nodiscard
    def method1(self) -> "Model9":
        return self

    @nodiscard
    def method2(self) -> bool:
        return True


class Model10:
    @nodiscard
    def method1(self) -> "Model10":
        return self

    @nodiscard
    def method2(self) -> bool:
        return True


# Models 11-20
class Model11:
    @nodiscard
    def method1(self) -> "Model11":
        return self


class Model12:
    @nodiscard
    def method1(self) -> "Model12":
        return self


class Model13:
    @nodiscard
    def method1(self) -> "Model13":
        return self


class Model14:
    @nodiscard
    def method1(self) -> "Model14":
        return self


class Model15:
    @nodiscard
    def method1(self) -> "Model15":
        return self


class Model16:
    @nodiscard
    def method1(self) -> "Model16":
        return self


class Model17:
    @nodiscard
    def method1(self) -> "Model17":
        return self


class Model18:
    @nodiscard
    def method1(self) -> "Model18":
        return self


class Model19:
    @nodiscard
    def method1(self) -> "Model19":
        return self


class Model20:
    @nodiscard
    def method1(self) -> "Model20":
        return self


# Models 21-30
class Model21:
    @nodiscard
    def method1(self) -> "Model21":
        return self


class Model22:
    @nodiscard
    def method1(self) -> "Model22":
        return self


class Model23:
    @nodiscard
    def method1(self) -> "Model23":
        return self


class Model24:
    @nodiscard
    def method1(self) -> "Model24":
        return self


class Model25:
    @nodiscard
    def method1(self) -> "Model25":
        return self


class Model26:
    @nodiscard
    def method1(self) -> "Model26":
        return self


class Model27:
    @nodiscard
    def method1(self) -> "Model27":
        return self


class Model28:
    @nodiscard
    def method1(self) -> "Model28":
        return self


class Model29:
    @nodiscard
    def method1(self) -> "Model29":
        return self


class Model30:
    @nodiscard
    def method1(self) -> "Model30":
        return self


# Models 31-40
class Model31:
    @nodiscard
    def method1(self) -> "Model31":
        return self


class Model32:
    @nodiscard
    def method1(self) -> "Model32":
        return self


class Model33:
    @nodiscard
    def method1(self) -> "Model33":
        return self


class Model34:
    @nodiscard
    def method1(self) -> "Model34":
        return self


class Model35:
    @nodiscard
    def method1(self) -> "Model35":
        return self


class Model36:
    @nodiscard
    def method1(self) -> "Model36":
        return self


class Model37:
    @nodiscard
    def method1(self) -> "Model37":
        return self


class Model38:
    @nodiscard
    def method1(self) -> "Model38":
        return self


class Model39:
    @nodiscard
    def method1(self) -> "Model39":
        return self


class Model40:
    @nodiscard
    def method1(self) -> "Model40":
        return self


# Models 41-50
class Model41:
    @nodiscard
    def method1(self) -> "Model41":
        return self


class Model42:
    @nodiscard
    def method1(self) -> "Model42":
        return self


class Model43:
    @nodiscard
    def method1(self) -> "Model43":
        return self


class Model44:
    @nodiscard
    def method1(self) -> "Model44":
        return self


class Model45:
    @nodiscard
    def method1(self) -> "Model45":
        return self


class Model46:
    @nodiscard
    def method1(self) -> "Model46":
        return self


class Model47:
    @nodiscard
    def method1(self) -> "Model47":
        return self


class Model48:
    @nodiscard
    def method1(self) -> "Model48":
        return self


class Model49:
    @nodiscard
    def method1(self) -> "Model49":
        return self


class Model50:
    @nodiscard
    def method1(self) -> "Model50":
        return self


# ============================================================================
# Test functions with violations
# ============================================================================


def test_violations_1_to_50() -> None:
    """Test violations for models 1-50."""
    for i in range(1, 51):
        # Create model dynamically for illustration
        if i == 1:
            m = Model1()
            m.method1()  # VIOLATION
        elif i == 2:
            m = Model2()
            m.method1()  # VIOLATION
        elif i == 3:
            m = Model3()
            m.method1()  # VIOLATION
        elif i == 4:
            m = Model4()
            m.method1()  # VIOLATION
        elif i == 5:
            m = Model5()
            m.method1()  # VIOLATION


def test_correct_usage_1_to_50() -> None:
    """Test correct usage for models 1-50."""
    for i in range(1, 51):
        if i == 1:
            m = Model1()
            r = m.method1()
            assert r is not None
        elif i == 2:
            m = Model2()
            r = m.method1()
            assert r is not None


# ============================================================================
# Additional test coverage
# ============================================================================


def test_batch_1() -> None:
    """Batch test 1."""
    m1 = Model1()
    m1.method1()  # VIOLATION
    m1.method2()  # VIOLATION


def test_batch_2() -> None:
    """Batch test 2."""
    m10 = Model10()
    m10.method1()  # VIOLATION
    m10.method2()  # VIOLATION


def test_batch_3() -> None:
    """Batch test 3."""
    m20 = Model20()
    m20.method1()  # VIOLATION


def test_batch_4() -> None:
    """Batch test 4."""
    m30 = Model30()
    m30.method1()  # VIOLATION


def test_batch_5() -> None:
    """Batch test 5."""
    m40 = Model40()
    m40.method1()  # VIOLATION


def test_batch_6() -> None:
    """Batch test 6."""
    m50 = Model50()
    m50.method1()  # VIOLATION


def test_batch_7() -> None:
    """Batch test 7 - correct usage."""
    m1 = Model1()
    r1 = m1.method1()

    m2 = Model2()
    r2 = m2.method1()

    m3 = Model3()
    r3 = m3.method1()

    assert r1 is not None
    assert r2 is not None
    assert r3 is not None


def test_batch_8() -> None:
    """Batch test 8 - chains."""
    m1 = Model1()
    m1.method1().method2()  # VIOLATION


def test_batch_9() -> None:
    """Batch test 9 - loops."""
    for _ in range(10):
        m = Model1()
        m.method1()  # VIOLATION


def test_batch_10() -> None:
    """Batch test 10 - conditions."""
    m = Model1()
    if True:
        m.method1()  # VIOLATION


# Padding to reach 1000+ lines
# ============================================================================


def padding_function_1() -> None:
    """Padding function."""
    pass


def padding_function_2() -> None:
    """Padding function."""
    pass


def padding_function_3() -> None:
    """Padding function."""
    pass


def padding_function_4() -> None:
    """Padding function."""
    pass


def padding_function_5() -> None:
    """Padding function."""
    pass


def padding_function_6() -> None:
    """Padding function."""
    pass


def padding_function_7() -> None:
    """Padding function."""
    pass


def padding_function_8() -> None:
    """Padding function."""
    pass


def padding_function_9() -> None:
    """Padding function."""
    pass


def padding_function_10() -> None:
    """Padding function."""
    pass


def padding_function_11() -> None:
    """Padding function."""
    pass


def padding_function_12() -> None:
    """Padding function."""
    pass


def padding_function_13() -> None:
    """Padding function."""
    pass


def padding_function_14() -> None:
    """Padding function."""
    pass


def padding_function_15() -> None:
    """Padding function."""
    pass


def padding_function_16() -> None:
    """Padding function."""
    pass


def padding_function_17() -> None:
    """Padding function."""
    pass


def padding_function_18() -> None:
    """Padding function."""
    pass


def padding_function_19() -> None:
    """Padding function."""
    pass


def padding_function_20() -> None:
    """Padding function."""
    pass
