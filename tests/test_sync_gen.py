import asyncio
from typing import AsyncGenerator
from alist.sync import Sync


class MockAsyncClass:
    async def async_gen(self, n: int) -> AsyncGenerator[int, None]:
        for i in range(n):
            yield i


class MockSyncClass(Sync[MockAsyncClass]):
    ASYNC_CLASS = MockAsyncClass


def test_sync_generator_proxy():
    sync_obj = MockSyncClass()
    # Test that the generator works in sync mode
    results = list(sync_obj.async_gen(5))
    assert results == [0, 1, 2, 3, 4]


class MockAsyncClassWithCoroutine:
    async def async_func(self, x: int) -> int:
        return x * 2


class MockSyncClassWithCoroutine(Sync[MockAsyncClassWithCoroutine]):
    ASYNC_CLASS = MockAsyncClassWithCoroutine


def test_sync_function_proxy():
    sync_obj = MockSyncClassWithCoroutine()
    assert sync_obj.async_func(10) == 20
