"""Shared pytest fixtures and utilities for nodiscard tests."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from nodiscard._collector import ASTMethodCollector
from nodiscard._detector import DetectionContext, ExpressionStatementDetector, _build_method_index
from nodiscard._models import Violation
from nodiscard._type_tracker import LocalTypeTracker


@pytest.fixture
def fixture_dir() -> Path:
    """Return the path to the tests/fixtures/ directory."""
    return Path(__file__).parent / "fixtures"


def check_source(source: str) -> list[Violation]:
    """Parse source and detect violations. Shared test helper."""
    tree = ast.parse(source)
    fp = Path("test.py")
    collector = ASTMethodCollector()
    tracker = LocalTypeTracker()
    detector = ExpressionStatementDetector()
    methods = collector.collect(tree, fp)
    types = tracker.infer_types(tree, fp)
    ctx = DetectionContext(
        tree=tree,
        file_path=fp,
        method_index=_build_method_index(methods),
        all_class_methods={},
        type_scope=types,
        source_lines=tuple(source.splitlines()),
    )
    return detector.detect(ctx)
