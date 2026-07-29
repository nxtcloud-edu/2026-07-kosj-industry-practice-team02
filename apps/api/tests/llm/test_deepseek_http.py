from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
import pytest

from sejong_ai_api.llm.deepseek_http import (
    DeepSeekResponseEncodingRejected,
    DeepSeekResponseTooLarge,
    read_deepseek_response_bytes,
)


class _ObservedStream(httpx.AsyncByteStream):
    def __init__(
        self,
        chunks: tuple[bytes, ...],
        *,
        failure: Exception | None = None,
    ) -> None:
        self._chunks = chunks
        self._failure = failure
        self.yielded = 0
        self.closed = False

    async def __aiter__(self) -> AsyncIterator[bytes]:
        for chunk in self._chunks:
            self.yielded += 1
            yield chunk
        if self._failure is not None:
            raise self._failure

    async def aclose(self) -> None:
        self.closed = True


@pytest.mark.asyncio
@pytest.mark.parametrize("content_encoding", (None, "identity", " Identity\t"))
async def test_reads_only_identity_encoded_response(content_encoding: str | None) -> None:
    headers = {} if content_encoding is None else {"Content-Encoding": content_encoding}
    response = httpx.Response(200, headers=headers, stream=httpx.ByteStream(b"{}"))

    assert await read_deepseek_response_bytes(response) == b"{}"


@pytest.mark.asyncio
@pytest.mark.parametrize("content_encoding", ("gzip", "br", "identity,gzip", ""))
async def test_rejects_non_identity_content_encoding_without_reading_body(
    content_encoding: str,
) -> None:
    stream = _ObservedStream((b"provider-body-must-not-be-read",))
    response = httpx.Response(
        200,
        headers={"Content-Encoding": content_encoding},
        stream=stream,
    )

    with pytest.raises(
        DeepSeekResponseEncodingRejected,
        match="DEEPSEEK_RESPONSE_ENCODING_REJECTED",
    ):
        await read_deepseek_response_bytes(response)

    assert stream.yielded == 0


@pytest.mark.asyncio
async def test_rejects_exact_64_kib_response() -> None:
    response = httpx.Response(200, stream=httpx.ByteStream(b"x" * (64 * 1024)))

    with pytest.raises(DeepSeekResponseTooLarge, match="DEEPSEEK_RESPONSE_TOO_LARGE"):
        await read_deepseek_response_bytes(response)


@pytest.mark.asyncio
async def test_rejects_chunk_overflow_without_reading_tail() -> None:
    stream = _ObservedStream(
        (
            b"x" * ((64 * 1024) - 1),
            b"y",
            b"provider-tail-must-not-be-read",
        )
    )
    response = httpx.Response(200, stream=stream)

    with pytest.raises(DeepSeekResponseTooLarge, match="DEEPSEEK_RESPONSE_TOO_LARGE"):
        await read_deepseek_response_bytes(response)

    assert stream.yielded == 2


@pytest.mark.asyncio
async def test_propagates_typed_stream_failure_without_wrapping_provider_text() -> None:
    request = httpx.Request("POST", "https://api.deepseek.com/chat/completions")
    error = httpx.ReadError("provider-private-stream-marker", request=request)
    response = httpx.Response(
        200,
        request=request,
        stream=_ObservedStream((b"{",), failure=error),
    )

    with pytest.raises(httpx.ReadError) as caught:
        await read_deepseek_response_bytes(response)

    assert caught.value is error
