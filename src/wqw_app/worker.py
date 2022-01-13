"""
Worker.
"""
import asyncio
import pickle
import itertools as it
from typing import (
    List,
    Optional,
    TypedDict,
    Union,
    Any,
    Callable,
    Iterator,
    Tuple,
    Dict,
    cast,
)
from concurrent import futures
from datetime import datetime, timedelta
from dataclasses import fields

import redis

from arq.connections import create_pool, ArqRedis, RedisSettings
from arq.jobs import Job
from arq.constants import result_key_prefix

from wqw_app.utils import removeprefix

PHI = (1 + 5 ** 0.5) / 2
PSI = (1 - 5 ** 0.5) / 2


class TaskResult(TypedDict):
    """Result of a finished task."""

    function: str
    args: Tuple[Any, ...]
    kwargs: Dict[Any, Any]
    job_try: int
    enqueue_time: str
    score: Optional[int]
    success: bool
    result: Any
    start_time: str
    finish_time: str
    queue_name: str
    job_id: str


class Backend:
    """arq backend."""

    def __init__(self, redis_settings: RedisSettings = None):
        self._redis_settings: RedisSettings = (
            redis_settings if redis_settings is not None else RedisSettings()
        )
        self._redis_arq: Optional[ArqRedis] = None

    async def init(self):
        """Initialize connection pools to the backend."""
        self._redis_arq = await create_pool(self._redis_settings)

    async def close(self):
        """Close the connection pools to the backend."""
        self.redis_arq.close()
        await self.redis_arq.wait_closed()

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

        return await self.redis_arq.enqueue_job(
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

    async def results(self) -> List[Optional[TaskResult]]:
        """Return all results."""
        results = []
        for key in await self.redis_arq.keys(f"{result_key_prefix}*"):
            job_id = removeprefix(key, prefix=result_key_prefix)
            job = Job(job_id=job_id, redis=backend.redis_arq)

            if info := await job.info():
                results.append(
                    dict(
                        {
                            key: val.strftime("%c")
                            if isinstance(val, datetime)
                            else val
                            for field in fields(info)
                            if (key := field.name) and (val := getattr(info, key))
                        },  # type: ignore
                        job_id=job_id,
                    )
                )
            else:
                results.append(None)

        return results

    @property
    def redis_arq(self):
        """Return the redis connection."""
        if self._redis_arq is None:
            raise RuntimeError("Fatal: No async redis connection.")
        return self._redis_arq

    @property
    def redis_settings(self):
        """Return the redis settings."""
        if self._redis_settings is None:
            raise RuntimeError("Fatal: Could not obtain redis settings.")
        return self._redis_settings


backend = Backend()


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
    on_startup = startup
    on_shutdown = shutdown
