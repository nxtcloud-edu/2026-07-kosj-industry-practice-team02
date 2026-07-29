"""One-attempt DeepSeek transport boundary for grounded citizen answers."""

from __future__ import annotations

import asyncio

import httpx
from pydantic import ValidationError

from sejong_ai_api.llm.chat_contracts import (
    GeneratedChatDraft,
    GroundedChatOutcomeCode,
    GroundedChatRequest,
    GroundedChatResult,
)
from sejong_ai_api.llm.chat_prompt import (
    build_grounded_chat_messages,
    estimate_grounded_input_upper_bound,
)
from sejong_ai_api.llm.chat_runtime import GroundedChatRuntime
from sejong_ai_api.llm.contracts import TokenUsage
from sejong_ai_api.llm.deepseek_http import (
    DeepSeekResponseEncodingRejected,
    DeepSeekResponseTooLarge,
    read_deepseek_response_bytes,
)
from sejong_ai_api.llm.deepseek_settings import (
    DEEPSEEK_MAX_OUTPUT_TOKENS,
    DeepSeekChatSettings,
)
from sejong_ai_api.llm.deepseek_usage import (
    estimate_deepseek_cost_usd,
    parse_deepseek_token_usage,
)
from sejong_ai_api.llm.limits import (
    AttemptCapReached,
    ProviderAttemptLedger,
    ProviderCostReservation,
)
from sejong_ai_api.llm.strict_json import load_strict_json_bytes

_CHAT_COMPLETIONS_PATH = "/chat/completions"
_ZERO_USAGE = TokenUsage(0, 0, 0)


def create_deepseek_chat_client(settings: DeepSeekChatSettings) -> httpx.AsyncClient:
    """Create the exact no-retry client for local DeepSeek grounded answers."""

    if type(settings) is not DeepSeekChatSettings:
        raise ValueError("DEEPSEEK_CHAT_SETTINGS_INVALID")
    timeout = httpx.Timeout(
        settings.timeout_seconds,
        connect=settings.connect_timeout_seconds,
        read=settings.read_timeout_seconds,
        write=settings.write_timeout_seconds,
        pool=settings.pool_timeout_seconds,
    )
    return httpx.AsyncClient(
        base_url=settings.base_url,
        headers={
            "Authorization": f"Bearer {settings.api_key}",
            "Content-Type": "application/json",
        },
        timeout=timeout,
        transport=httpx.AsyncHTTPTransport(retries=0),
    )


class DeepSeekChatGenerator:
    """Return one strictly validated draft or a content-free failure result."""

    __slots__ = (
        "_chat_completions_url",
        "_client",
        "_ledger",
        "_max_input_usage_tokens",
        "_max_output_tokens",
        "_model",
        "_timeout_seconds",
    )

    def __init__(
        self,
        *,
        settings: DeepSeekChatSettings,
        client: httpx.AsyncClient,
        ledger: ProviderAttemptLedger,
    ) -> None:
        if type(settings) is not DeepSeekChatSettings:
            raise ValueError("DEEPSEEK_CHAT_SETTINGS_INVALID")
        if not isinstance(client, httpx.AsyncClient):
            raise ValueError("DEEPSEEK_CHAT_CLIENT_INVALID")
        if type(ledger) is not ProviderAttemptLedger:
            raise ValueError("PROVIDER_ATTEMPT_LEDGER_INVALID")
        self._chat_completions_url = f"{settings.base_url}{_CHAT_COMPLETIONS_PATH}"
        self._client = client
        self._ledger = ledger
        self._max_input_usage_tokens = settings.max_input_usage_tokens
        self._max_output_tokens = settings.max_output_tokens
        self._model = settings.model
        self._timeout_seconds = settings.timeout_seconds

    async def generate(self, request: GroundedChatRequest) -> GroundedChatResult:
        try:
            messages = build_grounded_chat_messages(request)
        except (AttributeError, TypeError, ValueError):
            return _failure(GroundedChatOutcomeCode.SCHEMA_INVALID)
        if estimate_grounded_input_upper_bound(messages) > self._max_input_usage_tokens:
            return _failure(GroundedChatOutcomeCode.INPUT_LIMIT)

        payload = {
            "model": self._model,
            "messages": list(messages),
            "response_format": {"type": "json_object"},
            "thinking": {"type": "disabled"},
            "temperature": 0,
            "max_tokens": self._max_output_tokens,
            "n": 1,
            "stream": False,
        }
        try:
            async with self._ledger.reserve_generator() as reservation:
                async with asyncio.timeout(self._timeout_seconds):
                    async with self._client.stream(
                        "POST",
                        self._chat_completions_url,
                        json=payload,
                        headers={"Accept-Encoding": "identity"},
                    ) as response:
                        if response.status_code in (401, 403):
                            return _failure(GroundedChatOutcomeCode.AUTH)
                        if response.status_code == 429:
                            return _failure(GroundedChatOutcomeCode.RATE_LIMIT)
                        if response.status_code < 200 or response.status_code >= 300:
                            return _failure(GroundedChatOutcomeCode.HTTP_ERROR)
                        response_bytes = await read_deepseek_response_bytes(response)
                        return _parse_response_bytes(
                            response_bytes,
                            reservation=reservation,
                            max_input_tokens=self._max_input_usage_tokens,
                            max_output_tokens=self._max_output_tokens,
                        )
        except AttemptCapReached:
            return _failure(GroundedChatOutcomeCode.ATTEMPT_CAP)
        except (DeepSeekResponseEncodingRejected, DeepSeekResponseTooLarge):
            return _failure(GroundedChatOutcomeCode.SCHEMA_INVALID)
        except (httpx.TimeoutException, TimeoutError):
            return _failure(GroundedChatOutcomeCode.TIMEOUT)
        except httpx.TransportError:
            return _failure(GroundedChatOutcomeCode.TRANSPORT)
        except Exception:
            # Provider details and response content never cross this boundary.
            return _failure(GroundedChatOutcomeCode.TRANSPORT)


