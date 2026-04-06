"""Resolve import statements to file paths on disk."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from nodiscard._models import ImportedName

if TYPE_CHECKING:
    from collections.abc import Sequence

_MAX_RESOLVE_DEPTH = 20


class ImportResolver(Protocol):
    """Protocol for import resolution."""

    def resolve_imports(
        self,
        tree: ast.Module,
        file_path: Path,
    ) -> list[ImportedName]: ...


class FileSystemImportResolver:
    """Resolves import paths to source files using the filesystem."""

    def __init__(self, src_roots: Sequence[Path]) -> None:
        self._src_roots = list(src_roots)
        self._resolve_cache: dict[str, Path | None] = {}

    def resolve_imports(
        self,
        tree: ast.Module,
        file_path: Path,
    ) -> list[ImportedName]:
        """Extract and resolve all import statements in the AST."""
        results: list[ImportedName] = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ImportFrom):
                results.extend(self._resolve_import_from(node, file_path))
            elif isinstance(node, ast.Import):
                results.extend(self._resolve_import(node))
        return results

    def _resolve_import_from(
        self,
        node: ast.ImportFrom,
        file_path: Path,
    ) -> list[ImportedName]:
        results: list[ImportedName] = []
        module = node.module or ""
        level = node.level or 0

        if level > 0:
            base = self._resolve_relative_base(file_path, level)
            if base is None:
                return results
            full_module = f"{base}.{module}" if module else base
        else:
            full_module = module

        for alias in node.names:
            local = alias.asname if alias.asname else alias.name
            resolved = self._find_module_file(full_module)
            results.append(
                ImportedName(
                    local_name=local,
                    original_name=alias.name,
                    module_path=full_module,
                    resolved_file=resolved,
                ),
            )
        return results

    def _resolve_import(self, node: ast.Import) -> list[ImportedName]:
        results: list[ImportedName] = []
        for alias in node.names:
            local = alias.asname if alias.asname else alias.name
            resolved = self._find_module_file(alias.name)
            results.append(
                ImportedName(
                    local_name=local,
                    original_name=alias.name,
                    module_path=alias.name,
                    resolved_file=resolved,
                ),
            )
        return results

    def _resolve_relative_base(self, file_path: Path, level: int) -> str | None:
        """Convert relative import level to a dotted module base."""
        current = file_path.parent
        for _ in range(level - 1):
            current = current.parent

        for root in self._src_roots:
            try:
                rel = current.relative_to(root)
            except ValueError:
                continue
            return ".".join(rel.parts)
        return None

    def _find_module_file(self, module_path: str) -> Path | None:
        """Find the .py file for a dotted module path."""
        if module_path in self._resolve_cache:
            return self._resolve_cache[module_path]

        result = self._do_find(module_path)
        self._resolve_cache[module_path] = result
        return result

    def _do_find(self, module_path: str) -> Path | None:
        parts = module_path.split(".")
        for root in self._src_roots:
            # Try as package/__init__.py
            pkg_init = root / Path(*parts) / "__init__.py"
            if pkg_init.is_file():
                return pkg_init
            # Try as module.py
            if len(parts) >= 1:
                mod_file = root / Path(*parts[:-1]) / f"{parts[-1]}.py"
                if mod_file.is_file():
                    return mod_file
            # Try .pyi stub
            pyi_file = root / Path(*parts[:-1]) / f"{parts[-1]}.pyi"
            if pyi_file.is_file():
                return pyi_file
        return None

    def resolve_file(self, module_path: str) -> Path | None:
        """Public accessor to resolve a module path to a file."""
        return self._find_module_file(module_path)
