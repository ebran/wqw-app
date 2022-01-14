"""arq backend module."""
import asyncio
import pickle
from typing import Union, Callable, Optional, Any, Iterable, Tuple, Dict, TypedDict
from datetime import datetime, timedelta
from collections import ChainMap
from dataclasses import asdict

from arq.jobs import Job, JobStatus
from arq.connections import create_pool, ArqRedis, RedisSettings
from arq import constants

from wqw_app.utils import removeprefix, track_progress_key_prefix


class _JobResultDictBase(TypedDict):
    """Required params for job result dict."""

    job_id: str
    status: JobStatus


class JobResultDict(_JobResultDictBase, total=False):
    """Optional params for job result dict."""

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

    async def info(self, job_id: str) -> JobResultDict:
        """Return info on `job_id`."""
        job = Job(job_id=job_id, redis=self.redis_arq)

        if (job_info := await job.info()) and (job_status := await job.status()):
            progress = {}
            if (job_status is JobStatus.in_progress) and (
                progress_data := await self.redis_arq.get(
                    track_progress_key_prefix + job_id, encoding=None
                )
            ):
                progress = pickle.loads(progress_data)

            job_data = dict(
                ChainMap(asdict(job_info), progress),
                job_id=job_id,
                status=job_status.value,
            )

            return JobResultDict(
                **{
                    k: v.strftime("%c") if isinstance(v, datetime) else v
                    for (k, v) in job_data.items()
                }  # type: ignore
            )

        return JobResultDict(job_id=job_id, status=JobStatus.not_found)

    async def info_all(self) -> Iterable[JobResultDict]:
        """Return info for all jobs."""
        job_ids = set()
        for prefix in (
            constants.result_key_prefix,
            constants.job_key_prefix,
            constants.in_progress_key_prefix,
            constants.retry_key_prefix,
        ):
            job_ids.update(
                {
                    removeprefix(key, prefix)
                    for key in await self.redis_arq.keys(f"{prefix}*")
                }
            )

        results = await asyncio.gather(
            *[self.info(job_id=job_id) for job_id in job_ids]
        )

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
