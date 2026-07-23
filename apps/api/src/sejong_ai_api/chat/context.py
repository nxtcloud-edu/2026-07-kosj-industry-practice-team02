"""Short-lived, signed, client-carried chat context.

The token is an integrity-protected hint, not an authentication mechanism. Its
payload is intentionally small and closed; it never contains citizen text or
official-source data.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Literal, cast

CONTEXT_TOKEN_SCHEMA_VERSION = 1
CONTEXT_TOKEN_TTL_SECONDS = 900
MAX_CONTEXT_TOKEN_LENGTH = 2048
_MIN_SECRET_BYTES = 32

type Intent = Literal[
    "MOVE_IN_RESIDENT_REGISTRATION",
    "CERTIFICATE_ISSUANCE",
    "BULKY_WASTE",
    "LOCAL_TAX_GENERAL",
    "OUT_OF_SCOPE",
    "UNKNOWN",
]
type Region = Literal["아름동", "도담동", "조치원읍"]
type ContextAnswerStatus = Literal["SUCCESS", "FOLLOWUP"]
type FollowupOptionId = Literal[
    "intent.move-in",
    "intent.certificate",
    "intent.bulky-waste",
    "intent.local-tax",
]
type Clock = Callable[[], int]

_INTENTS = frozenset(
    {
        "MOVE_IN_RESIDENT_REGISTRATION",
        "CERTIFICATE_ISSUANCE",
        "BULKY_WASTE",
        "LOCAL_TAX_GENERAL",
        "OUT_OF_SCOPE",
        "UNKNOWN",
    }
)
_REGIONS = frozenset({"아름동", "도담동", "조치원읍"})
_ANSWER_STATUSES = frozenset({"SUCCESS", "FOLLOWUP"})
_FOLLOWUP_OPTION_IDS = frozenset(
    {
        "intent.move-in",
        "intent.certificate",
        "intent.bulky-waste",
        "intent.local-tax",
    }
)
_REQUIRED_CLAIMS = frozenset(
    {
        "answer_status",
        "exp",
        "iat",
        "last_intent",
        "schema_version",
        "selected_region",
    }
)
_OPTIONAL_CLAIMS = frozenset({"followup_option_id"})


@dataclass(frozen=True, slots=True)
class ChatContext:
    """Validated, non-sensitive context recovered from a client token."""

    schema_version: int
    issued_at: int
    expires_at: int
    last_intent: Intent
    selected_region: Region | None
    answer_status: ContextAnswerStatus
    followup_option_id: str | None = None


class ContextTokenCodec:
    """Issue and silently validate version-one HMAC-SHA-256 context tokens."""

    __slots__ = ("_clock", "_secret")

    def __init__(self, *, secret: bytes, clock: Clock) -> None:
        if type(secret) is not bytes:
            raise TypeError("context token secret must be bytes")
        if len(secret) < _MIN_SECRET_BYTES:
            raise ValueError("context token secret must contain at least 32 bytes")
        if not callable(clock):
            raise TypeError("context token clock must be callable")
        self._secret = secret
        self._clock = clock

    def issue(
        self,
        *,
        last_intent: Intent,
        selected_region: Region | None,
        answer_status: ContextAnswerStatus,
        followup_option_id: FollowupOptionId | None = None,
    ) -> str:
        """Return a deterministic token for the supplied context at the injected time."""

        if type(last_intent) is not str or last_intent not in _INTENTS:
            raise ValueError("last_intent is not allowed")
        if selected_region is not None and (
            type(selected_region) is not str or selected_region not in _REGIONS
        ):
            raise ValueError("selected_region is not allowed")
        if type(answer_status) is not str or answer_status not in _ANSWER_STATUSES:
            raise ValueError("answer_status is not allowed")
        if followup_option_id is not None and not _valid_followup_option_id(followup_option_id):
            raise ValueError("followup_option_id is not a valid server identifier")

        issued_at = self._now()
        payload: dict[str, object] = {
            "answer_status": answer_status,
            "exp": issued_at + CONTEXT_TOKEN_TTL_SECONDS,
            "iat": issued_at,
            "last_intent": last_intent,
            "schema_version": CONTEXT_TOKEN_SCHEMA_VERSION,
            "selected_region": selected_region,
        }
        if followup_option_id is not None:
            payload["followup_option_id"] = followup_option_id

        payload_segment = _encode_base64url(_canonical_json(payload))
        signature = hmac.new(
            self._secret,
            payload_segment.encode("ascii"),
            hashlib.sha256,
        ).digest()
        token = f"{payload_segment}.{_encode_base64url(signature)}"
        if len(token) > MAX_CONTEXT_TOKEN_LENGTH:
            raise ValueError("context token exceeds the maximum length")
        return token

    def read(self, token: str | None) -> ChatContext | None:
        """Return valid context, or silently reset to no context for any bad token."""

        if type(token) is not str or not token or len(token) > MAX_CONTEXT_TOKEN_LENGTH:
            return None

        try:
            payload_segment, signature_segment = _split_token(token)
            supplied_signature = _decode_base64url(signature_segment)
            if len(supplied_signature) != hashlib.sha256().digest_size:
                return None

            expected_signature = hmac.new(
                self._secret,
                payload_segment.encode("ascii"),
                hashlib.sha256,
            ).digest()
            if not hmac.compare_digest(supplied_signature, expected_signature):
                return None

            payload_bytes = _decode_base64url(payload_segment)
            payload_object = json.loads(payload_bytes.decode("utf-8"))
            if type(payload_object) is not dict:
                return None
            payload = cast(dict[str, object], payload_object)
            if payload_bytes != _canonical_json(payload):
                return None
            return self._validate_claims(payload)
        except (
            ValueError,
            UnicodeError,
            binascii.Error,
            json.JSONDecodeError,
            RecursionError,
        ):
            return None

    def _now(self) -> int:
        now = self._clock()
        if type(now) is not int:
            raise TypeError("context token clock must return an integer epoch second")
        if now < 0:
            raise ValueError("context token clock cannot return a negative epoch second")
        return now

    def _validate_claims(self, payload: Mapping[str, object]) -> ChatContext | None:
        claim_names = frozenset(payload)
        if not _REQUIRED_CLAIMS.issubset(claim_names):
            return None
        if not claim_names.issubset(_REQUIRED_CLAIMS | _OPTIONAL_CLAIMS):
            return None

        schema_version = payload["schema_version"]
        issued_at = payload["iat"]
        expires_at = payload["exp"]
        last_intent = payload["last_intent"]
        selected_region = payload["selected_region"]
        answer_status = payload["answer_status"]
        followup_option_id = payload.get("followup_option_id")

        if type(schema_version) is not int or schema_version != CONTEXT_TOKEN_SCHEMA_VERSION:
            return None
        if type(issued_at) is not int or type(expires_at) is not int:
            return None
        if issued_at < 0 or expires_at - issued_at != CONTEXT_TOKEN_TTL_SECONDS:
            return None
        now = self._now()
        if issued_at > now or now >= expires_at:
            return None
        if type(last_intent) is not str or last_intent not in _INTENTS:
            return None
        if selected_region is not None and (
            type(selected_region) is not str or selected_region not in _REGIONS
        ):
            return None
        if type(answer_status) is not str or answer_status not in _ANSWER_STATUSES:
            return None
        if "followup_option_id" in payload and not _valid_followup_option_id(followup_option_id):
            return None

        return ChatContext(
            schema_version=schema_version,
            issued_at=issued_at,
            expires_at=expires_at,
            last_intent=cast(Intent, last_intent),
            selected_region=cast(Region | None, selected_region),
            answer_status=cast(ContextAnswerStatus, answer_status),
            followup_option_id=cast(str | None, followup_option_id),
        )


def _canonical_json(payload: Mapping[str, object]) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _encode_base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode_base64url(value: str) -> bytes:
    if not value or "=" in value:
        raise ValueError("non-canonical base64url")
    encoded = value.encode("ascii")
    padding = b"=" * (-len(encoded) % 4)
    decoded = base64.b64decode(encoded + padding, altchars=b"-_", validate=True)
    if _encode_base64url(decoded) != value:
        raise ValueError("non-canonical base64url")
    return decoded


def _split_token(token: str) -> tuple[str, str]:
    parts = token.split(".")
    if len(parts) != 2 or not all(parts):
        raise ValueError("malformed token")
    return parts[0], parts[1]


def _valid_followup_option_id(value: object) -> bool:
    return type(value) is str and value in _FOLLOWUP_OPTION_IDS


__all__ = [
    "CONTEXT_TOKEN_SCHEMA_VERSION",
    "CONTEXT_TOKEN_TTL_SECONDS",
    "MAX_CONTEXT_TOKEN_LENGTH",
    "ChatContext",
    "ContextTokenCodec",
]
