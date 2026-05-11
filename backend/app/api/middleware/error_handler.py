"""Centralized API error handling middleware."""

from __future__ import annotations

import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.exceptions import AppException

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Convert exceptions into stable JSON error responses."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        """Handle request exceptions from downstream middleware/routes."""
        try:
            return await call_next(request)
        except AppException as exc:
            logger.warning(
                "Handled application error",
                extra={"extra": {"code": exc.code, "path": request.url.path}},
            )
            return JSONResponse(
                status_code=exc.status_code,
                content={"error": {"code": exc.code, "message": exc.message}},
            )
        except SQLAlchemyError:
            logger.exception(
                "Database error",
                extra={"extra": {"path": request.url.path}},
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "database_error",
                        "message": "A database error occurred.",
                    }
                },
            )
        except Exception:
            logger.exception(
                "Unhandled application error",
                extra={"extra": {"path": request.url.path}},
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "internal_server_error",
                        "message": "An unexpected error occurred.",
                    }
                },
            )
