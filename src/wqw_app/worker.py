"""
Worker.
"""
import asyncio
import itertools as it
from typing import List, Optional, TypedDict, Union, Any, Callable, Iterator
from concurrent import futures
from datetime import datetime, timedelta

from arq.jobs import Job, JobDef
from arq.constants import default_queue_name
from arq.connections import create_pool, RedisSettings, ArqRedis

PHI = (1 + 5 ** 0.5) / 2
PSI = (1 - 5 ** 0.5) / 2


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

    async def enqueue_job(
        self,
        function: Union[str, Callable],
        *args: Any,
        _job_id: Optional[str] = None,
        _queue_name: Optional[str] = None,
        _defer_until: Optional[datetime] = None,
        _defer_by: Union[None, int, float, timedelta] = None,
        _expires: Union[None, int, float, timedelta] = None,
        _job_try: Optional[int] = None,
        **kwargs: Any,
    ) -> Optional[Job]:
        """Enqueue a job"""
        assert isinstance(function, (str, Callable))
        if isinstance(function, Callable):
            function = function.__name__

        return await self.redis.enqueue_job(
            function,
            *args,
            _job_id=_job_id,
            _queue_name=_queue_name,
            _defer_until=_defer_until,
            _defer_by=_defer_by,
            _expires=_expires,
            _job_try=_job_try,
            **kwargs,
        )

    async def queued_jobs(
        self, *, queue_name: str = default_queue_name
    ) -> List[JobDef]:
        """List of queued jobs."""
        return await self.redis.queued_jobs(queue_name=queue_name)

    @property
    def redis(self):
        """Return the redis connection."""
        if self._redis is None:
            raise RuntimeError("Fatal: No redis connection.")
        return self._redis


backend = Backend()


class WorkerContext(TypedDict):
    """Context for workers."""

    backend: Backend


class FibonacciTracker:
    """Class to track progress of calculating n:th Fibonacci number."""

    def __init__(self, start: int = 0, max_iterations: int = 1) -> None:
        self.counter: Iterator[int] = it.count(start=start)
        self.max_iterations: int = max_iterations
        self.progress: float = 0.0

    def countup(self) -> int:
        """Update the counter and return the current iteration number."""
        current_iter = next(self.counter)
        self.progress = current_iter / self.max_iterations
        return current_iter

    def __repr__(self) -> str:
        """String representation of class."""
        return f"<Fibonacci calculation of number {self.max_iterations} at {self.progress:.2%}>"


def binet(number: int) -> int:
    """Binet's formula for calculating approximation to n:th Fibonacci number."""
    return int((PHI ** number - PSI ** number) / 5 ** 0.5)


def fib(
    ctx: Optional[WorkerContext],
    number: int,
    tracker: Optional[FibonacciTracker] = None,
) -> int:
    """Fibonacci example function

    Parameters
    ----------
    ctx: WorkerContext (optional)
        Optional dictionary that holds state for the worker.
    number : integer
        Compute the number:th Fibonacci number.
    tracker: Optional[FibonacciTracker], default=None
        Tracker to report progress of the recursive computation.

    Returns
    -------
      int: The n-th Fibonacci number
    """
    assert number > 0

    if tracker is None:
        tracker = FibonacciTracker(start=2, max_iterations=int(binet(number)))
        print(tracker, end="\r")

    if number < 3:
        return 1

    if tracker.countup() % 1000 == 0:
        print(tracker, end="\r")

    return fib(ctx, number - 1, tracker) + fib(ctx, number - 2, tracker)


async def async_fib(ctx: Optional[WorkerContext], number: int) -> int:
    """Async wrapper around blocking fib function."""
    loop = asyncio.get_running_loop()

    with futures.ProcessPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, fib, ctx, number)

    return result


async def startup(ctx: WorkerContext) -> None:
    """Startup logic goes here."""
    ctx["backend"] = backend


# WorkerSettings defines the settings to use when creating the work,
# it's used by the arq cli
# pylint: disable=too-few-public-methods
class WorkerSettings:
    """Settings for the worker."""

    functions = [async_fib]
    on_startup = startup
    # on_shutdown = shutdown
