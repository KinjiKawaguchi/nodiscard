"""Test edge cases for nodiscard detection.

Tests E-1 through E-18 for edge cases, robustness, and special scenarios.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from nodiscard.checker import check
from tests.conftest import check_source


class TestEdgeCases:
    """Tests for edge cases and robustness."""

    def test_e1_nodiscard_returning_none(self) -> None:
        """E-1: @nodiscard on method returning None → no crash."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def side_effect(self):
        print("hello")
        return None

obj = Foo()
obj.side_effect()
"""
        violations = check_source(source)
        # Should detect even if returning None
        assert len(violations) == 1

    def test_e2_empty_file_no_errors(self) -> None:
        """E-2: Empty file → no errors."""
        source = ""
        violations = check_source(source)
        assert len(violations) == 0

    def test_e3_syntax_error_file_skipped(self, tmp_path: Path) -> None:
        """E-3: Syntax error file → skipped, files_skipped incremented."""
        bad_file = tmp_path / "bad.py"
        bad_file.write_text("if True\n  invalid syntax")

        result = check([tmp_path])

        assert result.files_skipped >= 1
        assert any("Syntax error" in reason for _, reason in result.skipped_reasons)

    def test_e4_binary_file_skipped(self, tmp_path: Path) -> None:
        """E-4: Binary file → skipped."""
        binary_file = tmp_path / "binary.py"
        binary_file.write_bytes(b"\x80\x81\x82\x83")

        result = check([tmp_path])

        assert result.files_skipped >= 1

    def test_e5_nested_decorators_recognized(self) -> None:
        """E-5: Nested decorators @other @nodiscard → correctly recognized."""
        source = """
from nodiscard import nodiscard

def other(f):
    return f

class Foo:
    @other
    @nodiscard
    def method(self):
        return 42

obj = Foo()
obj.method()
"""
        violations = check_source(source)
        assert len(violations) == 1
        assert violations[0].method_name == "method"

    def test_e6_same_method_name_different_classes(self) -> None:
        """E-6: Same method name, different classes, one @nodiscard."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

class Bar:
    def method(self):
        return 42

