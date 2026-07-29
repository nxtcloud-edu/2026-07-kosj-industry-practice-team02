from __future__ import annotations

import json
from collections.abc import Callable
from decimal import Decimal

import httpx
import pytest

from sejong_ai_api.db.models import Intent
from sejong_ai_api.llm.chat_contracts import (
    FactKind,
    GroundedChatOutcomeCode,
    GroundedChatRequest,
    GroundedFact,
)
from sejong_ai_api.llm.chat_prompt import build_grounded_chat_messages
from sejong_ai_api.llm.chat_runtime import GroundedChatRuntime
from sejong_ai_api.llm.contracts import TokenUsage
from sejong_ai_api.llm.deepseek_chat import (
    DeepSeekChatGenerator,
    build_deepseek_chat_runtime,
    create_deepseek_chat_client,
)
from sejong_ai_api.llm.deepseek_settings import DeepSeekChatSettings
from sejong_ai_api.llm.deepseek_usage import estimate_deepseek_cost_usd
from sejong_ai_api.llm.limits import ProviderAttemptLedger

SECRET = "deepseek-chat-test-key-not-a-real-secret"
DSN_SENTINEL = "postgresql://forbidden-dsn.invalid/database"
CLASSIFIER_WORST_CASE_USD = estimate_deepseek_cost_usd(TokenUsage(16384, 0, 128))
GENERATOR_WORST_CASE_USD = estimate_deepseek_cost_usd(TokenUsage(16384, 0, 1024))


def _request(*, question: str = "[PHONE] 전입신고 방법을 알려 주세요.") -> GroundedChatRequest:
    return GroundedChatRequest(
        masked_question=question,
        intent=Intent.MOVE_IN_RESIDENT_REGISTRATION,
        service_name="전입신고",
        approved_summary="전입한 날부터 14일 이내에 전입신고를 합니다.",
        facts=(
            GroundedFact("STEP-01", FactKind.PROCEDURE_STEP, "신고서를 작성합니다."),
            GroundedFact("DOC-01", FactKind.REQUIRED_DOCUMENT, "신분증을 준비합니다."),
            GroundedFact("TIME-01", FactKind.PROCESSING_TIME, "즉시"),
            GroundedFact("FEE-01", FactKind.FEE, "수수료 없음"),
            GroundedFact("DEPT-01", FactKind.DEPARTMENT, "주민등록 담당부서"),
        ),
    )


def _draft_payload(**updates: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "summary": "전입신고 안내를 쉽게 정리해 드려요.",
        "procedure_step_ids": ["STEP-01"],
        "required_document_ids": ["DOC-01"],
        "processing_time_id": "TIME-01",
        "fee_id": "FEE-01",
        "department_id": "DEPT-01",
    }
    payload.update(updates)
    return payload


def _usage(**updates: object) -> dict[str, object]:
    usage: dict[str, object] = {
        "prompt_tokens": 20,
        "completion_tokens": 10,
        "total_tokens": 30,
        "prompt_cache_hit_tokens": 5,
        "prompt_cache_miss_tokens": 15,
    }
    usage.update(updates)
    return usage


