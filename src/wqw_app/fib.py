"""Module for Fibonacci computations."""
from typing import List, Optional

from pydantic import BaseModel
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from wqw_app.backend import backend, JobResultDict
from wqw_app.worker import async_fib

router = APIRouter()


class ResponseAccepted(BaseModel):
    """Computation was accepted."""

    task_id: str
    submitted_at: str


class ResponseNotAccepted(BaseModel):
    """Computation was not accepted."""

    error: str


@router.post(
    "/compute/{number}",
    summary="Compute a Fibonacci number.",
    responses={
        202: {"description": "Computation was accepted.", "model": ResponseAccepted},
        500: {
            "description": "Computation was not accepted.",
            "model": ResponseNotAccepted,
        },
    },
    tags=["Computations"],
)
async def post_task(number: int, task_id: Optional[str] = None) -> JSONResponse:
    """Post a computation task."""

    if (job := await backend.enqueue_job(async_fib, number, _job_id=task_id)) and (
        job_info := await job.info()
    ):
        return JSONResponse(
            content={
                "task_id": job.job_id,
                "submitted_at": job_info.enqueue_time.strftime("%c"),
            },
            status_code=202,
        )

    return JSONResponse(content={"error": "Failed to enqueue task."}, status_code=500)


@router.get(
    "/results",
    summary="Results from all Fibonacci computation.",
    responses={
        200: {
            "description": "All Fibonacci computation tasks.",
            "model": List[JobResultDict],
        }
    },
    tags=["Results"],
)
async def read_task_list() -> JSONResponse:
    """Get list of calculation tasks."""
    return JSONResponse(content=await backend.info_all(), status_code=200)


@router.get(
    "/results/{task_id}",
    summary="Result from a particular Fibonacci computation.",
    responses={
        200: {"description": "Fibonacci computation task.", "model": JobResultDict}
    },
    tags=["Results"],
)
async def read_task(task_id: str) -> JSONResponse:
    """Get status for a calculation task."""
    return JSONResponse(content=await backend.info(job_id=task_id), status_code=200)
