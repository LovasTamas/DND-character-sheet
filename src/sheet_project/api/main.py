"""FastAPI application: CORS, exception handlers, router registration,
and (optionally) serving the built webui as static files.

Run with:
    PYTHONPATH=src uvicorn sheet_project.api.main:app --reload
"""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.staticfiles import StaticFiles

from .config import settings
from .errors import ApiError, error_body
from .routes import catalog, characters, mutations

logger = logging.getLogger("sheet_project.api")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="D&D Character Sheet API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    if exc.status_code >= 500:
        logger.error("500 error on %s %s: %s", request.method, request.url.path, exc.message)
    else:
        logger.warning(
            "%s error on %s %s: %s", exc.status_code, request.method, request.url.path, exc.message
        )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(exc.code, exc.message, exc.field),
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    first = errors[0] if errors else {}
    field = ".".join(str(part) for part in first.get("loc", []) if part not in ("body", "query", "path"))
    message = first.get("msg", "Invalid request.")
    logger.warning("400 validation error on %s %s: %s", request.method, request.url.path, message)
    return JSONResponse(
        status_code=400,
        content=error_body("validation_error", message, field or None),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception on %s %s", request.method, request.url.path, exc_info=exc)
    return JSONResponse(
        status_code=500,
        content=error_body("internal_error", "An unexpected error occurred."),
    )


API_PREFIX = "/api/v1"
app.include_router(catalog.router, prefix=API_PREFIX)
app.include_router(characters.router, prefix=API_PREFIX)
app.include_router(mutations.router, prefix=API_PREFIX)


# Optional: serve the built frontend (webui/dist) if it exists, mounted at
# "/" AFTER the API routers so /api/v1/* always wins.
_webui_dist = Path(__file__).resolve().parents[3] / "webui" / "dist"
if _webui_dist.is_dir():
    app.mount("/", StaticFiles(directory=str(_webui_dist), html=True), name="webui")
