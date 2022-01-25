"""
Worker.
"""
import asyncio
import pickle
import itertools as it
from typing import Optional, TypedDict, Union, Any, Iterator, Dict, cast
from concurrent import futures
from datetime import datetime

import redis
from arq.connections import ArqRedis

from wqw_app.backend import backend
from wqw_app.settings import get_redis_settings

PHI = (1 + 5 ** 0.5) / 2
PSI = (1 - 5 ** 0.5) / 2


class WorkerContext(TypedDict):
    """Context for workers."""

    redis: ArqRedis
    pool: futures.ProcessPoolExecutor
    job_id: str
    job_try: int
    enqueue_time: datetime
    score: int


class FibonacciTracker:
    """Class to track progress of calculating n:th Fibonacci number."""

    def __init__(self, number: int) -> None:
        assert number > 0

        self.number = number
        self.max_iter: int = int(binet(number))
        self.counter: Iterator[int] = it.count(start=2)
        self.progress: float = 0.0

    def __getstate__(self) -> Dict[str, Union[int, float]]:
        """Called on the pickled state."""
        return {
            "number": self.number,
            "max_iter": self.max_iter,
            "current_iter": next(self.counter) - 1,
            "progress": self.progress,
        }

    def __setstate__(self, state: Dict[str, Union[int, float]]) -> None:
        """Called with the unpickled state."""
        self.number = cast(int, state["number"])
        self.max_iter = cast(int, state["max_iter"])
        self.counter = it.count(start=cast(int, state["current_iter"]))
        self.progress = cast(float, state["progress"])

    def __repr__(self) -> str:
        """String representation of class."""
        return (
            f"<Fibonacci calculation of number {self.number} "
            f"currently at {self.progress:.1%}>"
        )

    def countup(self) -> int:
        """Update the counter and return the current iteration number."""
        current_iter = next(self.counter)
        self.progress = current_iter / self.max_iter
        return current_iter


def binet(number: int) -> int:
    """Binet's formula for calculating approximation to n:th Fibonacci number."""
    return int((PHI ** number - PSI ** number) / 5 ** 0.5)


def fib(
    number: int,
    ctx: Optional[Dict[str, Any]] = None,
    tracker: Optional[FibonacciTracker] = None,
    redis_client: Optional[redis.Redis] = None,
) -> int:
    """Fibonacci example function

    Parameters
    ----------
    number : integer
        Compute the number:th Fibonacci number.
    tracker: Optional[FibonacciTracker], default=None
        Tracker to report progress of the recursive computation.

    Returns
    -------
      int: The n-th Fibonacci number
    """
    assert number > 0

    if ctx is None:
        ctx = {}
    if tracker is None:
        tracker = FibonacciTracker(number=number)
    if redis_client is None:
        redis_client = redis.Redis(
            host=cast(str, backend.redis_settings.host),
            port=backend.redis_settings.port,
            db=backend.redis_settings.database,
        )
        print(tracker, end="\r")

    if number < 3:
        return 1

    if tracker.countup() % 10000 == 0:
        redis_client.set(
            f"arq:track:{ctx['job_id']}",
            pickle.dumps(
                {
                    "job_id": ctx["job_id"],
                    "timestamp": datetime.now().strftime("%c"),
                    "progress": round(tracker.progress, ndigits=3),
                }
            ),
        )
        print(f"{tracker}", end="\r")

    return fib(number - 1, ctx, tracker, redis_client) + fib(
        number - 2, ctx, tracker, redis_client
    )


async def async_fib(ctx: WorkerContext, number: int) -> int:
    """Async wrapper around blocking fib function."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        ctx["pool"], fib, number, {"job_id": ctx["job_id"]}
    )


async def startup(ctx: WorkerContext) -> None:
    """Startup logic goes here."""
    ctx["pool"] = futures.ProcessPoolExecutor()


async def shutdown(ctx: WorkerContext) -> None:
    """Startup logic goes here."""
    ctx["pool"].shutdown()


# pylint: disable=too-few-public-methods
class WorkerSettings:
    """Settings for the worker."""

    functions = [async_fib]
    retry_jobs = False
    redis_settings = get_redis_settings()
    allow_abort_jobs = True
    on_startup = startup
    on_shutdown = shutdown
