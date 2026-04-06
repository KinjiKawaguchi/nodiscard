"""
Syntax error fixture.

This file intentionally contains a syntax error.
The checker should handle this gracefully (skip file + warning).
"""

from nodiscard import nodiscard


class Model:
    @nodiscard
    def method(self) -> "Model":
        return self

def broken_function(
    # Missing closing parenthesis and colon
