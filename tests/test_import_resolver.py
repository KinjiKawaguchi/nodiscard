"""Test FileSystemImportResolver import resolution.

Tests I-1 through I-5 for import statement resolution.
"""

from __future__ import annotations

import ast
from pathlib import Path

from nodiscard._import_resolver import FileSystemImportResolver


class TestFileSystemImportResolver:
    """Tests for FileSystemImportResolver.resolve_imports()."""

    def test_i1_absolute_import_resolves_to_module_file(self, tmp_path: Path) -> None:
        """I-1: from pkg.mod import Foo resolves to correct file."""
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "mod.py").write_text("class Foo: pass")

        source = "from pkg.mod import Foo"
        tree = ast.parse(source)

        resolver = FileSystemImportResolver([tmp_path])
        imports = resolver.resolve_imports(tree, Path("test.py"))

        assert len(imports) == 1
        assert imports[0].local_name == "Foo"
        assert imports[0].original_name == "Foo"
        assert imports[0].module_path == "pkg.mod"
        assert imports[0].resolved_file == pkg / "mod.py"

    def test_i2_package_import_resolves_via_init(self, tmp_path: Path) -> None:
        """I-2: from pkg import Foo resolves via __init__.py."""
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("class Foo: pass")

        source = "from pkg import Foo"
        tree = ast.parse(source)

        resolver = FileSystemImportResolver([tmp_path])
        imports = resolver.resolve_imports(tree, Path("test.py"))

        assert len(imports) == 1
        assert imports[0].local_name == "Foo"
        assert imports[0].resolved_file == pkg / "__init__.py"

    def test_i3_relative_import_resolves_correctly(self, tmp_path: Path) -> None:
        """I-3: Relative import from .mod import Foo resolves correctly."""
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "mod.py").write_text("class Foo: pass")

        source = "from .mod import Foo"
        tree = ast.parse(source)

        # When resolving relative imports, we need to know the file_path
        # to determine the package context
        file_in_pkg = pkg / "sibling.py"

        resolver = FileSystemImportResolver([tmp_path])
        imports = resolver.resolve_imports(tree, file_in_pkg)

        assert len(imports) == 1
        assert imports[0].local_name == "Foo"
        assert imports[0].module_path == "pkg.mod"
        assert imports[0].resolved_file == pkg / "mod.py"

    def test_i4_non_existent_module_resolves_to_none(self, tmp_path: Path) -> None:
        """I-4: Non-existent module → resolved_file is None."""
        source = "from nonexistent.module import Foo"
        tree = ast.parse(source)

        resolver = FileSystemImportResolver([tmp_path])
        imports = resolver.resolve_imports(tree, Path("test.py"))

        assert len(imports) == 1
        assert imports[0].resolved_file is None

    def test_i5_third_party_import_resolves_to_none(self, tmp_path: Path) -> None:
        """I-5: Third-party import → resolved_file is None."""
        source = "from typing import List"
        tree = ast.parse(source)

        resolver = FileSystemImportResolver([tmp_path])
        imports = resolver.resolve_imports(tree, Path("test.py"))

        assert len(imports) == 1
        assert imports[0].local_name == "List"
        # Standard library modules are not in tmp_path, so resolved_file is None
        assert imports[0].resolved_file is None

    def test_multiple_imports_same_statement(self, tmp_path: Path) -> None:
        """Multiple imports from same module."""
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "mod.py").write_text("class Foo: pass\nclass Bar: pass")

        source = "from pkg.mod import Foo, Bar"
        tree = ast.parse(source)

        resolver = FileSystemImportResolver([tmp_path])
        imports = resolver.resolve_imports(tree, Path("test.py"))

        assert len(imports) == 2
        assert imports[0].local_name == "Foo"
        assert imports[1].local_name == "Bar"
        assert imports[0].resolved_file == imports[1].resolved_file == pkg / "mod.py"

    def test_import_with_alias(self, tmp_path: Path) -> None:
        """from pkg.mod import Foo as F → local_name is F."""
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "mod.py").write_text("class Foo: pass")

        source = "from pkg.mod import Foo as F"
        tree = ast.parse(source)

        resolver = FileSystemImportResolver([tmp_path])
        imports = resolver.resolve_imports(tree, Path("test.py"))

        assert len(imports) == 1
        assert imports[0].local_name == "F"
        assert imports[0].original_name == "Foo"

    def test_plain_import_statement(self, tmp_path: Path) -> None:
        """import pkg.mod → resolves pkg/mod.py."""
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "mod.py").write_text("class Foo: pass")

        source = "import pkg.mod"
        tree = ast.parse(source)

        resolver = FileSystemImportResolver([tmp_path])
        imports = resolver.resolve_imports(tree, Path("test.py"))

        assert len(imports) == 1
        assert imports[0].local_name == "pkg.mod"
        assert imports[0].resolved_file == pkg / "mod.py"

    def test_pyi_stub_file_resolution(self, tmp_path: Path) -> None:
        """Resolve .pyi stub files."""
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "mod.pyi").write_text("class Foo: ...")

        source = "from pkg.mod import Foo"
        tree = ast.parse(source)

        resolver = FileSystemImportResolver([tmp_path])
        imports = resolver.resolve_imports(tree, Path("test.py"))

        assert len(imports) == 1
        assert imports[0].resolved_file == pkg / "mod.pyi"

    def test_resolve_file_public_api(self, tmp_path: Path) -> None:
        """Test public resolve_file() API."""
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "mod.py").write_text("pass")

        resolver = FileSystemImportResolver([tmp_path])
        result = resolver.resolve_file("pkg.mod")

        assert result == pkg / "mod.py"

    def test_resolve_file_caching(self, tmp_path: Path) -> None:
        """Multiple calls to resolve_file use cache."""
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "mod.py").write_text("pass")

        resolver = FileSystemImportResolver([tmp_path])
        result1 = resolver.resolve_file("pkg.mod")
        result2 = resolver.resolve_file("pkg.mod")

        assert result1 is result2  # Same cached object

    def test_multiple_src_roots(self, tmp_path: Path) -> None:
        """Search across multiple source roots."""
        root1 = tmp_path / "root1"
        root2 = tmp_path / "root2"
        root1.mkdir()
        root2.mkdir()

        pkg1 = root1 / "pkg"
        pkg1.mkdir()
        (pkg1 / "__init__.py").write_text("")
        (pkg1 / "mod1.py").write_text("pass")

        pkg2 = root2 / "pkg"
        pkg2.mkdir()
        (pkg2 / "__init__.py").write_text("")
        (pkg2 / "mod2.py").write_text("pass")

        resolver = FileSystemImportResolver([root1, root2])

        result1 = resolver.resolve_file("pkg.mod1")
        result2 = resolver.resolve_file("pkg.mod2")

        assert result1 == pkg1 / "mod1.py"
        assert result2 == pkg2 / "mod2.py"

    def test_relative_import_level_2(self, tmp_path: Path) -> None:
        """from .. import lib in nested package."""
        outer = tmp_path / "outer"
        outer.mkdir()
        (outer / "__init__.py").write_text("")

        inner = outer / "inner"
        inner.mkdir()
        (inner / "__init__.py").write_text("")
        (inner / "mod.py").write_text("class Foo: pass")

        (outer / "lib.py").write_text("class Bar: pass")

        source = "from .. import lib"
        tree = ast.parse(source)

        file_in_inner = inner / "sibling.py"

        resolver = FileSystemImportResolver([tmp_path])
        imports = resolver.resolve_imports(tree, file_in_inner)

        assert len(imports) == 1
        # from .. imports outer package itself
        assert imports[0].module_path == "outer"
        assert imports[0].resolved_file == outer / "__init__.py"
