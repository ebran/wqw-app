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


@router.get("/add/{number}", summary="New Fibonacci computation.")
async def add_task(request: Request, number: int) -> Response:
    """Compute a new Fibonacci number.

    Return one active Bootstrap row and one inactive Bootstrap row.
    """
    working_id = unique_string()

    return templates.TemplateResponse(
        "add.html",
        {"request": request, "working_id": working_id, "number": number, "progress": 0},
    )
