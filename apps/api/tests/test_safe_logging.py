from __future__ import annotations

import ast
import importlib
import io
import json
import logging
from pathlib import Path
from types import ModuleType
from uuid import UUID

from fastapi import Body, WebSocket
from fastapi.testclient import TestClient
from uvicorn.logging import TRACE_LOG_LEVEL

from sejong_ai_api.main import create_app

API_ROOT = Path(__file__).resolve().parents[1]
LOGGING_SOURCE = API_ROOT / "src" / "sejong_ai_api" / "core" / "logging.py"
FIXED_REQUEST_ID = UUID("12345678-1234-5678-9234-567812345678")


class RecordCaptureHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def safe_logging() -> ModuleType:
    assert LOGGING_SOURCE.is_file(), "safe logging module must be implemented"
    return importlib.import_module("sejong_ai_api.core.logging")


def capturing_logger() -> tuple[logging.Logger, io.StringIO]:
    module = safe_logging()
    stream = io.StringIO()
    logger = logging.Logger("sejong-ai-safe-log-test", level=logging.INFO)
    handler = logging.StreamHandler(stream)
    handler.setFormatter(module.SafeRequestJsonFormatter())
    logger.addHandler(handler)
    logger.propagate = False
    return logger, stream


def fixed_request_id() -> UUID:
    return FIXED_REQUEST_ID


def assert_single_record(
    stream: io.StringIO, *, method: str, path: str, status: int, sentinel: str
) -> None:
    output = stream.getvalue()
    if sentinel in output:
        raise AssertionError("formatted request log disclosed synthetic request value")
    lines = output.splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == {
        "request_id": str(FIXED_REQUEST_ID),
        "method": method,
        "path": path,
        "status": status,
    }


def assert_safe_raw_record(record: logging.LogRecord, sentinel: str) -> None:
    baseline = logging.LogRecord("", 0, "", 0, "", (), None).__dict__
    custom_extras = set(record.__dict__) - set(baseline)
    assert custom_extras == {"request_id", "method", "path", "status"}
    assert record.msg == "request_completed"
    assert record.args == ()
    assert record.exc_info is None
    assert record.exc_text is None
    assert record.stack_info is None
    if any(sentinel in str(value) for value in record.__dict__.values()):
        raise AssertionError("raw log record disclosed synthetic request value")


def test_pure_asgi_logging_preserves_body_and_omits_request_derived_values() -> None:
    sentinel = "synthetic-sensitive-sentinel"
    logger, stream = capturing_logger()
    application = create_app(request_logger=logger, request_id_factory=fixed_request_id)

    @application.post("/test-probe/{item_id}")
    async def test_probe(payload: bytes = Body()) -> dict[str, int]:
        return {"size": len(payload)}

    with TestClient(application) as client:
        response = client.post(
            f"/test-probe/{sentinel}",
            params={"lookup": sentinel},
            content=sentinel,
            headers={
                "Authorization": f"Bearer {sentinel}",
                "Content-Type": "application/octet-stream",
                "X-Request-ID": sentinel,
                "X-Synthetic-Probe": sentinel,
                "Cookie": f"probe={sentinel}",
            },
        )

    assert response.status_code == 200
    assert response.json() == {"size": len(sentinel.encode())}
    assert_single_record(
        stream,
        method="POST",
        path="/test-probe/{item_id}",
        status=200,
        sentinel=sentinel,
    )


