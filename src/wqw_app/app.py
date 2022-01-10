"""
Web app
"""
from dataclasses import asdict
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# from devtools import debug

from wqw_app.worker import backend, fibonacci


app = FastAPI()


@app.on_event("startup")
async def startup():
    """Startup logic goes here."""
    await backend.init()


@app.on_event("shutdown")
async def shutdown():
    """Shutdown logic goes here."""
    await backend.close()


@app.get("/")
def read_root() -> JSONResponse:
    """Root"""
    return JSONResponse(content={"Hello": "World"}, status_code=200)


@app.post("/fib")
async def post_task(number: int) -> JSONResponse:
    """Post a calculation task."""

    if job := await backend.redis.enqueue_job(fibonacci.__name__, number):
        if job_info := await job.info():
            return JSONResponse(
                content={
                    "task_id": job.job_id,
                    "submitted_at": job_info.enqueue_time.strftime("%c"),
                },
                status_code=200,
            )

    return JSONResponse(content={"error": "Failed to enqueue task."}, status_code=500)


@app.get("/fib")
async def read_task_list() -> JSONResponse:
    """Get list of calculation tasks."""
    task_list = []
    for task in await backend.redis.queued_jobs():
        task_dict = asdict(task)
        task_dict["submitted_at"] = task_dict.pop("enqueue_time").strftime("%c")
        task_list.append(task_dict)

    return JSONResponse(content=task_list, status_code=200)


@app.get("/fib/{task_id}")
def read_task(task_id: int) -> JSONResponse:
    """Get status for a calculation task."""
    return JSONResponse(content={"task_id": task_id}, status_code=200)