def _response_bytes(
    *,
    content: object | None = None,
    finish_reason: object = "stop",
    choices: object | None = None,
    usage: object | None = None,
    include_usage: bool = True,
) -> bytes:
    envelope: dict[str, object] = {
        "choices": (
            [
                {
                    "finish_reason": finish_reason,
                    "message": {
                        "content": (
                            json.dumps(
                                _draft_payload(),
                                ensure_ascii=False,
                                separators=(",", ":"),
                            )
                            if content is None
                            else content
                        )
                    },
                }
            ]
            if choices is None
            else choices
        )
    }
    if include_usage:
        envelope["usage"] = _usage() if usage is None else usage
    return json.dumps(envelope, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _response(
    *,
    content: object | None = None,
    finish_reason: object = "stop",
    choices: object | None = None,
    usage: object | None = None,
    include_usage: bool = True,
) -> httpx.Response:
    return httpx.Response(
        200,
        stream=httpx.ByteStream(
            _response_bytes(
                content=content,
                finish_reason=finish_reason,
                choices=choices,
                usage=usage,
                include_usage=include_usage,
            )
        ),
    )


def _ledger(
    *,
    generator_cap: int = 100,
    combined_cap: int = 160,
    cost_cap_usd: Decimal = Decimal("0.20"),
) -> ProviderAttemptLedger:
    return ProviderAttemptLedger(
        classifier_cap=80,
        generator_cap=generator_cap,
        combined_cap=combined_cap,
        cost_cap_usd=cost_cap_usd,
        classifier_worst_case_usd=CLASSIFIER_WORST_CASE_USD,
        generator_worst_case_usd=GENERATOR_WORST_CASE_USD,
        classifier_cost_estimator=estimate_deepseek_cost_usd,
        generator_cost_estimator=estimate_deepseek_cost_usd,
    )


@pytest.mark.asyncio
async def test_success_sends_exact_deepseek_json_request_and_parses_strict_draft() -> None:
    settings = DeepSeekChatSettings(api_key=SECRET)
    ledger = _ledger()
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return _response()

    async with httpx.AsyncClient(
        base_url=settings.base_url,
        transport=httpx.MockTransport(handler),
    ) as client:
        result = await DeepSeekChatGenerator(
            settings=settings,
            client=client,
            ledger=ledger,
        ).generate(_request())

    assert result.code is GroundedChatOutcomeCode.SUCCESS
    assert result.draft is not None
    assert result.draft.summary == "전입신고 안내를 쉽게 정리해 드려요."
    assert result.usage == TokenUsage(20, 5, 10)
    assert ledger.actual_cost_usd == estimate_deepseek_cost_usd(TokenUsage(20, 5, 10))
    assert len(seen) == 1
    request = seen[0]
    assert request.method == "POST"
    assert request.url.path == "/chat/completions"
    assert request.headers["Accept-Encoding"] == "identity"
    payload = json.loads(request.content)
    assert payload == {
        "model": "deepseek-v4-flash",
        "messages": list(build_grounded_chat_messages(_request())),
        "response_format": {"type": "json_object"},
        "thinking": {"type": "disabled"},
        "temperature": 0,
        "max_tokens": 1024,
        "n": 1,
        "stream": False,
    }
    serialized = request.content.decode("utf-8")
    assert "[PHONE]" in serialized
    for forbidden in (
        "010-2223-2545",
        SECRET,
        DSN_SENTINEL,
        "https://official-source.invalid/private",
        "KB-INTERNAL-UUID-SENTINEL",
    ):
        assert forbidden not in serialized


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status_code", "expected_code"),
    (
        (401, GroundedChatOutcomeCode.AUTH),
        (403, GroundedChatOutcomeCode.AUTH),
        (429, GroundedChatOutcomeCode.RATE_LIMIT),
        (400, GroundedChatOutcomeCode.HTTP_ERROR),
        (500, GroundedChatOutcomeCode.HTTP_ERROR),
    ),
)
async def test_http_failure_discards_body_and_never_retries(
    status_code: int,
    expected_code: GroundedChatOutcomeCode,
    caplog: pytest.LogCaptureFixture,
) -> None:
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            status_code,
            stream=httpx.ByteStream(b"provider-private-body-marker"),
        )

    async with httpx.AsyncClient(
        base_url="https://api.deepseek.com",
        transport=httpx.MockTransport(handler),
    ) as client:
        result = await DeepSeekChatGenerator(
            settings=DeepSeekChatSettings(api_key=SECRET),
            client=client,
            ledger=_ledger(),
        ).generate(_request())

    assert result.code is expected_code
    assert result.draft is None
    assert calls == 1
    assert "provider-private-body-marker" not in repr(result)
    assert "provider-private-body-marker" not in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("exception_factory", "expected_code"),
    (
        (
            lambda request: httpx.ReadTimeout("private-timeout-marker", request=request),
            GroundedChatOutcomeCode.TIMEOUT,
        ),
        (
            lambda request: httpx.ConnectError("private-transport-marker", request=request),
            GroundedChatOutcomeCode.TRANSPORT,
        ),
    ),
)
async def test_transport_failure_is_content_free_and_never_retried(
    exception_factory: Callable[[httpx.Request], httpx.TransportError],
    expected_code: GroundedChatOutcomeCode,
    caplog: pytest.LogCaptureFixture,
) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise exception_factory(request)

    async with httpx.AsyncClient(
        base_url="https://api.deepseek.com",
        transport=httpx.MockTransport(handler),
    ) as client:
        result = await DeepSeekChatGenerator(
            settings=DeepSeekChatSettings(api_key=SECRET),
            client=client,
            ledger=_ledger(),
        ).generate(_request())

    assert result.code is expected_code
    assert result.draft is None
    assert calls == 1
    assert "private-" not in repr(result)
    assert "private-" not in caplog.text


@pytest.mark.asyncio
async def test_unexpected_provider_exception_is_content_free_and_nonretaining(
    caplog: pytest.LogCaptureFixture,
) -> None:
    question_marker = "masked-question-marker"
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise RuntimeError(f"{question_marker} {SECRET} {DSN_SENTINEL}")

    async with httpx.AsyncClient(
        base_url="https://api.deepseek.com",
        transport=httpx.MockTransport(handler),
    ) as client:
        result = await DeepSeekChatGenerator(
            settings=DeepSeekChatSettings(api_key=SECRET),
            client=client,
            ledger=_ledger(),
        ).generate(_request(question=question_marker))

    assert result.code is GroundedChatOutcomeCode.TRANSPORT
    assert result.draft is None
    assert calls == 1
    for forbidden in (question_marker, SECRET, DSN_SENTINEL):
        assert forbidden not in repr(result)
        assert forbidden not in caplog.text