def test_raw_log_record_contains_only_generic_message_and_four_metadata_extras() -> None:
    sentinel = "synthetic-pre-formatter-sentinel"
    module = safe_logging()
    stream = io.StringIO()
    logger = logging.Logger("sejong-ai-record-capture-test", level=logging.INFO)
    capture = RecordCaptureHandler()
    output = logging.StreamHandler(stream)
    output.setFormatter(module.SafeRequestJsonFormatter())
    logger.addHandler(capture)
    logger.addHandler(output)
    logger.propagate = False
    application = create_app(request_logger=logger, request_id_factory=fixed_request_id)

    @application.post("/test-record/{item_id}")
    async def test_record(payload: bytes = Body()) -> dict[str, int]:
        return {"size": len(payload)}

    with TestClient(application) as client:
        response = client.post(
            f"/test-record/{sentinel}",
            params={"value": sentinel},
            content=sentinel,
            headers={
                "Authorization": sentinel,
                "Content-Type": "application/octet-stream",
                "Cookie": f"probe={sentinel}",
            },
        )
    assert response.status_code == 200
    assert len(capture.records) == 1
    assert_safe_raw_record(capture.records[0], sentinel)


def test_unmatched_route_uses_a_fixed_label() -> None:
    sentinel = "synthetic-unmatched-sentinel"
    logger, stream = capturing_logger()
    application = create_app(request_logger=logger, request_id_factory=fixed_request_id)
    with TestClient(application) as client:
        response = client.get(f"/{sentinel}", params={"value": sentinel})
    assert response.status_code == 404
    assert_single_record(
        stream,
        method="GET",
        path="<unmatched>",
        status=404,
        sentinel=sentinel,
    )


def test_default_request_id_is_a_server_generated_uuid() -> None:
    sentinel = "untrusted-client-request-id"
    logger, stream = capturing_logger()
    with TestClient(create_app(request_logger=logger)) as client:
        response = client.get("/health", headers={"X-Request-ID": sentinel})
    assert response.status_code == 200
    record = json.loads(stream.getvalue())
    assert UUID(record["request_id"])
    assert record["request_id"] != sentinel


def test_exception_logs_generic_500_metadata_once_and_is_reraised() -> None:
    sentinel = "synthetic-exception-sentinel"
    logger, stream = capturing_logger()
    capture = RecordCaptureHandler()
    logger.addHandler(capture)
    application = create_app(request_logger=logger, request_id_factory=fixed_request_id)

    @application.post("/test-error/{item_id}")
    async def test_error(item_id: str, payload: bytes = Body()) -> None:
        raise RuntimeError(sentinel)

    with TestClient(application, raise_server_exceptions=False) as client:
        response = client.post(
            f"/test-error/{sentinel}",
            params={"value": sentinel},
            content=sentinel,
            headers={
                "Authorization": sentinel,
                "Content-Type": "application/octet-stream",
                "Cookie": f"probe={sentinel}",
            },
        )
    assert response.status_code == 500
    if sentinel in response.text:
        raise AssertionError("public 500 response disclosed synthetic exception value")
    assert len(capture.records) == 1
    assert_safe_raw_record(capture.records[0], sentinel)
    assert_single_record(
        stream,
        method="POST",
        path="/test-error/{item_id}",
        status=500,
        sentinel=sentinel,
    )

    second_logger, _ = capturing_logger()
    second_application = create_app(
        request_logger=second_logger, request_id_factory=fixed_request_id
    )

    @second_application.get("/test-reraise")
    async def test_reraise() -> None:
        raise RuntimeError(sentinel)

    with TestClient(second_application, raise_server_exceptions=True) as client:
        try:
            client.get("/test-reraise")
        except RuntimeError as error:
            assert str(error) == sentinel
        else:
            raise AssertionError("middleware must re-raise application exceptions")


def test_lifespan_and_websocket_scopes_emit_no_request_log() -> None:
    logger, stream = capturing_logger()
    application = create_app(request_logger=logger, request_id_factory=fixed_request_id)

    @application.websocket("/test-websocket")
    async def test_websocket(websocket: WebSocket) -> None:
        await websocket.accept()
        await websocket.close()

    with TestClient(application) as client:
        assert stream.getvalue() == ""
        with client.websocket_connect("/test-websocket"):
            pass
    assert stream.getvalue() == ""


