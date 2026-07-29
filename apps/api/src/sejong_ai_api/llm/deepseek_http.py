"""Shared bounded response reader for local DeepSeek provider adapters."""

from __future__ import annotations

import httpx

DEEPSEEK_RESPONSE_MAX_BYTES = (64 * 1024) - 1
DEEPSEEK_RESPONSE_STREAM_CHUNK_BYTES = 4096


class DeepSeekResponseEncodingRejected(RuntimeError):
    """Value-free control flow for a non-identity provider response."""


class DeepSeekResponseTooLarge(RuntimeError):
    """Value-free control flow for a provider response crossing the byte cap."""


async def read_deepseek_response_bytes(response: httpx.Response) -> bytes:
    """Read one identity-encoded response below the fixed 64-KiB boundary."""

    if not _content_encoding_is_identity(response):
        raise DeepSeekResponseEncodingRejected("DEEPSEEK_RESPONSE_ENCODING_REJECTED")

    payload = bytearray()
    async for chunk in response.aiter_raw(chunk_size=DEEPSEEK_RESPONSE_STREAM_CHUNK_BYTES):
        remaining = DEEPSEEK_RESPONSE_MAX_BYTES - len(payload)
        if len(chunk) > remaining:
            raise DeepSeekResponseTooLarge("DEEPSEEK_RESPONSE_TOO_LARGE")
        payload.extend(chunk)
    return bytes(payload)


def _content_encoding_is_identity(response: httpx.Response) -> bool:
    value = response.headers.get("Content-Encoding")
    return value is None or value.strip(" \t").casefold() == "identity"


__all__ = [
    "DEEPSEEK_RESPONSE_MAX_BYTES",
    "DeepSeekResponseEncodingRejected",
    "DeepSeekResponseTooLarge",
    "read_deepseek_response_bytes",
]