@pytest.mark.asyncio
async def test_invalid_provider_field_is_discarded_without_logging_or_retention(
    caplog: pytest.LogCaptureFixture,
) -> None:
    invalid_marker = "invalid-provider-field-marker"
    body = _response_bytes(
        content=json.dumps(
            _draft_payload(untrusted_extra_field=invalid_marker),
            ensure_ascii=False,
            separators=(",", ":"),
        )
    )

    async with httpx.AsyncClient(
        base_url="https://api.deepseek.com",
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(200, stream=httpx.ByteStream(body))
        ),
    ) as client:
        result = await DeepSeekChatGenerator(
            settings=DeepSeekChatSettings(api_key=SECRET),
            client=client,
            ledger=_ledger(),
        ).generate(_request())

    assert result.code is GroundedChatOutcomeCode.SCHEMA_INVALID
    assert result.draft is None
    assert invalid_marker not in repr(result)
    assert invalid_marker not in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("body", "expected_code"),
    (
        (b"not-json", GroundedChatOutcomeCode.SCHEMA_INVALID),
        (b"\xff", GroundedChatOutcomeCode.SCHEMA_INVALID),
        (b'{"choices":[],"choices":[],"usage":{}}', GroundedChatOutcomeCode.SCHEMA_INVALID),
        (
            _response_bytes(choices=[]),
            GroundedChatOutcomeCode.SCHEMA_INVALID,
        ),
        (
            _response_bytes(choices=[{}, {}]),
            GroundedChatOutcomeCode.SCHEMA_INVALID,
        ),
        (
            _response_bytes(finish_reason="length"),
            GroundedChatOutcomeCode.TRUNCATED,
        ),
        (
            _response_bytes(choices=[{"finish_reason": "stop"}]),
            GroundedChatOutcomeCode.SCHEMA_INVALID,
        ),
        (
            _response_bytes(choices=[{"finish_reason": "stop", "message": {"content": 123}}]),
            GroundedChatOutcomeCode.SCHEMA_INVALID,
        ),
        (
            _response_bytes(content=""),
            GroundedChatOutcomeCode.EMPTY,
        ),
        (
            _response_bytes(content="   "),
            GroundedChatOutcomeCode.EMPTY,
        ),
        (
            _response_bytes(content="{not-json"),
            GroundedChatOutcomeCode.SCHEMA_INVALID,
        ),
        (
            _response_bytes(
                content=(
                    '{"summary":"first","summary":"second",'
                    '"procedure_step_ids":["STEP-01"],'
                    '"required_document_ids":["DOC-01"],'
                    '"processing_time_id":"TIME-01","fee_id":"FEE-01",'
                    '"department_id":"DEPT-01"}'
                )
            ),
            GroundedChatOutcomeCode.SCHEMA_INVALID,
        ),
        (
            _response_bytes(
                content=json.dumps(
                    _draft_payload(source_url="https://provider.invalid"),
                    ensure_ascii=False,
                )
            ),
            GroundedChatOutcomeCode.SCHEMA_INVALID,
        ),
        (
            _response_bytes(include_usage=False),
            GroundedChatOutcomeCode.SCHEMA_INVALID,
        ),
        (
            _response_bytes(usage=_usage(prompt_tokens=True)),
            GroundedChatOutcomeCode.SCHEMA_INVALID,
        ),
        (
            _response_bytes(
                usage=_usage(
                    prompt_cache_hit_tokens=4,
                    prompt_cache_miss_tokens=15,
                )
            ),
            GroundedChatOutcomeCode.SCHEMA_INVALID,
        ),
        (
            _response_bytes(usage=_usage(total_tokens=31)),
            GroundedChatOutcomeCode.SCHEMA_INVALID,
        ),
        (
            _response_bytes(usage=_usage(completion_tokens=1025, total_tokens=1045)),
            GroundedChatOutcomeCode.SCHEMA_INVALID,
        ),
    ),
)
async def test_invalid_response_discards_complete_draft(
    body: bytes,
    expected_code: GroundedChatOutcomeCode,
) -> None:
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, stream=httpx.ByteStream(body))

    async with httpx.AsyncClient(
        base_url="https://api.deepseek.com",
        transport=httpx.MockTransport(handler),
    ) as client:
        result = await DeepSeekChatGenerator(
            settings=DeepSeekChatSettings(api_key=SECRET),
            client=client,
            ledger=_ledger(),
        ).generate(_request())

    assert result.code is expected_code
    assert result.draft is None
    assert calls == 1


