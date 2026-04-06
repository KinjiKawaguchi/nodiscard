"""
No violation fixtures.

This file covers all valid usage patterns (U-cases) for @nodiscard methods.
These should NOT trigger warnings.
"""

from __future__ import annotations

import sys
from contextlib import nullcontext
from typing import TYPE_CHECKING, Iterator

from nodiscard import nodiscard

if TYPE_CHECKING:
    from typing import Self


class Schema:
    """A schema class with @nodiscard methods used correctly."""

    @nodiscard
    def merge(self, other: Schema) -> Schema:
        """Merge with another schema."""
        return self

    @nodiscard
    def validate(self) -> bool:
        """Validate the schema."""
        return True

    @nodiscard
    def transform(self) -> Schema:
        """Transform the schema."""
        return self

    @nodiscard
    async def async_merge(self, other: Schema) -> Schema:
        """Async merge."""
        return self

    @nodiscard
    def get_copy(self) -> Schema:
        """Get a copy."""
        return self

    @nodiscard
    def iter_values(self) -> Iterator[int]:
        """Iterate values."""
        yield 1
        yield 2


def u1_assignment() -> None:
    """U-1: Assignment - result assigned to variable."""
    schema = Schema()
    result = schema.merge(schema)  # OK: assigned
    assert result is not None


def u2_reassignment() -> None:
    """U-2: Reassignment - result assigned to existing variable."""
    schema = Schema()
    result = schema
    result = schema.merge(schema)  # OK: reassigned
    assert result is not None


def u3_return_statement() -> Schema:
    """U-3: Return - result returned from function."""
    schema = Schema()
    return schema.merge(schema)  # OK: returned


def u4_yield_statement() -> Iterator[Schema]:
    """U-4: Yield - result yielded from generator."""
    schema = Schema()
    yield schema.merge(schema)  # OK: yielded


def u5_function_argument() -> bool:
    """U-5: Function argument - result passed to function."""
    schema = Schema()

    def consume(s: Schema) -> bool:
        return True

    return consume(schema.merge(schema))  # OK: func arg


def u6_if_condition() -> None:
    """U-6: If condition - result used in if statement."""
    schema = Schema()
    if schema.validate():  # OK: if condition
        pass


def u7_while_condition() -> None:
    """U-7: While condition - result used in while loop."""
    schema = Schema()
    counter = 0
    while schema.validate() and counter < 1:  # OK: while condition
        counter += 1


def u8_assert_statement() -> None:
    """U-8: Assert - result used in assert."""
    schema = Schema()
    assert schema.validate()  # OK: assert


def u9_list_comprehension() -> list[Schema]:
    """U-9: List comprehension - result used in comprehension."""
    schemas = [Schema() for _ in range(3)]
    return [s.merge(s) for s in schemas]  # OK: list comprehension


def u10_ternary_expression() -> Schema:
    """U-10: Ternary - result used in ternary expression."""
    schema = Schema()
    return schema.merge(schema) if True else schema  # OK: ternary


def u11_tuple_unpacking() -> tuple[Schema, Schema]:
    """U-11: Tuple unpacking - result unpacked from tuple."""
    schema = Schema()
    a, b = schema.merge(schema), schema.merge(schema)  # OK: tuple unpack
    return a, b


def u12_walrus_operator() -> Schema:
    """U-12: Walrus operator - result assigned via walrus."""
    schema = Schema()
    if result := schema.merge(schema):  # OK: walrus
        return result
    return schema


def u13_method_chaining() -> Schema:
    """U-13: Method chaining - result used in chain."""
    schema = Schema()
    return schema.merge(schema).transform()  # OK: chained method call


def u14_await_assignment() -> Schema:
    """U-14: Await assignment - async result assigned."""
    import asyncio

    schema = Schema()

    async def async_operation() -> Schema:
        result = await schema.async_merge(schema)  # OK: await assigned
        return result

    return asyncio.run(async_operation())