def test_health_and_readiness_public_contracts_remain_exact() -> None:
    logger, stream = capturing_logger()
    request_ids = iter(
        (
            UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"),
            UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"),
        )
    )

    def request_id_factory() -> UUID:
        return next(request_ids)

    with TestClient(
        create_app(request_logger=logger, request_id_factory=request_id_factory)
    ) as client:
        health = client.get("/health")
        ready = client.get("/ready")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    assert ready.status_code == 503
    assert ready.headers["Retry-After"] == "30"
    assert set(ready.json()) == {"error"}
    assert len(stream.getvalue().splitlines()) == 2


def test_formatter_serializes_only_allowlisted_metadata_and_safely_defaults_malformed_extras() -> (
    None
):
    module = safe_logging()
    sentinel = "synthetic-malformed-log-sentinel"
    formatter = module.SafeRequestJsonFormatter()
    record = logging.LogRecord(
        name="sejong_ai_api.request",
        level=logging.ERROR,
        pathname=__file__,
        lineno=1,
        msg="request failed: %s",
        args=(sentinel,),
        exc_info=(RuntimeError, RuntimeError(sentinel), None),
    )
    record.request_id = sentinel
    record.method = sentinel
    record.path = sentinel
    record.status = sentinel
    record.exc_text = sentinel
    record.stack_info = sentinel

    output = formatter.format(record)

    if sentinel in output:
        raise AssertionError("formatter disclosed malformed synthetic metadata")
    assert json.loads(output) == {
        "request_id": "00000000-0000-0000-0000-000000000000",
        "method": "UNKNOWN",
        "path": "<unmatched>",
        "status": 500,
    }
    assert set(json.loads(output)) == {"request_id", "method", "path", "status"}


def test_request_logger_configuration_is_idempotent() -> None:
    module = safe_logging()
    first = module.get_safe_request_logger()
    create_app()
    second = module.get_safe_request_logger()
    create_app()
    matching_handlers = [
        handler
        for handler in second.handlers
        if isinstance(handler.formatter, module.SafeRequestJsonFormatter)
    ]
    assert first is second
    assert second.propagate is False
    assert len(matching_handlers) == 1


def test_uvicorn_access_is_disabled_and_exception_filter_is_safe_and_idempotent() -> None:
    module = safe_logging()
    module.configure_uvicorn_log_safety()
    module.configure_uvicorn_log_safety()
    access_logger = logging.getLogger("uvicorn.access")
    trace_logger = logging.getLogger("uvicorn.asgi")
    error_logger = logging.getLogger("uvicorn.error")
    filters = [
        item for item in error_logger.filters if isinstance(item, module.SafeExceptionFilter)
    ]
    assert access_logger.disabled is True
    assert access_logger.propagate is False
    assert trace_logger.disabled is True
    assert trace_logger.propagate is False
    assert error_logger.disabled is False
    assert len(filters) == 1

    sentinel = "synthetic-uvicorn-error-sentinel"
    exception_record = logging.LogRecord(
        name="uvicorn.error",
        level=logging.ERROR,
        pathname=__file__,
        lineno=1,
        msg="request failed: %s",
        args=(sentinel,),
        exc_info=(RuntimeError, RuntimeError(sentinel), None),
    )
    exception_record.exc_text = sentinel
    exception_record.stack_info = sentinel
    assert filters[0].filter(exception_record) is True
    assert exception_record.getMessage() == "Unhandled application error"
    assert exception_record.args == ()
    assert exception_record.exc_info is None
    assert exception_record.exc_text is None
    assert exception_record.stack_info is None

    for level, message in (
        (logging.INFO, "Application startup complete."),
        (logging.ERROR, "Non-exception operational error."),
    ):
        record = logging.LogRecord(
            name="uvicorn.error",
            level=level,
            pathname=__file__,
            lineno=1,
            msg=message,
            args=(),
            exc_info=None,
        )
        assert filters[0].filter(record) is True
        assert record.getMessage() == message


