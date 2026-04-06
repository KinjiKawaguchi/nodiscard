"""Test correct usage patterns that should NOT be flagged."""

from __future__ import annotations

import ast
from pathlib import Path

from nodiscard._collector import ASTMethodCollector
from nodiscard._detector import ExpressionStatementDetector
from nodiscard._models import Violation
from nodiscard._type_tracker import LocalTypeTracker


def _check_source(source: str) -> list[Violation]:
    """Parse source and detect violations."""
    tree = ast.parse(source)
    tree._source_lines = source.splitlines()  # type: ignore[attr-defined]
    fp = Path("test.py")
    collector = ASTMethodCollector()
    tracker = LocalTypeTracker()
    detector = ExpressionStatementDetector()
    methods = collector.collect(tree, fp)
    types = tracker.infer_types(tree, fp)
    return detector.detect(tree, fp, methods, types, tuple(source.splitlines()))


class TestCorrectUsagePatterns:
    """Tests U-1 through U-25 for correct usage patterns (zero violations expected)."""

    def test_u1_simple_assignment(self) -> None:
        """U-1: x = obj.method() → not flagged."""
        source = """from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
x = obj.method()
"""
        violations = _check_source(source)
        assert len(violations) == 0

    def test_u2_reassignment(self) -> None:
        """U-2: obj = obj.method() → not flagged."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return self

obj = Foo()
obj = obj.method()
"""
        violations = _check_source(source)
        assert len(violations) == 0

    def test_u3_return_statement(self) -> None:
        """U-3: return obj.method() → not flagged."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

def get_value(obj):
    return obj.method()
"""
        violations = _check_source(source)
        assert len(violations) == 0

    def test_u4_yield_statement(self) -> None:
        """U-4: yield obj.method() → not flagged."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

def generator(obj):
    yield obj.method()
"""
        violations = _check_source(source)
        assert len(violations) == 0

    def test_u5_function_argument(self) -> None:
        """U-5: func(obj.method()) → not flagged."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
print(obj.method())
"""
        violations = _check_source(source)
        assert len(violations) == 0

    def test_u6_if_condition(self) -> None:
        """U-6: if obj.method(): → not flagged."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return True

obj = Foo()
if obj.method():
    pass
"""
        violations = _check_source(source)
        assert len(violations) == 0

    def test_u7_while_condition(self) -> None:
        """U-7: while obj.method(): → not flagged."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return False

obj = Foo()
while obj.method():
    break
"""
        violations = _check_source(source)
        assert len(violations) == 0

    def test_u8_assert_statement(self) -> None:
        """U-8: assert obj.method() → not flagged."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return True

obj = Foo()
assert obj.method()
"""
        violations = _check_source(source)
        assert len(violations) == 0

    def test_u9_list_comprehension(self) -> None:
        """U-9: [obj.method() for x in items] → not flagged."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
items = [obj.method() for _ in range(1)]
"""
        violations = _check_source(source)
        assert len(violations) == 0

    def test_u10_ternary_expression(self) -> None:
        """U-10: x = obj.method() if cond else other → not flagged."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
x = obj.method() if True else 0
"""
        violations = _check_source(source)
        assert len(violations) == 0

    def test_u11_tuple_unpacking(self) -> None:
        """U-11: a, b = obj.method() → not flagged."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return (1, 2)

obj = Foo()
a, b = obj.method()
"""
        violations = _check_source(source)
        assert len(violations) == 0

    def test_u12_walrus_operator(self) -> None:
        """U-12: if (x := obj.method()): → not flagged."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
if (x := obj.method()):
    pass
"""
        violations = _check_source(source)
        assert len(violations) == 0

    def test_u13_method_chaining(self) -> None:
        """U-13: obj.method().chained() → not flagged."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return self

    def chained(self):
        return 42

obj = Foo()
result = obj.method().chained()
"""
        violations = _check_source(source)
        assert len(violations) == 0

    def test_u14_await_async_method(self) -> None:
        """U-14: x = await obj.async_method() → not flagged."""
        source = """
from nodiscard import nodiscard
import asyncio

class Foo:
    @nodiscard
    async def async_method(self):
        return 42

async def main():
    obj = Foo()
    x = await obj.async_method()
"""
        violations = _check_source(source)
        assert len(violations) == 0

    def test_u15_underscore_assignment(self) -> None:
        """U-15: _ = obj.method() → not flagged."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
_ = obj.method()
"""
        violations = _check_source(source)
        assert len(violations) == 0

    def test_u16_for_loop_iteration(self) -> None:
        """U-16: for x in obj.method(): → not flagged."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return [1, 2, 3]

obj = Foo()
for x in obj.method():
    pass
"""
        violations = _check_source(source)
        assert len(violations) == 0

    def test_u17_with_statement(self) -> None:
        """U-17: with obj.method() as x: → not flagged."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

obj = Foo()
with obj.method() as x:
    pass
"""
        violations = _check_source(source)
        assert len(violations) == 0

    def test_u18_match_statement(self) -> None:
        """U-18: match obj.method(): → not flagged."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 1

obj = Foo()
match obj.method():
    case 1:
        pass
"""
        violations = _check_source(source)
        assert len(violations) == 0

    def test_u19_raise_from_exception(self) -> None:
        """U-19: raise E() from obj.method() → not flagged."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return Exception("test")

obj = Foo()
try:
    raise Exception("orig") from obj.method()
except Exception:
    pass
"""
        violations = _check_source(source)
        assert len(violations) == 0

    def test_u20_or_expression(self) -> None:
        """U-20: x = a or obj.method() → not flagged."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
x = False or obj.method()
"""
        violations = _check_source(source)
        assert len(violations) == 0

    def test_u21_list_literal(self) -> None:
        """U-21: x = [obj.method()] → not flagged."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
x = [obj.method()]
"""
        violations = _check_source(source)
        assert len(violations) == 0

    def test_u22_f_string(self) -> None:
        """U-22: f"{obj.method()}" → not flagged."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
s = f"{obj.method()}"
"""
        violations = _check_source(source)
        assert len(violations) == 0

    def test_u23_dict_assignment(self) -> None:
        """U-23: d[key] = obj.method() → not flagged."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
d = {}
d['key'] = obj.method()
"""
        violations = _check_source(source)
        assert len(violations) == 0

    def test_u24_binop_assigned(self) -> None:
        """U-24: x = obj.method() + other → not flagged."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 10

obj = Foo()
x = obj.method() + 5
"""
        violations = _check_source(source)
        assert len(violations) == 0

    def test_u25_unary_assigned(self) -> None:
        """U-25: x = not obj.method() → not flagged."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return True

obj = Foo()
x = not obj.method()
"""
        violations = _check_source(source)
        assert len(violations) == 0

    def test_and_expression(self) -> None:
        """x = a and obj.method() → not flagged."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
x = True and obj.method()
"""
        violations = _check_source(source)
        assert len(violations) == 0

    def test_tuple_literal(self) -> None:
        """x = (obj.method(),) → not flagged."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
x = (obj.method(),)
"""
        violations = _check_source(source)
        assert len(violations) == 0

    def test_dict_literal(self) -> None:
        """x = {'key': obj.method()} → not flagged."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
x = {'key': obj.method()}
"""
        violations = _check_source(source)
        assert len(violations) == 0