def u15_underscore_assignment() -> None:
    """U-15: Underscore assignment - result assigned to _ (discard)."""
    schema = Schema()
    _ = schema.merge(schema)  # OK: explicitly discarded with _


def u16_for_loop_iteration() -> list[Schema]:
    """U-16: For loop iteration - result used in for iterable."""
    schema = Schema()
    results = []
    for value in schema.iter_values():  # OK: for iterable
        results.append(schema.get_copy())
    return results


def u17_with_statement() -> None:
    """U-17: With statement - result used as context manager."""
    schema = Schema()
    with nullcontext(schema.merge(schema)):  # OK: with statement
        pass


def u18_match_statement() -> str:
    """U-18: Match statement - result used in match subject."""
    schema = Schema()
    result = schema.merge(schema)
    match result:  # OK: match subject
        case _:
            return "ok"


def u19_raise_from() -> None:
    """U-19: Raise from - (exception context, not applicable here)."""
    # This is for exception chaining; not directly applicable to nodiscard
    pass


def u20_boolean_operators() -> bool:
    """U-20: Boolean operators - result in and/or expressions."""
    schema = Schema()
    return schema.validate() and True  # OK: boolean op


def u21_list_literal() -> list[Schema]:
    """U-21: List literal - result in list/set/dict literals."""
    schema = Schema()
    return [schema.merge(schema), schema.get_copy()]  # OK: list literal


def u22_f_string() -> str:
    """U-22: F-string - result in f-string."""
    schema = Schema()
    return f"Schema: {schema.merge(schema)}"  # OK: f-string


def u23_subscript_assignment() -> None:
    """U-23: Subscript assignment - result assigned to subscript."""
    schema = Schema()
    data: dict[str, Schema] = {}
    data["key"] = schema.merge(schema)  # OK: subscript assign


def u24_augmented_assignment() -> None:
    """U-24: Augmented assignment - result in += etc."""
    # Not directly applicable; skip


def u25_unary_operation() -> bool:
    """U-25: Unary operation - result in unary op like not."""
    schema = Schema()
    return not schema.validate()  # OK: unary not


def u26_dict_value() -> dict[str, Schema]:
    """U-26: Dict value assignment."""
    schema = Schema()
    return {"key": schema.merge(schema)}  # OK: dict value


def u27_set_literal() -> set[int]:
    """U-27: Set literal."""
    schema = Schema()
    return {1, 2, len(str(schema.merge(schema)))}  # OK: set literal


def u28_isinstance_condition() -> None:
    """U-28: isinstance in condition."""
    schema = Schema()
    obj = schema.merge(schema)
    if isinstance(obj, Schema):  # OK: isinstance
        pass


def u29_comparison() -> bool:
    """U-29: Comparison operators."""
    schema = Schema()
    other = Schema()
    return schema.merge(schema) is other  # OK: comparison


def u30_lambda_return() -> Schema:
    """U-30: Lambda return value used."""
    schema = Schema()
    fn = lambda s: s.merge(s)  # OK: lambda stores function
    return fn(schema)  # OK: fn result assigned


def u31_slice_assignment() -> None:
    """U-31: Slice assignment."""
    schema = Schema()
    lst: list[Schema] = [schema]
    lst[0:1] = [schema.merge(schema)]  # OK: slice assign


def u32_del_statement() -> None:
    """U-32: Not applicable to return values."""
    pass


def u33_isinstance_body() -> None:
    """U-33: Inside isinstance body."""
    schema = Schema()
    obj: object = schema.merge(schema)
    if isinstance(obj, Schema):
        result = obj.validate()  # OK: assigned after narrowing
        assert result


def u34_type_annotation() -> None:
    """U-34: Type annotation doesn't consume value."""
    schema: Schema = Schema()
    result: bool = schema.validate()  # OK: assigned with annotation
    assert result