def test_uvicorn_error_filter_drops_protocol_trace_with_client_address() -> None:
    module = safe_logging()
    module.configure_uvicorn_log_safety()
    error_logger = logging.getLogger("uvicorn.error")
    capture = RecordCaptureHandler()
    original_level = error_logger.level
    original_handlers = list(error_logger.handlers)
    original_disabled = error_logger.disabled
    original_propagate = error_logger.propagate
    sentinel = "synthetic-client-address-sentinel"

    try:
        error_logger.handlers = [capture]
        error_logger.setLevel(TRACE_LOG_LEVEL)
        error_logger.disabled = False
        error_logger.propagate = False
        error_logger.log(
            TRACE_LOG_LEVEL,
            "%sHTTP connection made",
            f"{sentinel}:43210 - ",
        )
        error_logger.info("Application startup complete.")
        error_logger.error("Non-exception operational error.")
    finally:
        error_logger.handlers = original_handlers
        error_logger.setLevel(original_level)
        error_logger.disabled = original_disabled
        error_logger.propagate = original_propagate

    messages = [record.getMessage() for record in capture.records]
    assert messages == [
        "Application startup complete.",
        "Non-exception operational error.",
    ]
    assert all(sentinel not in message for message in messages)


def test_uvicorn_error_filter_drops_websocket_info_templates_without_formatting() -> None:
    module = safe_logging()
    module.configure_uvicorn_log_safety()
    filters = [
        item
        for item in logging.getLogger("uvicorn.error").filters
        if isinstance(item, module.SafeExceptionFilter)
    ]
    assert len(filters) == 1
    sentinel_client = "synthetic-websocket-client-sentinel:43210"
    sentinel_path = "/synthetic-websocket-path?token=synthetic-query-sentinel"
    pinned_records = (
        ('%s - "WebSocket %s" [accepted]', (sentinel_client, sentinel_path)),
        ('%s - "WebSocket %s" 403', (sentinel_client, sentinel_path)),
        ('%s - "WebSocket %s" %d', (sentinel_client, sentinel_path, 401)),
    )

    for message, arguments in pinned_records:
        record = logging.LogRecord(
            name="uvicorn.error",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg=message,
            args=arguments,
            exc_info=None,
        )
        assert filters[0].filter(record) is False
        assert record.msg == message
        assert record.args == arguments


def test_official_uvicorn_command_disables_access_log_and_websockets() -> None:
    readme = (API_ROOT / "README.md").read_text(encoding="utf-8")
    command = readme.split("uvicorn sejong_ai_api.main:app", 1)[1].split("```", 1)[0]
    assert "--no-access-log" in command
    assert "--ws none" in command


def test_safe_logging_source_is_pure_asgi_and_never_reads_sensitive_request_channels() -> None:
    safe_logging()
    source = LOGGING_SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(LOGGING_SOURCE))
    assert "BaseHTTPMiddleware" not in source
    assert "call_next" not in source
    assert "from fastapi import Request" not in source

    banned_attributes = {
        "body",
        "json",
        "form",
        "headers",
        "query_params",
        "cookies",
        "client",
        "url",
        "getMessage",
        "formatException",
    }
    accessed_attributes = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    assert accessed_attributes.isdisjoint(banned_attributes)

    banned_scope_keys = {"body", "headers", "query_string", "cookies", "client", "raw_path"}
    retrieved_keys: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "get" or not node.args:
            continue
        first_argument = node.args[0]
        if isinstance(first_argument, ast.Constant) and isinstance(first_argument.value, str):
            retrieved_keys.add(first_argument.value)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Subscript):
            continue
        key = node.slice
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            retrieved_keys.add(key.value)
    assert retrieved_keys.isdisjoint(banned_scope_keys)

    receive_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "receive"
    ]
    downstream_receive_arguments = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and any(
            isinstance(argument, ast.Name) and argument.id == "receive" for argument in node.args
        )
    ]
    assert receive_calls == []
    assert len(downstream_receive_arguments) == 1

    middleware_classes = [
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "SafeRequestLoggingMiddleware"
    ]
    assert len(middleware_classes) == 1
    assert middleware_classes[0].bases == []
