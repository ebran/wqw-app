"""Module for Fibonacci computations."""
from fastapi import APIRouter, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

router = APIRouter()


@router.get("/new", summary="New Fibonacci computation.")
async def new_task() -> Response:
    """Compute a new Fibonacci number.

    Return one active Bootstrap row and one inactive Bootstrap row."""
    return HTMLResponse(content="hello world", status_code=200)
