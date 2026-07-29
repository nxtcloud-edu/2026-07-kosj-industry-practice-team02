"""Provider-neutral owned runtime for grounded citizen answers."""

from dataclasses import dataclass

import httpx

from sejong_ai_api.llm.chat_contracts import GroundedAnswerGenerator


@dataclass(frozen=True, slots=True)
class GroundedChatRuntime:
    """Own one provider adapter and its process-scoped HTTP client."""

    generator: GroundedAnswerGenerator
    client: httpx.AsyncClient

    async def aclose(self) -> None:
        await self.client.aclose()


__all__ = ["GroundedChatRuntime"]
