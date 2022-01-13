"""
Web app
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse, HTMLResponse

# from devtools import debug

from wqw_app.worker import backend, async_fib


app = FastAPI()


@app.on_event("startup")
async def startup():
    """Startup logic goes here."""
    await backend.init()


@app.on_event("shutdown")
async def shutdown():
    """Shutdown logic goes here."""
    await backend.close()


@app.get("/", summary="Landing page")
def read_root() -> HTMLResponse:
    """Landing page"""
    return HTMLResponse(
        content="""
        <h1>Welcome to the Fibonacci app!</h1>
        <div>Go to the <a href="/docs">docs</a> to get started!</div>""",
        status_code=200,
    )


@app.post("/fib/calc", summary="Calculate a Fibonacci number.")
async def post_task(number: int) -> JSONResponse:
    """Post a calculation task."""

    if job := await backend.enqueue_job(async_fib, number):
        if job_info := await job.info():
            return JSONResponse(
                content={
                    "task_id": job.job_id,
                    "submitted_at": job_info.enqueue_time.strftime("%c"),
                },
                status_code=202,
            )

    return JSONResponse(content={"error": "Failed to enqueue task."}, status_code=500)


@app.get("/fib/results", summary="List of the results from all Fibonacci calculations.")
async def read_task_list() -> JSONResponse:
    """Get list of calculation tasks."""
    return JSONResponse(content=await backend.results(), status_code=200)


@app.get(
    "/fib/results/{task_id}", summary="Result of a particular Fibonacci calculation."
)
def read_task(task_id: int) -> JSONResponse:
    """Get status for a calculation task."""
    return JSONResponse(content={"task_id": task_id}, status_code=200)
