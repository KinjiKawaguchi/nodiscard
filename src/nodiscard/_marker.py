"""Runtime marker for @nodiscard decorator and Annotated usage."""

from __future__ import annotations

import functools
from typing import TYPE_CHECKING, TypeVar, overload

if TYPE_CHECKING:
    from collections.abc import Callable

F = TypeVar("F", bound="Callable[..., object]")

NODISCARD_ATTR = "__nodiscard__"


class NoDiscard:
    """Marker for ``Annotated[T, NoDiscard]`` return type annotations.

    Usage::

        from typing import Annotated

        def merge(self, other: Schema) -> Annotated[Schema, NoDiscard]: ...
    """


@overload
def nodiscard(func: F, /) -> F: ...


@overload
def nodiscard(*, reason: str = "") -> Callable[[F], F]: ...


def nodiscard(
    func: F | None = None,
    /,
    *,
    reason: str = "",
) -> F | Callable[[F], F]:
    """Mark a function/method so its return value must not be discarded.

    Can be used as a bare decorator ``@nodiscard`` or
    as a factory ``@nodiscard(reason="...")``.

    Raises ``TypeError`` when applied to a property descriptor.
    """
    def _wrap(fn: F) -> F:
        if isinstance(fn, property):
            msg = "@nodiscard cannot be applied to a property"
            raise TypeError(msg)

        target = fn
        if isinstance(target, (classmethod, staticmethod)):
            inner = target.__func__  # type: ignore[union-attr]
            functools.wraps(inner)(inner)
            setattr(inner, NODISCARD_ATTR, True)
            if reason:
                setattr(inner, "__nodiscard_reason__", reason)
            return fn  # type: ignore[return-value]

        @functools.wraps(target)  # type: ignore[arg-type]
        def wrapper(*args: object, **kwargs: object) -> object:
            return target(*args, **kwargs)  # type: ignore[misc]

        setattr(wrapper, NODISCARD_ATTR, True)
        if reason:
            setattr(wrapper, "__nodiscard_reason__", reason)
        return wrapper  # type: ignore[return-value]

    if func is not None:
        return _wrap(func)
    return _wrap
