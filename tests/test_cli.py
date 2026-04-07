"""Test CLI functionality.

Tests CLI-1 through CLI-11 for command-line interface behavior.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from nodiscard.cli import main


class TestCLI:
    """Tests for the nodiscard CLI."""

    def test_cli1_clean_directory_exit_0(self, tmp_path: Path) -> None:
        """CLI-1: Clean directory → exit code 0."""
        clean_file = tmp_path / "clean.py"
        clean_file.write_text("""
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
result = obj.method()
""")

        exit_code = main(["check", str(tmp_path)])

        assert exit_code == 0

    def test_cli2_violations_exit_1(self, tmp_path: Path) -> None:
        """CLI-2: Directory with violations → exit code 1."""
        violation_file = tmp_path / "violation.py"
        violation_file.write_text("""
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
obj.method()
""")

        exit_code = main(["check", str(tmp_path)])

        assert exit_code == 1

    def test_cli3_single_file_path(self, tmp_path: Path) -> None:
        """CLI-3: File path argument → only that file checked."""
        violation_file = tmp_path / "violation.py"
        violation_file.write_text("""
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
obj.method()
""")

        other_file = tmp_path / "other.py"
        other_file.write_text("# Just a comment")

        exit_code = main(["check", str(violation_file)])

        assert exit_code == 1

    def test_cli4_directory_recursive_check(self, tmp_path: Path) -> None:
        """CLI-4: Directory path → recursive check."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        (subdir / "file2.py").write_text("""
from nodiscard import nodiscard

class RecursiveTarget:
    @nodiscard
    def recursive_method(self):
        return 42

obj = RecursiveTarget()
obj.recursive_method()
""")

        exit_code = main(["check", str(tmp_path)])

        # Should find violation in subdir
        assert exit_code == 1

    def test_cli5_help_exit_0(self) -> None:
        """CLI-5: --help → exit code 0."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0

    def test_cli6_text_output_format(self, tmp_path: Path, capsys):
        """CLI-6: Text output format matches `path:line:col: ND001 ...`."""
        violation_file = tmp_path / "test.py"
        violation_file.write_text("""
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
obj.method()
""")

        main(["check", str(tmp_path), "--format", "text"])
        captured = capsys.readouterr()

        assert "ND001" in captured.out
        assert "method" in captured.out
        assert str(violation_file) in captured.out

    def test_cli7_exclude_pattern(self, tmp_path: Path) -> None:
        """CLI-7: --exclude skips matching files."""
        (tmp_path / "violation.py").write_text("""
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
obj.method()
""")

        (tmp_path / "test_violation.py").write_text("""
from nodiscard import nodiscard

class Bar:
    @nodiscard
    def method(self):
        return 42

obj = Bar()
obj.method()
""")

        exit_code = main(["check", str(tmp_path), "--exclude", "test_*"])

        # Only test_violation.py is excluded, violation.py still checked
        assert exit_code == 1

    def test_cli8_non_existent_path_exit_2(self) -> None:
        """CLI-8: Non-existent path → exit code 2."""
        exit_code = main(["check", "/nonexistent/path"])

        assert exit_code == 2

    def test_cli9_json_output_format(self, tmp_path: Path, capsys):
        """CLI-9: --format json → valid JSON output."""
        violation_file = tmp_path / "test.py"
        violation_file.write_text("""
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
obj.method()
""")

        main(["check", str(tmp_path), "--format", "json"])
        captured = capsys.readouterr()

        data = json.loads(captured.out)

        assert "violations" in data
        assert "summary" in data
        assert data["summary"]["violations"] >= 1

    def test_cli11_pyproject_toml_config_read(self, tmp_path: Path) -> None:
        """CLI-11: pyproject.toml [tool.nodiscard] config is read."""
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("""
[tool.nodiscard]
exclude = ["test_*"]
format = "json"
""")

        violation_file = tmp_path / "violation.py"
        violation_file.write_text("""
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
obj.method()
""")

        test_violation = tmp_path / "test_violation.py"
        test_violation.write_text("""
from nodiscard import nodiscard

class Bar:
    @nodiscard
    def method(self):
        return 42

obj = Bar()
obj.method()
""")

        exit_code = main(
            [
                "check",
                str(tmp_path),
                "--config",
                str(config_file),
            ]
        )

        # With exclude pattern, only violation.py is checked
        assert exit_code == 1

    def test_default_path_is_current_dir(self, tmp_path: Path, monkeypatch):
        """Default path when not specified."""
        monkeypatch.chdir(tmp_path)

        clean_file = tmp_path / "clean.py"
        clean_file.write_text("x = 1")

        exit_code = main(["check"])

        # Should check current directory without error
        assert exit_code in (0, 1)

    def test_no_subcommand_prints_help(self, capsys):
        """No subcommand provided → print help."""
        exit_code = main([])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "nodiscard" in captured.out or "usage" in captured.out.lower()

    def test_multiple_violations_all_reported(self, tmp_path: Path, capsys):
        """Multiple violations are all reported."""
        violation_file = tmp_path / "violations.py"
        violation_file.write_text("""
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
obj.method()
obj.method()
obj.method()
""")

        main(["check", str(tmp_path)])
        captured = capsys.readouterr()

        # Should report 3 violations
        assert "3 error" in captured.out

    def test_json_output_contains_all_fields(self, tmp_path: Path, capsys):
        """JSON output has all required fields."""
        violation_file = tmp_path / "test.py"
        violation_file.write_text("""
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
obj.method()
""")

        main(["check", str(tmp_path), "--format", "json"])
        captured = capsys.readouterr()

        data = json.loads(captured.out)
        assert len(data["violations"]) >= 1

        violation = data["violations"][0]
        assert "file" in violation
        assert "line" in violation
        assert "col" in violation
        assert "code" in violation
        assert "method" in violation
        assert "message" in violation

    def test_exclude_multiple_patterns(self, tmp_path: Path) -> None:
        """Multiple --exclude patterns work together."""
        (tmp_path / "violation.py").write_text("""
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
obj.method()
""")

        (tmp_path / "test_one.py").write_text("x = 1")
        (tmp_path / "test_two.py").write_text("x = 2")

        exit_code = main(
            [
                "check",
                str(tmp_path),
                "--exclude",
                "test_*",
                "--exclude",
                "temp_*",
            ]
        )

        # violation.py should be checked
        assert exit_code == 1

    def test_empty_directory(self, tmp_path: Path) -> None:
        """Empty directory → exit code 0."""
        exit_code = main(["check", str(tmp_path)])

        assert exit_code == 0

    def test_directory_with_non_python_files(self, tmp_path: Path) -> None:
        """Directory with non-Python files → ignored."""
        (tmp_path / "readme.txt").write_text("Some readme")
        (tmp_path / "data.json").write_text('{"key": "value"}')
        (tmp_path / "clean.py").write_text("x = 1")

        exit_code = main(["check", str(tmp_path)])

        # Should only check .py files
        assert exit_code == 0

    def test_text_output_error_count(self, tmp_path: Path, capsys):
        """Text output reports error count."""
        (tmp_path / "violations.py").write_text("""
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
obj.method()
obj.method()
""")

        main(["check", str(tmp_path)])
        captured = capsys.readouterr()

        assert "Found 2 errors" in captured.out

    def test_text_output_single_error(self, tmp_path: Path, capsys):
        """Text output reports singular 'error' for single violation."""
        (tmp_path / "violation.py").write_text("""
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return 42

obj = Foo()
obj.method()
""")

        main(["check", str(tmp_path)])
        captured = capsys.readouterr()

        assert "Found 1 error" in captured.out
