"""Fibonacci calculator

Welcome to the world's greatest.
"""
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.templating import Jinja2Templates

from wqw_app import api, __version__ as version, frontend
from wqw_app.backend import backend


app = FastAPI(
    title="Fibonacci calculator",
    openapi_url=None,
    docs_url=None,
    redoc_url=None,
)

app.mount("/static", StaticFiles(directory="static"), name="static")

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
    "/", summary="Landing page", include_in_schema=False, response_class=HTMLResponse
)
def fibonacci_calculator(request: Request) -> Response:
    """Landing page"""
    return templates.TemplateResponse("index.html", {"request": request})


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
    openapi_schema["paths"]["/api/cancel/{task_id}"]["post"]["responses"].pop(
        "200", None
    )
    openapi_schema["paths"]["/api/cancel/{task_id}"]["post"]["responses"].pop(
        "422", None
    )
    openapi_schema["paths"]["/api/results"]["get"]["responses"].pop("422", None)
    openapi_schema["paths"]["/api/results/{task_id}"]["get"]["responses"].pop(
        "422", None
    )

    return openapi_schema


# Add fibonacci endpoints
# JSON API
app.include_router(api.router, prefix="/api")

# HTML frontend endpoints
app.include_router(
    frontend.router,
    prefix="/frontend",
    include_in_schema=False,
    default_response_class=HTMLResponse,
)
