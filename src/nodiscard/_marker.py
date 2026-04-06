"""Runtime marker for @nodiscard decorator and Annotated usage."""

from __future__ import annotations

import functools
from typing import TYPE_CHECKING, TypeVar, overload

if TYPE_CHECKING:
    from collections.abc import Callable

F = TypeVar("F", bound="Callable[..., object]")

NODISCARD_ATTR = "__nodiscard__"
_REASON_ATTR = "__nodiscard_reason__"


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

    Can be used as ``@nodiscard`` or ``@nodiscard(reason="...")``.

    Raises ``TypeError`` when applied to a property descriptor.
    """
    def _wrap(fn: F) -> F:
        if isinstance(fn, property):
            msg = "@nodiscard cannot be applied to a property"
            raise TypeError(msg)

        if isinstance(fn, (classmethod, staticmethod)):
            _set_marker_on_descriptor(fn, reason)
            return fn

        return _wrap_and_mark(fn, reason)

    if func is not None:
        return _wrap(func)
    return _wrap


def _set_marker_on_descriptor(
    desc: classmethod | staticmethod,  # type: ignore[type-arg]
    reason: str,
) -> None:
    """Set the nodiscard marker on the inner function of a descriptor.

    classmethod/staticmethod store the real function in ``__func__``.
    Python's type system cannot express the generic parameter of these
    descriptors without knowing the wrapped function's signature.
    """
    inner = desc.__func__
    setattr(inner, NODISCARD_ATTR, True)
    if reason:
        setattr(inner, _REASON_ATTR, reason)


def _wrap_and_mark(fn: F, reason: str) -> F:
    """Wrap a regular function, preserving metadata, and set the marker.

    ``functools.wraps`` expects a concrete callable but ``F`` is a TypeVar
    bound to ``Callable[..., object]``. The wrapper is structurally
    identical to ``fn`` at runtime; the mismatch is purely in the
    type-checker's model of higher-kinded callable types.
    """
    @functools.wraps(fn)  # type: ignore[arg-type]
    def wrapper(*args: object, **kwargs: object) -> object:
        return fn(*args, **kwargs)

    setattr(wrapper, NODISCARD_ATTR, True)
    if reason:
        setattr(wrapper, _REASON_ATTR, reason)
    return wrapper  # type: ignore[return-value]
