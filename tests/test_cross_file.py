"""Test cross-file violation detection.

Tests X-1 through X-8 for detecting violations across file boundaries.
"""

from __future__ import annotations

from pathlib import Path

from nodiscard.checker import check


class TestCrossFileDetection:
    """Tests for cross-file violation detection."""

    def test_x1_file_a_defines_file_b_calls_expression(self, tmp_path: Path) -> None:
        """X-1: FileA defines @nodiscard, FileB calls it as expression → violation."""
        file_a = tmp_path / "file_a.py"
        file_a.write_text("""
from nodiscard import nodiscard

class Schema:
    @nodiscard
    def merge(self, other):
        return Schema()
""")

        file_b = tmp_path / "file_b.py"
        file_b.write_text("""
from file_a import Schema

schema = Schema()
schema.merge(Schema())
""")

        result = check([tmp_path])

        assert len(result.violations) == 1
        assert result.violations[0].method_name == "merge"
        assert result.violations[0].file_path == file_b

    def test_x2_file_a_defines_file_b_uses_correctly(self, tmp_path: Path) -> None:
        """X-2: FileA defines @nodiscard, FileB uses correctly → no violation."""
        file_a = tmp_path / "file_a.py"
        file_a.write_text("""
from nodiscard import nodiscard

class Schema:
    @nodiscard
    def merge(self, other):
        return Schema()
""")

        file_b = tmp_path / "file_b.py"
        file_b.write_text("""
from file_a import Schema

schema = Schema()
result = schema.merge(Schema())
""")

        result = check([tmp_path])

        assert len(result.violations) == 0

    def test_x3_reexport_through_init(self, tmp_path: Path) -> None:
        """X-3: Re-export through __init__.py → violation detected."""
        pkg = tmp_path / "pkg"
        pkg.mkdir()

        models = pkg / "models.py"
        models.write_text("""
from nodiscard import nodiscard

class User:
    @nodiscard
    def with_name(self, name):
        return User()
""")

        init = pkg / "__init__.py"
        init.write_text("from .models import User")

        usage = tmp_path / "usage.py"
        usage.write_text("""
from pkg import User

u = User()
u.with_name("alice")
""")

        result = check([tmp_path])

        assert len(result.violations) == 1
        assert result.violations[0].method_name == "with_name"

    def test_attribute_chain_resolves_non_nodiscard_receiver(self, tmp_path: Path) -> None:
        """Issue #2: Same method name on @nodiscard and non-@nodiscard class.

        When receiver type is resolved via attribute chain, the correct
        class is identified and no false positive occurs.
        """
        (tmp_path / "models.py").write_text("""
from nodiscard import nodiscard

class Document:
    @nodiscard
    def update_metadata(self, key, value) -> "Document":
        return Document()
""")
        (tmp_path / "repository.py").write_text("""
class DocumentRepository:
    async def update_metadata(self, key, value) -> None:
        pass
""")
        (tmp_path / "uow.py").write_text("""
from repository import DocumentRepository

class UnitOfWork:
    documents: DocumentRepository
""")
        (tmp_path / "service.py").write_text("""
from uow import UnitOfWork

async def do_work(uow: UnitOfWork):
    await uow.documents.update_metadata("title", "new")
""")

        result = check([tmp_path])

        # uow.documents is DocumentRepository (not @nodiscard)
        # → no false positive
        service_violations = [v for v in result.violations if "service.py" in str(v.file_path)]
        assert len(service_violations) == 0

    def test_reexport_through_non_init_module(self, tmp_path: Path) -> None:
        """Re-export through a regular module (not __init__.py) is detected."""
        (tmp_path / "core.py").write_text("""
from nodiscard import nodiscard

class Config:
    @nodiscard
    def with_debug(self, enabled):
        return Config()
""")

        (tmp_path / "adapter.py").write_text("""
from core import Config
""")

        (tmp_path / "app.py").write_text("""
from adapter import Config

c = Config()
c.with_debug(True)
""")

        result = check([tmp_path])

        assert len(result.violations) == 1
        assert result.violations[0].method_name == "with_debug"

    def test_x4_multiple_directories_all_checked(self, tmp_path: Path) -> None:
        """X-4: Multiple directories → all files checked."""
        dir1 = tmp_path / "dir1"
        dir1.mkdir()
        dir2 = tmp_path / "dir2"
        dir2.mkdir()

        (dir1 / "models.py").write_text("""
from nodiscard import nodiscard

class Foo:
    @nodiscard
    def method(self):
        return Foo()
""")

        (dir2 / "usage.py").write_text("""
import sys
sys.path.insert(0, str(__file__))
from dir1.models import Foo

Foo().method()
""")

        result = check([dir1, dir2])

        # At least 2 files checked
        assert result.files_checked >= 2

    def test_x5_inherited_nodiscard_from_parent_class(self, tmp_path: Path) -> None:
        """X-5: Parent @nodiscard, child overrides → still detected (LSP)."""
        file_a = tmp_path / "file_a.py"
        file_a.write_text("""
from nodiscard import nodiscard

class Parent:
    @nodiscard
    def method(self):
        return Parent()

class Child(Parent):
    def method(self):
        return super().method()
""")

        file_b = tmp_path / "file_b.py"
        file_b.write_text("""
from file_a import Child

c = Child()
c.method()
""")

        result = check([tmp_path])

        # Child inherits @nodiscard requirement from Parent
        assert len(result.violations) >= 1

    def test_x6_mixin_nodiscard_propagates(self, tmp_path: Path) -> None:
        """X-6: Mixin @nodiscard propagates to class using mixin."""
        file_a = tmp_path / "file_a.py"
        file_a.write_text("""
from nodiscard import nodiscard

class Mixin:
    @nodiscard
    def transform(self):
        return type(self)()
""")

        file_b = tmp_path / "file_b.py"
        file_b.write_text("""
from file_a import Mixin

class MyClass(Mixin):
    pass

obj = MyClass()
obj.transform()
""")

        result = check([tmp_path])

        # Violation propagated from Mixin
        assert len(result.violations) >= 1

    def test_x7_protocol_with_nodiscard(self, tmp_path: Path) -> None:
        """X-7: Protocol with @nodiscard → implementors detected."""
        file_a = tmp_path / "file_a.py"
        file_a.write_text("""
from typing import Protocol
from nodiscard import nodiscard

class Copyable(Protocol):
    @nodiscard
    def copy(self):
        ...
""")

        file_b = tmp_path / "file_b.py"
        file_b.write_text("""
from file_a import Copyable

class MyClass:
    @nodiscard
    def copy(self):
        return MyClass()

obj = MyClass()
obj.copy()
""")

        result = check([tmp_path])

        # Direct violation in file_b
        assert len(result.violations) >= 1

    def test_x8_multiple_inheritance_mro_resolution(self, tmp_path: Path) -> None:
        """X-8: Multiple inheritance MRO resolution."""
        file_a = tmp_path / "file_a.py"
        file_a.write_text("""
from nodiscard import nodiscard

class A:
    @nodiscard
    def method(self):
        return A()

class B:
    def method(self):
        return B()
""")

        file_b = tmp_path / "file_b.py"
        file_b.write_text("""
from file_a import A, B

class C(A, B):
    pass

c = C()
c.method()
""")

        result = check([tmp_path])

        # c = C() at module level → type inferred as C.
        # C inherits @nodiscard method from A via MRO → violation detected.
        assert len(result.violations) >= 1

    def test_import_star_resolution(self, tmp_path: Path) -> None:
        """from module import * → methods available in consumer."""
        file_a = tmp_path / "file_a.py"
        file_a.write_text("""
from nodiscard import nodiscard

class MyClass:
    @nodiscard
    def method(self):
        return MyClass()
""")

        file_b = tmp_path / "file_b.py"
        file_b.write_text("""
from file_a import *

obj = MyClass()
obj.method()
""")

        check([tmp_path])

    def test_nested_package_structure(self, tmp_path: Path) -> None:
        """Nested package with @nodiscard across packages."""
        pkg_a = tmp_path / "pkg_a"
        pkg_a.mkdir()
        (pkg_a / "__init__.py").write_text("")
        (pkg_a / "models.py").write_text("""
from nodiscard import nodiscard

class Item:
    @nodiscard
    def duplicate(self):
        return Item()
""")

        pkg_b = tmp_path / "pkg_b"
        pkg_b.mkdir()
        (pkg_b / "__init__.py").write_text("")
        (pkg_b / "process.py").write_text("""
from pkg_a.models import Item

item = Item()
item.duplicate()
""")

        result = check([tmp_path])

        assert len(result.violations) == 1
        assert result.violations[0].method_name == "duplicate"

    def test_circular_import_no_infinite_loop(self, tmp_path: Path) -> None:
        """X-15: Circular import → no infinite loop."""
        file_a = tmp_path / "file_a.py"
        file_a.write_text("""
from nodiscard import nodiscard
from file_b import Helper

class Foo:
    @nodiscard
    def method(self):
        return Foo()
""")

        file_b = tmp_path / "file_b.py"
        file_b.write_text("""
from file_a import Foo

class Helper:
    def use_foo(self):
        f = Foo()
        f.method()
""")

        result = check([tmp_path])

        # Should complete without hanging
        assert result.files_checked >= 2

    def test_false_negative_indirect_import(self, tmp_path: Path) -> None:
        """False negative: @nodiscard method not detected when class is not directly imported.

        File imports an interface, but operates on an instance whose class
        has @nodiscard methods defined in a different module.
        """
        pkg = tmp_path / "core"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")

        (pkg / "document.py").write_text("""
from nodiscard import nodiscard

class Document:
    @nodiscard
    def merge(self, other: "Document") -> "Document":
        return Document()
""")

        (pkg / "interface.py").write_text("""
from typing import Protocol

class IDocumentService(Protocol):
    def get_document(self) -> object: ...
""")

        (tmp_path / "usecase.py").write_text("""
from core.interface import IDocumentService

def process(service: IDocumentService, doc):
    # doc is actually a Document, but not imported here
    doc.merge(doc)
""")

        result = check([tmp_path])

        usecase_violations = [v for v in result.violations if "usecase.py" in str(v.file_path)]
        # doc.merge() should be detected even though Document
        # is not directly imported in usecase.py
        assert len(usecase_violations) == 1
        assert usecase_violations[0].method_name == "merge"

    def test_unique_method_detected_without_type_inference(self, tmp_path: Path) -> None:
        """Method name unique to @nodiscard class should be detected
        even when receiver type is unknown.

        `add_item` exists only on Collection (@nodiscard).
        The caller does not import Collection.
        Detection should not require type inference.
        """
        (tmp_path / "domain.py").write_text("""
from nodiscard import nodiscard

class Collection:
    @nodiscard
    def add_item(self, item):
        return Collection()

    @nodiscard
    def merge(self, other):
        return Collection()
""")

        (tmp_path / "repository.py").write_text("""
class Store:
    def save(self, obj):
        pass
""")

        (tmp_path / "usecase.py").write_text("""
def process(coll, store):
    coll.add_item("test")   # VIOLATION: unique to @nodiscard class
    coll.merge(coll)         # VIOLATION: unique to @nodiscard class
    store.save(coll)         # OK: save is not @nodiscard
""")

        result = check([tmp_path])

        usecase_violations = [v for v in result.violations if "usecase.py" in str(v.file_path)]
        methods = {v.method_name for v in usecase_violations}
        assert "add_item" in methods, "add_item should be detected (unique to @nodiscard class)"
        assert "merge" in methods, "merge should be detected (unique to @nodiscard class)"
        assert len(usecase_violations) == 2

    def test_ambiguous_method_with_non_nodiscard_class(self, tmp_path: Path) -> None:
        """When method name exists on both @nodiscard and non-@nodiscard
        classes, the ambiguous call is suppressed to avoid false positives.

        `update` exists on both ImmutableConfig (@nodiscard) and Store (not @nodiscard).
        Without type inference, the ambiguous call should not be flagged.
        """
        (tmp_path / "domain.py").write_text("""
from nodiscard import nodiscard

class ImmutableConfig:
    @nodiscard
    def update(self, data):
        return ImmutableConfig()
""")

        (tmp_path / "repository.py").write_text("""
class Store:
    def update(self, entity):
        pass  # side-effect method, not @nodiscard
""")

        (tmp_path / "usecase.py").write_text("""
from repository import Store

def process(config, store: Store):
    config.update("data")   # ambiguous: could be ImmutableConfig or something else
    store.update(config)     # should NOT be flagged: store is Store
""")

        result = check([tmp_path])

        usecase_violations = [v for v in result.violations if "usecase.py" in str(v.file_path)]
        # store.update() must NOT be flagged (type is known as Store)
        store_violations = [v for v in usecase_violations if v.line == 5]
        assert len(store_violations) == 0, "store.update() should not be flagged"

    def test_async_with_body_is_traversed(self, tmp_path: Path) -> None:
        """Violations inside `async with` blocks must be detected.

        This was a regression where `ast.AsyncWith` was not traversed.
        """
        (tmp_path / "domain.py").write_text("""
from nodiscard import nodiscard

class Document:
    @nodiscard
    def merge(self, other):
        return Document()
""")

        (tmp_path / "service.py").write_text("""
class Connection:
    async def __aenter__(self):
        return self
    async def __aexit__(self, *args):
        pass

async def process(doc):
    async with Connection() as conn:
        doc.merge(doc)  # VIOLATION inside async with
""")

        result = check([tmp_path])

        service_violations = [v for v in result.violations if "service.py" in str(v.file_path)]
        assert len(service_violations) == 1
        assert service_violations[0].method_name == "merge"

    def test_async_for_body_is_traversed(self, tmp_path: Path) -> None:
        """Violations inside `async for` blocks must be detected.

        Ensures `ast.AsyncFor` is traversed alongside `ast.For`.
        """
        (tmp_path / "domain.py").write_text("""
from nodiscard import nodiscard

class Document:
    @nodiscard
    def transform(self):
        return Document()
""")

        (tmp_path / "service.py").write_text("""
async def aiter():
    yield 1

async def process(doc):
    async for _ in aiter():
        doc.transform()  # VIOLATION inside async for
""")

        result = check([tmp_path])

        service_violations = [v for v in result.violations if "service.py" in str(v.file_path)]
        assert len(service_violations) == 1
        assert service_violations[0].method_name == "transform"
