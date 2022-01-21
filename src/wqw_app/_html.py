"""Module for Fibonacci computations."""
import json

import httpx

from devtools import debug

from fastapi import APIRouter, Request, Response, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from wqw_app.utils import unique_string

templates = Jinja2Templates(directory="templates")

router = APIRouter()


@router.post("/add", summary="New Fibonacci computation.")
async def add_task(request: Request, number: int = Form(...)) -> Response:
    """Compute a new Fibonacci number.

    Return one in-progress component and one waiting component.
    """
    task_id = unique_string()

    async with httpx.AsyncClient() as client:
        # Post computation to server.
        response = await client.post(
            f"{request.url.scheme}://{request.url.netloc}/api/compute/{number}",
            params={"task_id": task_id},
        )

        data = {}
        try:
            data = response.json()
        except json.JSONDecodeError:
            print("JSON decoding failed")

        assert task_id == data.get("task_id", None)

    return templates.TemplateResponse(
        "partials/add.html",
        {
            "request": request,
            "task_id": task_id,
            "number": number,
            "progress": 0,
        },
    )


@router.get("/in_progress/{task_id}", summary="Get progress for computation.")
async def get_progress(request: Request, task_id: str) -> Response:
    """Get task progress.

    Return one progress component.
    """
    async with httpx.AsyncClient() as client:
        # Get result for task from server.
        response = await client.get(
            f"{request.url.scheme}://{request.url.netloc}/api/results/{task_id}"
        )

        data = {}
        try:
            data = response.json()
        except json.JSONDecodeError:
            print("JSON decoding failed")

        assert data.get("function", None) == "async_fib"

        status = data.get("status", "not_found")
        progress = round(100 * float(data.get("progress", 0)))
        number = data.get("args", [None])[0]
        result = data.get("result")

        responses = {
            "in_progress": templates.TemplateResponse(
                "partials/in_progress.html",
                {
                    "request": request,
                    "task_id": task_id,
                    "number": number,
                    "progress": progress,
                },
            ),
            "complete": templates.TemplateResponse(
                "partials/complete.html",
                {"request": request, "number": number, "result": result},
            ),
            "not_found": templates.TemplateResponse(
                "partials/not_found.html",
                {
                    "request": request,
                    "task_id": task_id,
                    "number": number,
                },
            ),
        }

    return responses.get(status, responses["not_found"])


@router.get("/clear", summary="Return empty response.")
async def clear() -> Response:
    """Return an empty response."""
    return HTMLResponse(content="", status_code=200)


@router.post("/test", summary="Return test message.")
async def test(request: Request) -> Response:
    """Return an empty response."""
    debug(request)
    return HTMLResponse(content="ok", status_code=200)
