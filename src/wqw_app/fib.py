"""Module for Fibonacci computations."""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from wqw_app.backend import backend
from wqw_app.worker import async_fib

router = APIRouter()


@router.post("/compute", summary="Compute a Fibonacci number.")
async def post_task(number: int) -> JSONResponse:
    """Post a computation task."""

    if (job := await backend.enqueue_job(async_fib, number)) and (
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


@router.get("/results", summary="Results from all Fibonacci computation.")
async def read_task_list() -> JSONResponse:
    """Get list of calculation tasks."""
    return JSONResponse(content=await backend.info_all(), status_code=200)


@router.get(
    "/results/{task_id}", summary="Result from a particular Fibonacci computation."
)
async def read_task(task_id: str) -> JSONResponse:
    """Get status for a calculation task."""
    return JSONResponse(content=await backend.info(job_id=task_id), status_code=200)
