import type { components } from "../../../../packages/shared-contracts/src/generated/api";

export type ChatRequest = components["schemas"]["ChatRequest"];
export type ChatResponse = components["schemas"]["ChatResponse"];
export type Intent = components["schemas"]["Intent"];
export type Office = components["schemas"]["Office"];

type Fetcher = typeof fetch;

export type ChatSendOptions = Readonly<{
  idempotencyKey?: string;
}>;

export interface ChatTransport {
  send(request: ChatRequest, options?: ChatSendOptions): Promise<ChatResponse>;
}

export class ChatTransportError extends Error {
  readonly retryable: boolean;
  readonly status: number | null;

  constructor(status: number | null, retryable = true) {
    super("지금은 안전한 답변을 만들 수 없어요.");
    this.name = "ChatTransportError";
    this.retryable = retryable;
    this.status = status;
  }
}

function apiUrl(baseUrl: string | undefined, path: string) {
  const normalizedBase = baseUrl?.replace(/\/$/, "") ?? "";
  return `${normalizedBase}${path}`;
}

async function fetchJson<T>(fetcher: Fetcher, url: string, init?: RequestInit): Promise<T> {
  let response: Response;

  try {
    response = await fetcher(url, init);
  } catch {
    throw new ChatTransportError(null);
  }

  if (!response.ok) {
    throw new ChatTransportError(response.status, response.status >= 500);
  }

  try {
    return (await response.json()) as T;
  } catch {
    throw new ChatTransportError(response.status);
  }
}

export function createChatTransport(
  baseUrl?: string,
  fetcher: Fetcher = fetch,
): ChatTransport {
  return {
    send(request, options) {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (options?.idempotencyKey) {
        headers["Idempotency-Key"] = options.idempotencyKey;
      }
      return fetchJson<ChatResponse>(fetcher, apiUrl(baseUrl, "/api/v1/chat"), {
        method: "POST",
        headers,
        body: JSON.stringify(request),
      });
    },
  };
}