@pytest.mark.asyncio
async def test_compressed_or_oversized_response_fails_closed() -> None:
    responses = (
        httpx.Response(
            200,
            headers={"Content-Encoding": "gzip"},
            stream=httpx.ByteStream(b"provider-private-compressed-marker"),
        ),
        httpx.Response(200, stream=httpx.ByteStream(b"x" * (64 * 1024))),
    )

    for response in responses:
        async with httpx.AsyncClient(
            base_url="https://api.deepseek.com",
            transport=httpx.MockTransport(lambda _request, value=response: value),
        ) as client:
            result = await DeepSeekChatGenerator(
                settings=DeepSeekChatSettings(api_key=SECRET),
                client=client,
                ledger=_ledger(),
            ).generate(_request())

        assert result.code is GroundedChatOutcomeCode.SCHEMA_INVALID
        assert result.draft is None


@pytest.mark.asyncio
async def test_generator_attempt_cap_blocks_transport() -> None:
    ledger = _ledger(generator_cap=1, combined_cap=81)
    async with ledger.reserve_generator():
        pass
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return _response()

    async with httpx.AsyncClient(
        base_url="https://api.deepseek.com",
        transport=httpx.MockTransport(handler),
    ) as client:
        result = await DeepSeekChatGenerator(
            settings=DeepSeekChatSettings(api_key=SECRET),
            client=client,
            ledger=ledger,
        ).generate(_request())

    assert result.code is GroundedChatOutcomeCode.ATTEMPT_CAP
    assert calls == 0


@pytest.mark.asyncio
async def test_cost_cap_blocks_transport_before_request() -> None:
    ledger = _ledger(cost_cap_usd=GENERATOR_WORST_CASE_USD - Decimal("0.0000000001"))
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return _response()

    async with httpx.AsyncClient(
        base_url="https://api.deepseek.com",
        transport=httpx.MockTransport(handler),
    ) as client:
        result = await DeepSeekChatGenerator(
            settings=DeepSeekChatSettings(api_key=SECRET),
            client=client,
            ledger=ledger,
        ).generate(_request())

    assert result.code is GroundedChatOutcomeCode.ATTEMPT_CAP
    assert calls == 0
    assert ledger.generator_attempts_used == 0


@pytest.mark.asyncio
async def test_input_limit_blocks_transport() -> None:
    settings = DeepSeekChatSettings(api_key=SECRET)
    object.__setattr__(settings, "max_input_usage_tokens", 1)
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return _response()

    async with httpx.AsyncClient(
        base_url=settings.base_url,
        transport=httpx.MockTransport(handler),
    ) as client:
        result = await DeepSeekChatGenerator(
            settings=settings,
            client=client,
            ledger=_ledger(),
        ).generate(_request())

    assert result.code is GroundedChatOutcomeCode.INPUT_LIMIT
    assert calls == 0


@pytest.mark.asyncio
async def test_runtime_uses_owned_client_and_supplied_shared_ledger(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen = 0

    async def generate_once(
        _client: httpx.AsyncClient,
        *_args: object,
        **_kwargs: object,
    ) -> httpx.Response:
        nonlocal seen
        seen += 1
        return _response()

    monkeypatch.setattr(httpx.AsyncClient, "stream", generate_once)
    ledger = _ledger()
    runtime = build_deepseek_chat_runtime(
        DeepSeekChatSettings(api_key=SECRET),
        ledger=ledger,
    )

    assert isinstance(runtime, GroundedChatRuntime)
    assert isinstance(runtime.generator, DeepSeekChatGenerator)
    assert not runtime.client.is_closed
    await runtime.aclose()
    assert runtime.client.is_closed
    assert seen == 0
    assert ledger.generator_attempts_used == 0


def test_production_client_uses_exact_timeout_and_zero_retry_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class CapturingTransport:
        def __init__(self, *, retries: int) -> None:
            captured["retries"] = retries

    class CapturingClient:
        def __init__(self, **kwargs: object) -> None:
            captured.update(kwargs)

    monkeypatch.setattr(httpx, "AsyncHTTPTransport", CapturingTransport)
    monkeypatch.setattr(httpx, "AsyncClient", CapturingClient)

    client = create_deepseek_chat_client(DeepSeekChatSettings(api_key=SECRET))

    assert isinstance(client, CapturingClient)
    assert captured["base_url"] == "https://api.deepseek.com"
    assert captured["headers"] == {
        "Authorization": f"Bearer {SECRET}",
        "Content-Type": "application/json",
    }
    timeout = captured["timeout"]
    assert isinstance(timeout, httpx.Timeout)
    assert timeout.connect == 3.0
    assert timeout.read == 10.0
    assert timeout.write == 3.0
    assert timeout.pool == 3.0
    assert captured["retries"] == 0