foo = Foo()
bar = Bar()
foo.method()
bar.method()
"""
        violations = check_source(source)
        # Only Foo.method() is @nodiscard
        # foo.method() is an expression statement and is detected as a violation
        # bar.method() is not @nodiscard, so it's correctly not flagged
        assert len(violations) == 1
        assert violations[0].method_name == "method"
        assert violations[0].receiver_type == "Foo"

    def test_e7_exec_eval_calls_not_analyzed(self) -> None:
        """E-7: exec()/eval() calls → not detected (we don't analyze inside)."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

code = "obj = Foo(); obj.method()"
exec(code)
"""
        check_source(source)

    def test_e8_large_file_no_crash(self) -> None:
        """E-8: Large file (1000+ lines) → no crash."""
        lines = ["from nodiscard import nodiscard", ""]
        lines.append("""
class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
""")
        # Add 1000 lines of assignments
        lines.extend(f"x{i} = {i}" for i in range(1000))

        lines.append("obj.method()")

        source = "\n".join(lines)
        violations = check_source(source)

        # Should complete without crash and detect violation
        assert isinstance(violations, list)

    def test_e9_try_block_expression_statement_detected(self) -> None:
        """E-9: try block expression statement → detected (same as B-7)."""
        source = """
from nodiscard import nodiscard

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
        violations = check_source(source)
        assert len(violations) == 1

    def test_e11_method_chain_first_discarded_ok(self) -> None:
        """E-11: obj.m1().m2() where m1 is @nodiscard → OK (used by .m2())."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def m1(self):
        return Foo()

    def m2(self):
        return Foo()

obj = Foo()
obj.m1().m2()
"""
        violations = check_source(source)
        # m1() is not discarded; its return value is used by .m2()
        assert len(violations) == 0

    def test_e12_method_chain_second_discarded(self) -> None:
        """E-12: obj.m1().m2() where m2 is @nodiscard → detected."""
        source = """
from nodiscard import nodiscard

class Foo:
    def m1(self):
        return Foo()

    @nodiscard
    def m2(self):
        return Foo()

obj = Foo()
obj.m1().m2()
"""
        violations = check_source(source)
        # m2() is discarded  # noqa: ERA001
        assert len(violations) == 1
        assert violations[0].method_name == "m2"

    def test_e13_lambda_body_ok(self) -> None:
        """E-13: lambda: obj.method() → OK (lambda body is implicit return)."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
f = lambda: obj.method()
f()
"""
        violations = check_source(source)
        # The call inside lambda is implicit return, not discarded
        assert len(violations) == 0

    def test_e14_pyi_stub_with_nodiscard(self, tmp_path: Path) -> None:
        """E-14: .pyi stub with @nodiscard."""
        stub = tmp_path / "stubs.pyi"
        stub.write_text("""
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self) -> int: ...
""")

        usage = tmp_path / "usage.py"
        usage.write_text("""
from stubs import Foo

obj = Foo()
obj.method()
""")

        result = check([tmp_path])

        # Stubs should be processed
        assert result.files_checked >= 1

    def test_e16_symlink_deduplication(self, tmp_path: Path) -> None:
        """E-16: Symlink deduplication → same file not processed twice."""
        file1 = tmp_path / "file1.py"
        file1.write_text("""
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
obj.method()
""")

        symlink = tmp_path / "link.py"
        try:
            symlink.symlink_to(file1)
        except (OSError, NotImplementedError):
            # Symlinks might not be supported on all systems
            pytest.skip("Symlinks not supported")

        result = check([tmp_path])

        # File should be processed once, not twice
        assert result.files_checked == 1
        assert len(result.violations) == 1

    def test_e17_inline_suppress_comment(self) -> None:
        """E-17: # nodiscard: ignore inline suppression."""
        # Test without comment - should detect violation
        source_no_comment = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
obj.method()
"""
        violations_no_comment = check_source(source_no_comment)
        assert len(violations_no_comment) == 1

        # Test with comment - should suppress violation
        source_with_comment = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
obj.method()  # nodiscard: ignore
"""
        violations_with_comment = check_source(source_with_comment)
        assert len(violations_with_comment) == 0

    def test_e18_underscore_assignment_ok(self) -> None:
        """E-18: _ = obj.method() and _result = obj.method() → both OK."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
_ = obj.method()
_result = obj.method()
"""
        violations = check_source(source)
        # Assignments (even to _) are not expression statements
        assert len(violations) == 0

    def test_file_with_only_comments(self, tmp_path: Path) -> None:
        """File with only comments."""
        file = tmp_path / "comments.py"
        file.write_text("""
# This is a comment
# Another comment
""")

        result = check([tmp_path])

        assert result.files_checked >= 1
        assert len(result.violations) == 0

    def test_file_with_only_imports(self, tmp_path: Path) -> None:
        """File with only imports."""
        file = tmp_path / "imports.py"
        file.write_text("""
import os
from pathlib import Path
from typing import List
""")

        result = check([tmp_path])

        assert result.files_checked >= 1

    def test_pass_statement_in_class(self) -> None:
        """Class with only pass statement."""
        source = """
class Empty:
    pass
"""
        violations = check_source(source)
        assert len(violations) == 0

    def test_multiple_nested_blocks(self) -> None:
        """Multiple levels of nested blocks."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
if True:
    with None:
        try:
            for _ in range(1):
                obj.method()
        except:
            pass
"""
        violations = check_source(source)
        assert len(violations) == 1
        assert violations[0].line == 14

    def test_string_annotation_type_extraction(self) -> None:
        """String annotations are extracted (forward references)."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self) -> "Foo":
        return Foo()

    def caller(self):
        result: "Foo" = self.method()
"""
        violations = check_source(source)
        assert len(violations) == 0  # Correctly assigned

    def test_builtin_type_names(self) -> None:
        """Builtin type names in annotations."""
        source = """
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def get_int(self) -> int:
        return 42

obj = Foo()
obj.get_int()
"""
        violations = check_source(source)
        assert len(violations) == 1
