#!/usr/bin/env python3
"""Start the local/private API through a fail-closed Windows-safe boundary."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NoReturn, cast

_API_SOURCE = Path(__file__).resolve().parents[1] / "apps" / "api" / "src"
_DEFAULT_PORT = 8000
_MIN_PORT = 1024
_MAX_PORT = 65535

LocalAppFactory = Callable[..., Any]


class _ArgumentsInvalid(ValueError):
    """The caller requested an unsupported or unsafe runtime option."""


class _ConfigurationInvalid(RuntimeError):
    """The existing local-only environment is missing or invalid."""


class _StartupFailed(RuntimeError):
    """The private runner could not establish its startup boundary."""


@dataclass(frozen=True, slots=True)
class _RunnerOptions:
    port: int


class _SafeArgumentParser(argparse.ArgumentParser):
    def error(self, _message: str) -> NoReturn:
        # argparse normally echoes rejected values. Keep failures value-free in case
        # a secret was accidentally supplied as an unsupported argument.
        raise _ArgumentsInvalid from None


class _ValueFreeUvicornErrorFilter(logging.Filter):
    """Replace Uvicorn error details before any configured handler sees them."""

    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelno >= logging.ERROR:
            record.msg = "LOCAL_API_RUNTIME_ERROR"
            record.args = ()
            record.exc_info = None
            record.exc_text = None
            record.stack_info = None
            record.__dict__.pop("color_message", None)
        return True


def _bounded_port(value: str) -> int:
    if not value.isascii() or not value.isdecimal():
        raise argparse.ArgumentTypeError
    port = int(value)
    if not _MIN_PORT <= port <= _MAX_PORT:
        raise argparse.ArgumentTypeError
    return port


def _parse_args(argv: Sequence[str] | None = None) -> _RunnerOptions:
    parser = _SafeArgumentParser(
        prog="run_local_api.py",
        description="Start the loopback-only Sejong AI local API.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--port",
        type=_bounded_port,
        default=_DEFAULT_PORT,
        metavar="PORT",
        help=f"loopback port ({_MIN_PORT}-{_MAX_PORT}; default: {_DEFAULT_PORT})",
    )
    namespace = parser.parse_args(argv)
    port = namespace.port
    if type(port) is not int:
        raise _ArgumentsInvalid
    return _RunnerOptions(port=port)


def _configure_event_loop_policy(platform: str) -> None:
    """Install the psycopg-compatible loop policy on Windows only."""

    if platform != "win32":
        return
    policy_factory = getattr(asyncio, "WindowsSelectorEventLoopPolicy", None)
    if not callable(policy_factory):
        raise _StartupFailed
    asyncio.set_event_loop_policy(policy_factory())


def _load_required_local_app_factory() -> LocalAppFactory:
    """Return the existing factory only when its allowlisted local config is valid."""

    if not _API_SOURCE.is_dir():
        raise _StartupFailed
    source_path = str(_API_SOURCE)
    if source_path not in sys.path:
        sys.path.insert(0, source_path)

    from sejong_ai_api.local import create_local_app, load_local_settings

    if load_local_settings() is None:
        raise _ConfigurationInvalid
    return cast(LocalAppFactory, create_local_app)


def _run_uvicorn(application_factory: LocalAppFactory, port: int) -> None:
    """Run one loopback-only worker without request-line access logging."""

    import uvicorn

    error_logger = logging.getLogger("uvicorn.error")
    value_free_filter = _ValueFreeUvicornErrorFilter()
    error_logger.addFilter(value_free_filter)
    try:
        uvicorn.run(
            application_factory,
            host="127.0.0.1",
            port=port,
            factory=True,
            # Uvicorn 0.51's win32 auto/asyncio factory explicitly creates Proactor.
            # "none" delegates loop creation to the selector policy installed above.
            loop="none",
            access_log=False,
            reload=False,
            workers=1,
            ws="none",
            proxy_headers=False,
            server_header=False,
            log_level="info",
            # Preserve the value-free filter instead of letting Uvicorn replace logging.
            log_config=None,
        )
    finally:
        error_logger.removeFilter(value_free_filter)


def main(argv: Sequence[str] | None = None) -> int:
    try:
        options = _parse_args(argv)
    except _ArgumentsInvalid:
        print("LOCAL_API_ARGUMENTS_INVALID", file=sys.stderr)
        return 2

    try:
        _configure_event_loop_policy(sys.platform)
        application_factory = _load_required_local_app_factory()
    except _ConfigurationInvalid:
        print("LOCAL_API_CONFIGURATION_INVALID", file=sys.stderr)
        return 1
    except Exception:
        print("LOCAL_API_START_FAILED", file=sys.stderr)
        return 1

    try:
        _run_uvicorn(application_factory, options.port)
    except SystemExit:
        print("LOCAL_API_START_FAILED", file=sys.stderr)
        return 1
    except Exception:
        print("LOCAL_API_START_FAILED", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
