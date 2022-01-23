"""Module for Fibonacci computations."""
import json
from typing import Optional

import httpx

from fastapi import APIRouter, Request, Response, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from wqw_app import api

templates = Jinja2Templates(directory="templates")

router = APIRouter()


@router.post("/add", summary="New Fibonacci computation.")
async def add_task(request: Request, number: int = Form(...)) -> Response:
    """Compute a new Fibonacci number.

    Return one in-progress component and one waiting component.
    """
    async with httpx.AsyncClient() as client:
        # Post computation to server.
        response = await client.post(
            request.url_for(api.post_task.__name__, number=number)
        )

        data = {}
        try:
            data = response.json()
        except json.JSONDecodeError:
            print("JSON decoding failed")

        task_id = data.get("task_id")

    return templates.TemplateResponse(
        "partials/add.html",
        {
            "request": request,
            "task_id": task_id,
            "number": number,
            "progress": 0,
        },
    )


@router.get("/status/{task_id}", summary="Get computation status.")
async def get_progress(request: Request, task_id: str) -> Response:
    """Get task status.

    Return in_progress, completed, or error="not found" component.
    """
    async with httpx.AsyncClient() as client:
        # Get result for task from server.
        response = await client.get(
            request.url_for(api.read_task.__name__, task_id=task_id)
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
                "partials/error.html",
                {
                    "request": request,
                    "number": number,
                    "task_id": task_id,
                    "error": "not found",
                },
            ),
        }

    return responses.get(status, responses["not_found"])


@router.post("/cancel/{task_id}", summary="Get computation status.")
async def cancel(
    request: Request,
    task_id: str,
    timeout: Optional[float] = None,
    poll_delay: float = 0.5,
) -> Response:
    """Cancel task.

    Return error="cancelled" component.
    """
    async with httpx.AsyncClient() as client:
        # Get result for task from server.
        response = await client.get(
            request.url_for(api.read_task.__name__, task_id=task_id)
        )

        data = {}
        try:
            data = response.json()
        except json.JSONDecodeError:
            print("JSON decoding failed")

        number = data.get("args", [None])[0]

        # Post cancel task to server.
        params = {"poll_delay": poll_delay}
        if timeout:
            params["timeout"] = timeout
        response = await client.post(
            request.url_for(api.cancel_task.__name__, task_id=task_id), params=params
        )

        data = {}
        try:
            data = response.json()
        except json.JSONDecodeError:
            print("JSON decoding failed")

        success = data.get("cancelled", False)

    return templates.TemplateResponse(
        "partials/error.html",
        {
            "request": request,
            "number": number,
            "task_id": task_id,
            "error": "cancelled" if success else "failed to cancel",
        },
    )


@router.get("/clear", summary="Return empty response.")
async def clear() -> Response:
    """Return an empty response."""
    return HTMLResponse(content="", status_code=200)
