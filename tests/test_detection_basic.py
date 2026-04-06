"""Test basic violation detection using AST parsing."""

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


class TestDetectionBasic:
    """Tests B-1 through B-7 for basic violation detection."""

    def test_b1_simple_expression_statement_detected(self) -> None:
        """B-1: obj.method() as expression statement → detected."""
        source = """from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
obj.method()
"""
        violations = _check_source(source)
        assert len(violations) == 1
        assert violations[0].method_name == "method"
        assert violations[0].line == 9
        assert violations[0].code == "ND001"

    def test_b2_self_method_inside_class_detected(self) -> None:
        """B-2: self.method() inside class → detected."""
        source = """from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

    def other(self):
        self.method()
"""
        violations = _check_source(source)
        assert len(violations) == 1
        assert violations[0].method_name == "method"
        assert violations[0].line == 9

    def test_b3_multiple_violations_correct_line_numbers(self) -> None:
        """B-3: Multiple violations in one file → all detected with correct line numbers."""
        source = """from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
obj.method()
obj.method()
obj.method()
"""
        violations = _check_source(source)
        assert len(violations) == 3
        assert violations[0].line == 9
        assert violations[1].line == 10
        assert violations[2].line == 11

    def test_b4_method_without_nodiscard_not_detected(self) -> None:
        """B-4: Method without @nodiscard → not detected."""
        source = """class Foo:
    def method(self):
        return 42

obj = Foo()
obj.method()
"""
        violations = _check_source(source)
        assert len(violations) == 0

    def test_b5_file_with_zero_violations_empty_result(self) -> None:
        """B-5: File with zero violations → empty result."""
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

    def test_b6_await_async_method_expression_detected(self) -> None:
        """B-6: await obj.async_method() as expression → detected."""
        source = """from nodiscard import nodiscard
import asyncio

class Foo:
    @nodiscard
    async def async_method(self):
        return 42

async def main():
    obj = Foo()
    await obj.async_method()

asyncio.run(main())
"""
        violations = _check_source(source)
        assert len(violations) == 1
        assert violations[0].method_name == "async_method"
        assert violations[0].line == 11

    def test_b7_method_in_try_block_detected(self) -> None:
        """B-7: try: obj.method() → detected."""
        source = """from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
try:
    obj.method()
except Exception:
    pass
"""
        violations = _check_source(source)
        assert len(violations) == 1
        assert violations[0].line == 10

    def test_method_in_nested_if_detected(self) -> None:
        """Method call in nested if block → detected."""
        source = """from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
if True:
    if True:
        obj.method()
"""
        violations = _check_source(source)
        assert len(violations) == 1
        assert violations[0].line == 11

    def test_method_in_for_loop_detected(self) -> None:
        """Method call in for loop → detected."""
        source = """from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
for _ in range(1):
    obj.method()
"""
        violations = _check_source(source)
        assert len(violations) == 1
        assert violations[0].line == 10

    def test_method_in_while_loop_detected(self) -> None:
        """Method call in while loop → detected."""
        source = """from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
i = 0
while i < 1:
    obj.method()
    i += 1
"""
        violations = _check_source(source)
        assert len(violations) == 1
        assert violations[0].line == 11

    def test_method_in_with_statement_body_detected(self) -> None:
        """Method call in with statement body → detected."""
        source = """from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
with open('/dev/null') as f:
    obj.method()
"""
        violations = _check_source(source)
        assert len(violations) == 1
        assert violations[0].line == 10
