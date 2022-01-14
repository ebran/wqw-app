"""Fibonacci calculator

Welcome to the world's greatest.
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html

from wqw_app import fib, __version__ as version
from wqw_app.backend import backend

app = FastAPI(
    title="Fibonacci calculator",
    version=version,
    openapi_url=None,
    docs_url=None,
    redoc_url=None,
)


@app.on_event("startup")
async def startup():
    """Startup logic goes here."""
    await backend.init()


@app.on_event("shutdown")
async def shutdown():
    """Shutdown logic goes here."""
    await backend.close()


@app.get("/", summary="Landing page", include_in_schema=False)
def read_root() -> HTMLResponse:
    """Landing page"""
    return HTMLResponse(
        content="""
        <h1>Welcome to the Fibonacci app!</h1>
        <div>Go to the <a href="/docs">docs</a> to get started!</div>""",
        status_code=200,
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

    openapi_schema["paths"]["/fibonacci/compute"]["post"]["responses"].pop("200", None)
    openapi_schema["paths"]["/fibonacci/compute"]["post"]["responses"].pop("422", None)
    openapi_schema["paths"]["/fibonacci/results"]["get"]["responses"].pop("422", None)
    openapi_schema["paths"]["/fibonacci/results/{task_id}"]["get"]["responses"].pop(
        "422", None
    )

    return openapi_schema


# Add router endpoints
app.include_router(
    fib.router,
    prefix="/fibonacci",
)