def build_deepseek_chat_runtime(
    settings: DeepSeekChatSettings,
    *,
    ledger: ProviderAttemptLedger | None = None,
) -> GroundedChatRuntime:
    """Build one process-scoped DeepSeek answer runtime."""

    if type(settings) is not DeepSeekChatSettings:
        raise ValueError("DEEPSEEK_CHAT_SETTINGS_INVALID")
    client = create_deepseek_chat_client(settings)
    owned_ledger = ledger if ledger is not None else _build_default_ledger(settings)
    return GroundedChatRuntime(
        generator=DeepSeekChatGenerator(
            settings=settings,
            client=client,
            ledger=owned_ledger,
        ),
        client=client,
    )


def _build_default_ledger(settings: DeepSeekChatSettings) -> ProviderAttemptLedger:
    return ProviderAttemptLedger(
        classifier_cap=settings.classifier_attempt_cap,
        generator_cap=settings.generator_attempt_cap,
        combined_cap=settings.combined_attempt_cap,
        cost_cap_usd=settings.session_cost_cap_usd,
        classifier_worst_case_usd=estimate_deepseek_cost_usd(
            TokenUsage(settings.max_input_usage_tokens, 0, DEEPSEEK_MAX_OUTPUT_TOKENS)
        ),
        generator_worst_case_usd=estimate_deepseek_cost_usd(
            TokenUsage(settings.max_input_usage_tokens, 0, settings.max_output_tokens)
        ),
        classifier_cost_estimator=estimate_deepseek_cost_usd,
        generator_cost_estimator=estimate_deepseek_cost_usd,
    )


def _parse_response_bytes(
    response_bytes: bytes,
    *,
    reservation: ProviderCostReservation,
    max_input_tokens: int,
    max_output_tokens: int,
) -> GroundedChatResult:
    try:
        envelope = load_strict_json_bytes(response_bytes)
    except (UnicodeDecodeError, TypeError, ValueError):
        return _failure(GroundedChatOutcomeCode.SCHEMA_INVALID)
    if type(envelope) is not dict:
        return _failure(GroundedChatOutcomeCode.SCHEMA_INVALID)

    usage = parse_deepseek_token_usage(
        envelope.get("usage"),
        max_input_tokens=max_input_tokens,
        max_output_tokens=max_output_tokens,
    )
    if usage is None:
        return _failure(GroundedChatOutcomeCode.SCHEMA_INVALID)
    try:
        reservation.record_usage(usage)
    except Exception:
        return _failure(GroundedChatOutcomeCode.SCHEMA_INVALID)

    choices = envelope.get("choices")
    if type(choices) is not list or len(choices) != 1 or type(choices[0]) is not dict:
        return _failure(GroundedChatOutcomeCode.SCHEMA_INVALID, usage=usage)
    choice = choices[0]
    if choice.get("finish_reason") != "stop":
        return _failure(GroundedChatOutcomeCode.TRUNCATED, usage=usage)
    message = choice.get("message")
    if type(message) is not dict:
        return _failure(GroundedChatOutcomeCode.SCHEMA_INVALID, usage=usage)
    content = message.get("content")
    if type(content) is not str:
        return _failure(GroundedChatOutcomeCode.SCHEMA_INVALID, usage=usage)
    if not content.strip():
        return _failure(GroundedChatOutcomeCode.EMPTY, usage=usage)
    try:
        draft_value = load_strict_json_bytes(content.encode("utf-8"))
        draft = GeneratedChatDraft.model_validate(draft_value)
    except (UnicodeEncodeError, UnicodeDecodeError, TypeError, ValueError, ValidationError):
        return _failure(GroundedChatOutcomeCode.SCHEMA_INVALID, usage=usage)
    return GroundedChatResult(
        code=GroundedChatOutcomeCode.SUCCESS,
        draft=draft,
        usage=usage,
    )


def _failure(
    code: GroundedChatOutcomeCode,
    *,
    usage: TokenUsage = _ZERO_USAGE,
) -> GroundedChatResult:
    return GroundedChatResult(code=code, usage=usage)


__all__ = [
    "DeepSeekChatGenerator",
    "build_deepseek_chat_runtime",
    "create_deepseek_chat_client",
]
