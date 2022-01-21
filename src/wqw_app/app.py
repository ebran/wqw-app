"""Fibonacci calculator

Welcome to the world's greatest.
"""
import logging

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError

from wqw_app import _html, fib, __version__ as version
from wqw_app.backend import backend
from wqw_app.utils import unique_string


app = FastAPI(
    title="Fibonacci calculator",
    openapi_url=None,
    docs_url=None,
    redoc_url=None,
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Debug ValidationError"""
    exc_str = f"{exc}".replace("\n", " ").replace("   ", " ")
    logging.error(f"{request}: {exc_str}")
    content = {"status_code": 10422, "message": exc_str, "data": None}
    return JSONResponse(
        content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )


templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
async def startup():
    """Startup logic goes here."""
    await backend.init()


@app.on_event("shutdown")
async def shutdown():
    """Shutdown logic goes here."""
    await backend.close()


@app.get(
    "/components",
    summary="Components",
    include_in_schema=False,
    response_class=HTMLResponse,
)
def components(request: Request) -> Response:
    """Landing page"""
    task_id = unique_string()

    return templates.TemplateResponse(
        "components.html",
        {
            "request": request,
            "task_id": task_id,
            "number": 42,
            "progress": 45,
            "result": 12345678,
        },
    )


@app.get(
    "/", summary="Landing page", include_in_schema=False, response_class=HTMLResponse
)
def fibonacci_calculator(request: Request) -> Response:
    """Landing page"""
    task_id = unique_string()

    return templates.TemplateResponse(
        "index.html", {"request": request, "task_id": task_id}
    )


@app.get(
    "/docs",
    include_in_schema=False,
)
def get_documentation():
    """Endpoint for docs."""
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=__doc__.splitlines()[0] if __doc__ else "",
    )


@app.get(
    "/openapi.json",
    include_in_schema=False,
)
def openapi():
    """Endpoint for OpenAPI specs."""
    openapi_schema = get_openapi(
        title=__doc__.splitlines()[0] if __doc__ else "",
        description="\n".join(__doc__.splitlines()[1:]) if __doc__ else "",
        version=version,
        routes=app.routes,
    )

    openapi_schema["paths"]["/api/compute/{number}"]["post"]["responses"].pop(
        "200", None
    )
    openapi_schema["paths"]["/api/compute/{number}"]["post"]["responses"].pop(
        "422", None
    )
    openapi_schema["paths"]["/api/results"]["get"]["responses"].pop("422", None)
    openapi_schema["paths"]["/api/results/{task_id}"]["get"]["responses"].pop(
        "422", None
    )

    return openapi_schema


# Add router endpoints
# JSON API
app.include_router(fib.router, prefix="/api")

# HTML endpoints
app.include_router(
    _html.router,
    prefix="/_html",
    include_in_schema=False,
    default_response_class=HTMLResponse,
)
