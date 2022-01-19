"""Module for Fibonacci computations."""
from fastapi import APIRouter, Request, Response
from fastapi.templating import Jinja2Templates

from wqw_app.utils import unique_string

templates = Jinja2Templates(directory="templates")

router = APIRouter()


@router.get("/add", summary="New Fibonacci computation.")
async def add_task(request: Request) -> Response:
    """Compute a new Fibonacci number.

    Return one active Bootstrap row and one inactive Bootstrap row.
    """
    working_id = unique_string()

    return templates.TemplateResponse(
        "add.html", {"request": request, "working_id": working_id}
    )
