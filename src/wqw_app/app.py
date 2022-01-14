"""
Web app.
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from wqw_app import fib
from wqw_app.backend import backend

app = FastAPI()


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


# Add router endpoints
app.include_router(
    fib.router,
    prefix="/fibonacci",
    tags=["Fibonacci"],
)
