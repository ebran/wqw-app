"""
Web app
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()


@app.get("/")
def read_root() -> JSONResponse:
    """Root"""
    return JSONResponse(content={"Hello": "World"}, status_code=200)


@app.get("/tasks/{task_id}")
def read_item(task_id: int) -> JSONResponse:
    """Get task."""
    return JSONResponse(content={"task_id": task_id}, status_code=200)
