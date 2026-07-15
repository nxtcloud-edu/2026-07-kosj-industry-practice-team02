"""Metadata-only HTTP logging and Uvicorn log safety boundaries."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from uuid import UUID, uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

_LOGGER_NAME = "sejong_ai_api.request"
_FALLBACK_REQUEST_ID = "00000000-0000-0000-0000-000000000000"
_GENERIC_ERROR_MESSAGE = "Unhandled application error"
_UNSAFE_UVICORN_WEBSOCKET_MESSAGES = frozenset(
    {
        '%s - "WebSocket %s" [accepted]',
        '%s - "WebSocket %s" 403',
        '%s - "WebSocket %s" %d',
    }
)
_ALLOWED_METHODS = frozenset(
    {"CONNECT", "DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT", "TRACE"}
)


def _safe_request_id(value: object) -> str:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, str):
        try:
            return str(UUID(value))
        except ValueError:
            pass
    return _FALLBACK_REQUEST_ID


def _safe_method(value: object) -> str:
    if isinstance(value, str) and value in _ALLOWED_METHODS:
        return value
    return "UNKNOWN"


def _safe_path(value: object) -> str:
    if value == "<unmatched>":
        return "<unmatched>"
    if (
        isinstance(value, str)
        and value.startswith("/")
        and len(value) <= 256
        and "?" not in value
        and "#" not in value
    ):
        return value
    return "<unmatched>"


def _safe_status(value: object) -> int:
    if type(value) is int and 100 <= value <= 599:
        return value
    return 500


class SafeRequestJsonFormatter(logging.Formatter):
    """Serialize exactly the request metadata allowlist without formatting the message."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "request_id": _safe_request_id(record.__dict__.get("request_id")),
            "method": _safe_method(record.__dict__.get("method")),
            "path": _safe_path(record.__dict__.get("path")),
            "status": _safe_status(record.__dict__.get("status")),
        }
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


class SafeExceptionFilter(logging.Filter):
    """Drop unsafe protocol detail and sanitize exception-derived content."""

    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelno < logging.INFO:
            return False
        if isinstance(record.msg, str) and record.msg in _UNSAFE_UVICORN_WEBSOCKET_MESSAGES:
            return False
        if (
            record.exc_info is not None
            or record.exc_text is not None
            or record.stack_info is not None
        ):
            record.msg = _GENERIC_ERROR_MESSAGE
            record.args = ()
            record.exc_info = None
            record.exc_text = None
            record.stack_info = None
        return True


def configure_uvicorn_log_safety() -> None:
    """Block unsafe Uvicorn records and sanitize exception-derived content."""
    for unsafe_logger_name in ("uvicorn.access", "uvicorn.asgi"):
        unsafe_logger = logging.getLogger(unsafe_logger_name)
        unsafe_logger.disabled = True
        unsafe_logger.propagate = False

    error_logger = logging.getLogger("uvicorn.error")
    error_logger.disabled = False
    if not any(isinstance(item, SafeExceptionFilter) for item in error_logger.filters):
        error_logger.addFilter(SafeExceptionFilter())


def get_safe_request_logger() -> logging.Logger:
    """Return the single-handler metadata logger used by the application."""
    configure_uvicorn_log_safety()
    logger = logging.getLogger(_LOGGER_NAME)
    logger.disabled = False
    logger.setLevel(logging.INFO)
    logger.propagate = False

    safe_handlers = [
        handler
        for handler in logger.handlers
        if isinstance(handler.formatter, SafeRequestJsonFormatter)
    ]
    for handler in tuple(logger.handlers):
        if handler not in safe_handlers[:1]:
            logger.removeHandler(handler)
    if not safe_handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(SafeRequestJsonFormatter())
        logger.addHandler(handler)
    return logger


def _route_template(scope: Scope) -> str:
    route = scope.get("route")
    template = getattr(route, "path", None)
    return _safe_path(template)


class SafeRequestLoggingMiddleware:
    """Log one safe metadata record per HTTP request without consuming its receive channel."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        logger: logging.Logger,
        request_id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._application = app
        self._logger = logger
        self._request_id_factory = request_id_factory

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        is_http = scope.get("type") == "http"
        status = 500

        async def send_with_status(message: Message) -> None:
            nonlocal status
            if message.get("type") == "http.response.start":
                status = _safe_status(message.get("status"))
            await send(message)

        downstream_send = send_with_status if is_http else send
        request_id = self._request_id_factory() if is_http else None
        try:
            await self._application(scope, receive, downstream_send)
        except Exception:
            if is_http:
                self._write_record(scope, request_id, 500)
            raise
        else:
            if is_http:
                self._write_record(scope, request_id, status)

    def _write_record(self, scope: Scope, request_id: UUID | None, status: int) -> None:
        safe_request_id = request_id if isinstance(request_id, UUID) else uuid4()
        self._logger.info(
            "request_completed",
            extra={
                "request_id": str(safe_request_id),
                "method": _safe_method(scope.get("method")),
                "path": _route_template(scope),
                "status": _safe_status(status),
            },
        )
