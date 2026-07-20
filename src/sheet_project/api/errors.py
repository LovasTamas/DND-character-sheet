"""Uniform API error type + the `{"error": {...}}` body shape.

Every 4xx/5xx response produced by this API (including FastAPI's own
`RequestValidationError`) is normalized to this shape by the exception
handlers registered in `main.py`.
"""
from __future__ import annotations

from typing import Any, Optional


class ApiError(Exception):
    """Raised by route handlers to produce a structured JSON error response."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        field: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.field = field


def error_body(code: str, message: str, field: Optional[str] = None) -> dict:
    return {"error": {"code": code, "message": message, "field": field}}


def not_found(message: str, code: str = "not_found", field: Optional[str] = None) -> ApiError:
    return ApiError(404, code, message, field)


def bad_request(message: str, code: str = "bad_request", field: Optional[str] = None) -> ApiError:
    return ApiError(400, code, message, field)


def conflict(message: str, code: str = "conflict", field: Optional[str] = None) -> ApiError:
    return ApiError(409, code, message, field)
