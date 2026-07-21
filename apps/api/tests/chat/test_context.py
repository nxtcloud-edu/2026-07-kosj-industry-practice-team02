from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
from collections.abc import Callable
from typing import Any

import pytest

from sejong_ai_api.chat.context import (
    CONTEXT_TOKEN_TTL_SECONDS,
    MAX_CONTEXT_TOKEN_LENGTH,
    ChatContext,
    ContextTokenCodec,
)

NOW = 1_800_000_000
SECRET = b"0123456789abcdef0123456789abcdef"


def _clock(at: int = NOW) -> Callable[[], int]:
    return lambda: at


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _signed_token(payload: dict[str, Any], *, secret: bytes = SECRET) -> str:
    encoded_payload = _b64url(
        json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    )
    signature = hmac.new(secret, encoded_payload.encode("ascii"), hashlib.sha256).digest()
    return f"{encoded_payload}.{_b64url(signature)}"


def _valid_payload() -> dict[str, Any]:
    return {
        "answer_status": "FOLLOWUP",
        "exp": NOW + 900,
        "followup_option_id": "intent.bulky-waste",
        "iat": NOW,
        "last_intent": "UNKNOWN",
        "schema_version": 1,
        "selected_region": "아름동",
    }


def _decode_payload(token: str) -> dict[str, Any]:
    encoded_payload, _signature = token.split(".")
    padding = "=" * (-len(encoded_payload) % 4)
    value = json.loads(base64.urlsafe_b64decode(encoded_payload + padding))
    assert isinstance(value, dict)
    return value


def test_issue_and_read_round_trip_uses_exact_900_second_ttl() -> None:
    codec = ContextTokenCodec(secret=SECRET, clock=_clock())

    token = codec.issue(
        last_intent="UNKNOWN",
        selected_region="아름동",
        answer_status="FOLLOWUP",
        followup_option_id="intent.bulky-waste",
    )

    assert len(token) <= MAX_CONTEXT_TOKEN_LENGTH
    assert _decode_payload(token) == _valid_payload()
    assert codec.read(token) == ChatContext(
        schema_version=1,
        issued_at=NOW,
        expires_at=NOW + CONTEXT_TOKEN_TTL_SECONDS,
        last_intent="UNKNOWN",
        selected_region="아름동",
        answer_status="FOLLOWUP",
        followup_option_id="intent.bulky-waste",
    )


def test_issue_is_deterministic_and_omits_optional_claim_when_absent() -> None:
    codec = ContextTokenCodec(secret=SECRET, clock=_clock())

    first = codec.issue(
        last_intent="BULKY_WASTE",
        selected_region=None,
        answer_status="SUCCESS",
    )
    second = codec.issue(
        last_intent="BULKY_WASTE",
        selected_region=None,
        answer_status="SUCCESS",
    )

    assert first == second
    assert _decode_payload(first) == {
        "answer_status": "SUCCESS",
        "exp": NOW + 900,
        "iat": NOW,
        "last_intent": "BULKY_WASTE",
        "schema_version": 1,
        "selected_region": None,
    }


def test_payload_has_only_closed_non_sensitive_claims() -> None:
    token = ContextTokenCodec(secret=SECRET, clock=_clock()).issue(
        last_intent="CERTIFICATE_ISSUANCE",
        selected_region="도담동",
        answer_status="SUCCESS",
    )

    payload = _decode_payload(token)

    assert set(payload) == {
        "answer_status",
        "exp",
        "iat",
        "last_intent",
        "schema_version",
        "selected_region",
    }
    serialized = json.dumps(payload, ensure_ascii=False).lower()
    for forbidden in (
        "question",
        "answer_text",
        "masked",
        "source",
        "url",
        "kb_id",
        "actor",
        "role",
        "provider",
        "secret",
    ):
        assert forbidden not in serialized


@pytest.mark.parametrize(
    "token",
    [
        None,
        "",
        "one-segment",
        "too.many.segments",
        "!not-base64!.signature",
        "a." + ("x" * MAX_CONTEXT_TOKEN_LENGTH),
    ],
)
def test_malformed_or_oversized_tokens_silently_reset(
    token: str | None,
    caplog: pytest.LogCaptureFixture,
) -> None:
    codec = ContextTokenCodec(secret=SECRET, clock=_clock())

    with caplog.at_level(logging.DEBUG):
        result = codec.read(token)

    assert result is None
    assert caplog.records == []


