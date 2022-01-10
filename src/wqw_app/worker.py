"""
Worker.
"""
import asyncio
from typing import Optional, TypedDict
from concurrent import futures

from arq.connections import create_pool, RedisSettings, ArqRedis

from devtools import debug


class WorkerContext(TypedDict):
    """Context for workers."""

    job_id: str


# async def startup(ctx):
#     """Startup logic goes here."""
#     pass


# async def shutdown(ctx):
#     """Shutdown logic goes here."""
#     pass


class Backend:
    """arq backend."""

    def __init__(self):
        self._redis: Optional[ArqRedis] = None

    async def init(self):
        """Initialize a connection pool to the backend."""
        self._redis = await create_pool(RedisSettings())

    async def close(self):
        """Close the connection pool to the backend."""
        self.redis.close()
        await self.redis.wait_closed()

    @property
    def redis(self):
        """Return the redis connection."""
        if self._redis is None:
            raise RuntimeError("Fatal: No redis connection.")
        return self._redis


def fib(number: int) -> int:
    """Fibonacci example function

    Args:
      n (int): integer

    Returns:
      int: n-th Fibonacci number
    """
    assert number > 0

    if number < 3:
        return 1
    return fib(number - 1) + fib(number - 2)


# pylint: disable=unused-argument
async def fibonacci(ctx: Optional[WorkerContext], number: int) -> int:
    """Async wrapper around fib function."""
    loop = asyncio.get_running_loop()

    with futures.ProcessPoolExecutor() as pool:
        print(f"Context is {ctx}")
        result = await loop.run_in_executor(pool, fib, number)

    return result


# WorkerSettings defines the settings to use when creating the work,
# it's used by the arq cli
# pylint: disable=too-few-public-methods
class WorkerSettings:
    """Settings for the worker."""

    functions = [fibonacci]
    # on_startup = startup
    # on_shutdown = shutdown


backend = Backend()
