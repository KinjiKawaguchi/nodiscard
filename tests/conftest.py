"""Shared pytest fixtures and utilities for nodiscard tests."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest


@pytest.fixture
def fixture_dir() -> Path:
    """Return the path to the tests/fixtures/ directory."""
    return Path(__file__).parent / "fixtures"


def parse_source(source: str) -> ast.Module:
    """Parse a Python source string into an AST Module."""
    return ast.parse(source)
