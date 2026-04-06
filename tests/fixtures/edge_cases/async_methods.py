"""
Async method patterns.

Tests async @nodiscard methods and await patterns.
"""

import asyncio

from nodiscard import nodiscard


class AsyncSchema:
    """Schema with async @nodiscard methods."""

    def __init__(self, data: str = "") -> None:
        """Initialize."""
        self._data = data

    @nodiscard
    async def merge_async(self, other: "AsyncSchema") -> "AsyncSchema":
        """Asynchronously merge. Return value must not be discarded."""
        await asyncio.sleep(0)
        return self

    @nodiscard
    async def validate_async(self) -> bool:
        """Asynchronously validate."""
        await asyncio.sleep(0)
        return True

    async def process_async(self) -> None:
        """Process asynchronously (no @nodiscard)."""
        await asyncio.sleep(0)


async def test_async_violation() -> None:
    """Test async method with violation."""
    schema = AsyncSchema("test")

    # VIOLATION: async result discarded without await
    schema.merge_async(schema)  # noqa: F704

    # VIOLATION: await but result discarded
    await schema.merge_async(schema)  # VIOLATION 1


async def test_async_correct_usage() -> None:
    """Test correct async usage."""
    schema = AsyncSchema("test")

    # OK: awaited and assigned
    result = await schema.merge_async(schema)
    assert result is not None

    # OK: awaited and used
    if await schema.validate_async():
        pass


async def test_async_in_gather() -> None:
    """Test async methods in asyncio.gather."""
    schema1 = AsyncSchema("a")
    schema2 = AsyncSchema("b")

    # OK: results gathered
    results = await asyncio.gather(
        schema1.merge_async(schema2),
        schema2.merge_async(schema1),
    )
    assert len(results) == 2


async def test_async_in_task() -> None:
    """Test async methods in asyncio.create_task."""
    schema = AsyncSchema("test")

    # OK: task is created and assigned
    task = asyncio.create_task(schema.merge_async(schema))
    result = await task
    assert result is not None


async def test_async_violation_in_task() -> None:
    """Test violation in async task."""
    schema = AsyncSchema("test")

    # VIOLATION: task result discarded without await
    asyncio.create_task(schema.merge_async(schema))


async def test_async_in_for_loop() -> None:
    """Test async methods in loop."""
    schemas = [AsyncSchema(f"s{i}") for i in range(3)]

    # OK: results collected
    results = []
    for schema in schemas:
        result = await schema.merge_async(schema)
        results.append(result)

    assert len(results) == 3


async def test_async_violation_in_loop() -> None:
    """Test async violation in loop."""
    schemas = [AsyncSchema(f"s{i}") for i in range(3)]

    for schema in schemas:
        # VIOLATION: awaited but result discarded
        await schema.merge_async(schema)  # VIOLATION 2


async def test_async_chaining() -> None:
    """Test async method chaining."""
    schema = AsyncSchema("initial")

    # VIOLATION: chain result discarded
    await schema.merge_async(schema).merge_async(schema)  # type: ignore


def test_async_without_await() -> None:
    """Test async methods without await (creates coroutine)."""
    schema = AsyncSchema("test")

    # Not technically a violation of @nodiscard, but the coroutine is discarded
    # This test demonstrates the difference between calling async vs. awaiting
    coro = schema.merge_async(schema)
    assert coro is not None  # OK: coroutine assigned
    coro.close()  # Clean up


def test_sync_and_async_mixed() -> None:
    """Mix sync and async in context."""

    class MixedSchema:
        def __init__(self) -> None:
            self.data = ""

        @nodiscard
        def sync_process(self) -> "MixedSchema":
            return self

        @nodiscard
        async def async_process(self) -> "MixedSchema":
            await asyncio.sleep(0)
            return self

    schema = MixedSchema()

    # VIOLATION: sync method
    schema.sync_process()  # VIOLATION 3


async def test_async_context_manager() -> None:
    """Test async context manager with @nodiscard (edge case)."""

    class AsyncContextManager:
        async def __aenter__(self) -> "AsyncContextManager":
            return self

        async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
            pass

        @nodiscard
        async def process(self) -> "AsyncContextManager":
            return self

    async with AsyncContextManager() as ctx:
        # VIOLATION: result discarded
        await ctx.process()  # VIOLATION 4
