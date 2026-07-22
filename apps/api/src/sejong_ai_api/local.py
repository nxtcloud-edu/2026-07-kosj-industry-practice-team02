"""Explicit local/private dependency composition.

Use this module as an application factory. Importing ``sejong_ai_api.main``
continues to avoid environment and database access.
"""

from __future__ import annotations

import os
import time
from collections.abc import AsyncIterator, Callable, Mapping
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, cast
from uuid import UUID, uuid4

from fastapi import FastAPI

from sejong_ai_api.chat.context import ContextTokenCodec
from sejong_ai_api.chat.readiness import ReadinessRepository, RepositoryReadinessProbe
from sejong_ai_api.chat.service import (
    ChatRepository,
    ChatResult,
    ChatService,
    ChatUnavailableError,
)
from sejong_ai_api.contracts.chat import ChatRequest
from sejong_ai_api.db.pool import create_pool
from sejong_ai_api.db.repository import PsycopgSejongRepository
from sejong_ai_api.main import create_app

_LOCAL_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
_ALLOWED_ENV_KEYS = frozenset({"DATABASE_URL", "CONTEXT_TOKEN_SECRET"})
_MIN_CONTEXT_SECRET_BYTES = 32


@dataclass(frozen=True, slots=True)
class LocalSettings:
    database_url: str = field(repr=False)
    context_token_secret: bytes = field(repr=False)


class LocalPool(Protocol):
    async def open(self, *, wait: bool = False) -> None: ...

    async def close(self) -> None: ...


class LocalRepository(ChatRepository, ReadinessRepository, Protocol):
    pass


class GuardedChatResponder:
    """Keep chat closed until the approved local projection is ready."""

    __slots__ = ("_probe", "_service")

    def __init__(self, probe: RepositoryReadinessProbe, service: ChatService) -> None:
        self._probe = probe
        self._service = service

    async def answer(
        self,
        request: ChatRequest,
        *,
        request_id: UUID | None = None,
    ) -> ChatResult:
        if not await self._probe.check_ready():
            raise ChatUnavailableError()
        try:
            return await self._service.answer(request, request_id=request_id)
        except ChatUnavailableError:
            self._probe.mark_unavailable()
            raise ChatUnavailableError() from None


def load_local_settings(
    *,
    environ: Mapping[str, str] | None = None,
    env_path: Path | None = None,
) -> LocalSettings | None:
    """Load only the two local runtime values, preferring the process environment."""

    source = os.environ if environ is None else environ
    selected: dict[str, str] = {}
    for key in _ALLOWED_ENV_KEYS:
        if key in source:
            selected[key] = source[key]

    if len(selected) != len(_ALLOWED_ENV_KEYS):
        file_values = _read_allowlisted_env(env_path if env_path is not None else _LOCAL_ENV_PATH)
        if file_values is None:
            return None
        for key in _ALLOWED_ENV_KEYS:
            if key not in selected and key in file_values:
                selected[key] = file_values[key]

    database_dsn = selected.get("DATABASE_URL")
    secret_text = selected.get("CONTEXT_TOKEN_SECRET")
    if not _valid_database_url(database_dsn) or not _valid_env_value(secret_text):
        return None
    valid_database_url = cast(str, database_dsn)
    valid_secret_text = cast(str, secret_text)
    try:
        secret = valid_secret_text.encode("utf-8")
    except UnicodeEncodeError:
        return None
    if len(secret) < _MIN_CONTEXT_SECRET_BYTES:
        return None
    return LocalSettings(database_url=valid_database_url, context_token_secret=secret)


def create_local_app(
    *,
    environ: Mapping[str, str] | None = None,
    env_path: Path | None = None,
    pool_factory: Callable[[str], LocalPool] | None = None,
    repository_factory: Callable[[object], LocalRepository] | None = None,
) -> FastAPI:
    """Build one fail-closed local application without eager network access."""

    settings = load_local_settings(environ=environ, env_path=env_path)
    if settings is None:
        return create_app()

    selected_pool_factory = pool_factory if pool_factory is not None else _default_pool_factory
    selected_repository_factory = (
        repository_factory if repository_factory is not None else _default_repository_factory
    )
    try:
        pool = selected_pool_factory(settings.database_url)
        repository = selected_repository_factory(pool)
        probe = RepositoryReadinessProbe(repository)
        service = ChatService(
            repository=repository,
            context_codec=ContextTokenCodec(
                secret=settings.context_token_secret,
                clock=lambda: int(time.time()),
            ),
            request_id_factory=uuid4,
            monotonic_ns=time.monotonic_ns,
            is_test=False,
        )
        responder = GuardedChatResponder(probe, service)
    except Exception:
        return create_app()

    application = create_app(readiness_probe=probe, chat_responder=responder)

    @asynccontextmanager
    async def local_lifespan(_application: FastAPI) -> AsyncIterator[None]:
        try:
            await pool.open(wait=True)
            await probe.refresh()
        except Exception:
            probe.disable()
        try:
            yield
        finally:
            with suppress(Exception):
                await pool.close()
            probe.disable()

    application.router.lifespan_context = local_lifespan
    return application


def _read_allowlisted_env(path: Path) -> dict[str, str] | None:
    values: dict[str, str] = {}
    try:
        with path.open("r", encoding="utf-8") as stream:
            for raw_line in stream:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("export "):
                    line = line.removeprefix("export ").lstrip()
                key, separator, raw_value = line.partition("=")
                key = key.strip()
                if key not in _ALLOWED_ENV_KEYS:
                    continue
                if not separator or key in values:
                    return None
                value = raw_value.strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                    value = value[1:-1]
                values[key] = value
    except (OSError, UnicodeError):
        return None
    return values


def _valid_env_value(value: object) -> bool:
    return (
        type(value) is str
        and bool(value)
        and value == value.strip()
        and "\x00" not in value
        and "\r" not in value
        and "\n" not in value
    )


def _valid_database_url(value: object) -> bool:
    return _valid_env_value(value) and cast(str, value).startswith(("postgresql://", "postgres://"))


def _default_pool_factory(database_url: str) -> LocalPool:
    return cast(LocalPool, create_pool(database_url))


def _default_repository_factory(pool: object) -> LocalRepository:
    return cast(LocalRepository, PsycopgSejongRepository(cast(Any, pool)))


__all__ = [
    "GuardedChatResponder",
    "LocalSettings",
    "create_local_app",
    "load_local_settings",
]