def test_tampered_token_silently_resets() -> None:
    codec = ContextTokenCodec(secret=SECRET, clock=_clock())
    token = codec.issue(
        last_intent="LOCAL_TAX_GENERAL",
        selected_region="조치원읍",
        answer_status="SUCCESS",
    )
    payload, signature = token.split(".")
    tampered = f"{payload[:-1]}{'A' if payload[-1] != 'A' else 'B'}.{signature}"

    assert codec.read(tampered) is None


def test_token_is_valid_until_but_not_at_expiry() -> None:
    token = ContextTokenCodec(secret=SECRET, clock=_clock()).issue(
        last_intent="MOVE_IN_RESIDENT_REGISTRATION",
        selected_region=None,
        answer_status="SUCCESS",
    )

    assert ContextTokenCodec(secret=SECRET, clock=_clock(NOW + 899)).read(token) is not None
    assert ContextTokenCodec(secret=SECRET, clock=_clock(NOW + 900)).read(token) is None


@pytest.mark.parametrize(
    "mutate",
    [
        lambda payload: payload.update(schema_version=2),
        lambda payload: payload.update(extra="not-allowed"),
        lambda payload: payload.update(iat=NOW + 1, exp=NOW + 901),
        lambda payload: payload.update(exp=NOW + 901),
        lambda payload: payload.update(iat=True),
        lambda payload: payload.update(exp=float(NOW + 900)),
        lambda payload: payload.update(last_intent="NOT_AN_INTENT"),
        lambda payload: payload.update(selected_region="세종시"),
        lambda payload: payload.update(answer_status="FALLBACK"),
        lambda payload: payload.update(followup_option_id=None),
        lambda payload: payload.update(followup_option_id="질문 원문은 금지"),
    ],
)
def test_unknown_or_invalid_claims_silently_reset(
    mutate: Callable[[dict[str, Any]], None],
) -> None:
    payload = _valid_payload()
    mutate(payload)

    assert ContextTokenCodec(secret=SECRET, clock=_clock()).read(_signed_token(payload)) is None


def test_noncanonical_signed_payload_silently_resets() -> None:
    payload_bytes = json.dumps(_valid_payload(), ensure_ascii=False, indent=2).encode("utf-8")
    encoded_payload = _b64url(payload_bytes)
    signature = hmac.new(SECRET, encoded_payload.encode("ascii"), hashlib.sha256).digest()

    token = f"{encoded_payload}.{_b64url(signature)}"

    assert ContextTokenCodec(secret=SECRET, clock=_clock()).read(token) is None


@pytest.mark.parametrize(
    ("secret", "exception_type"),
    [
        (b"too-short", ValueError),
        ("0123456789abcdef0123456789abcdef", TypeError),
    ],
)
def test_codec_requires_at_least_32_secret_bytes(
    secret: object,
    exception_type: type[Exception],
) -> None:
    with pytest.raises(exception_type):
        ContextTokenCodec(secret=secret, clock=_clock())  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "clock_value",
    [True, 1.5, "1800000000"],
)
def test_clock_must_return_an_exact_integer(clock_value: object) -> None:
    def invalid_clock() -> int:
        return clock_value  # type: ignore[return-value]

    codec = ContextTokenCodec(secret=SECRET, clock=invalid_clock)

    with pytest.raises(TypeError):
        codec.issue(
            last_intent="UNKNOWN",
            selected_region=None,
            answer_status="FOLLOWUP",
        )


@pytest.mark.parametrize(
    "followup_option_id",
    [
        "",
        "contains space",
        "한글",
        "x" * 65,
        "010-1234-5678",
        "kb:KB-WASTE-03",
        "actor:user123",
        "source:official",
        "custom.option",
    ],
)
def test_issue_rejects_non_identifier_followup_values(followup_option_id: str) -> None:
    codec = ContextTokenCodec(secret=SECRET, clock=_clock())

    with pytest.raises(ValueError):
        codec.issue(
            last_intent="UNKNOWN",
            selected_region=None,
            answer_status="FOLLOWUP",
            followup_option_id=followup_option_id,  # type: ignore[arg-type]
        )
