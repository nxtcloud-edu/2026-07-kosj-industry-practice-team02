// @vitest-environment jsdom

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type {
  ChatRequest,
  ChatResponse,
  ChatTransport,
  Office,
} from "../../lib/chat-api";
import { ChatTransportError } from "../../lib/chat-api";

import { ChatExperience } from "./chat-experience";

const OFFICE = {
  id: "office-001",
  region: "아름동",
  office_name: "아름동 행정복지센터",
  address: "세종특별자치시 보듬3로 114",
  phone: "044-301-6361",
  opening_hours: "평일 09:00~18:00",
  map_url: "https://example.invalid/official/office-map",
  source_title: "세종특별자치시 공식 안내",
  source_url: "https://example.invalid/official/office",
  last_verified_at: "2026-07-20",
} satisfies Office;

const SUCCESS_RESPONSE = {
  request_id: "11111111-1111-4111-8111-111111111111",
  answer_status: "SUCCESS",
  intent: "MOVE_IN_RESIDENT_REGISTRATION",
  confidence: 0.96,
  summary: "전입신고는 전입한 날부터 14일 이내에 해요.",
  procedure_steps: ["신고서를 작성해요.", "행정복지센터에 제출해요."],
  required_documents: ["신분증"],
  processing_time: "즉시",
  fee: "없음",
  department: "주민등록 담당",
  sources: [
    {
      source_id: "source-001",
      title: "세종특별자치시 전입신고 안내",
      url: "https://example.invalid/official/move-in",
      last_verified_at: "2026-07-20",
    },
  ],
  office: OFFICE,
  context_token: "signed-context-one",
} satisfies ChatResponse;

function transportWith(send: ChatTransport["send"]): ChatTransport {
  return { send };
}

function ask(question: string) {
  fireEvent.change(screen.getByRole("textbox", { name: "민원 질문" }), {
    target: { value: question },
  });
  fireEvent.click(screen.getByRole("button", { name: "질문 보내기" }));
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("citizen chat experience", () => {
  it("renders a successful answer with source and selected-region office metadata unchanged", async () => {
    const send = vi.fn().mockResolvedValue(SUCCESS_RESPONSE);
    render(<ChatExperience transport={transportWith(send)} />);

    fireEvent.change(screen.getByRole("combobox", { name: "지역 선택" }), {
      target: { value: "아름동" },
    });
    ask("이사했는데 전입신고 어떻게 해요?");

    expect(await screen.findByText(SUCCESS_RESPONSE.summary)).toBeInTheDocument();
    expect(screen.getByText("신분증")).toBeInTheDocument();
    const sourceLink = screen.getByRole("link", { name: SUCCESS_RESPONSE.sources[0].title });
    expect(sourceLink).toHaveAttribute("href", SUCCESS_RESPONSE.sources[0].url);
    expect(screen.getAllByText("2026-07-20")).toHaveLength(2);
    expect(screen.getByRole("heading", { name: OFFICE.office_name })).toBeInTheDocument();
    expect(screen.getByText(OFFICE.address)).toBeInTheDocument();
    expect(screen.getByText(OFFICE.phone)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: OFFICE.source_title })).toHaveAttribute(
      "href",
      OFFICE.source_url,
    );
    expect(screen.getByRole("link", { name: "공식 지도 링크" })).toHaveAttribute(
      "href",
      OFFICE.map_url,
    );
    expect(send).toHaveBeenCalledWith({
      question: "이사했는데 전입신고 어떻게 해요?",
      selected_region: "아름동",
      simple_language: true,
      context_token: null,
    });
  });

  it("keeps follow-up context only in React memory and sends it with the selected option", async () => {
    const followup = {
      request_id: "22222222-2222-4222-8222-222222222222",
      answer_status: "FOLLOWUP",
      intent: "UNKNOWN",
      sources: [],
      followup_options: ["전입신고", "증명서 발급"],
      office: null,
      context_token: "signed-followup-context",
    } satisfies ChatResponse;
    const send = vi.fn().mockResolvedValueOnce(followup).mockResolvedValueOnce(SUCCESS_RESPONSE);
    const localStorageSpy = vi.spyOn(Storage.prototype, "setItem");
    render(<ChatExperience transport={transportWith(send)} />);

    ask("신고하고 싶어요.");
    const option = await screen.findByRole("button", { name: "전입신고" });
    fireEvent.click(option);

    await waitFor(() => expect(send).toHaveBeenCalledTimes(2));
    expect(send.mock.calls[1][0]).toEqual({
      question: "전입신고",
      selected_region: null,
      simple_language: true,
      context_token: "signed-followup-context",
    } satisfies ChatRequest);
    expect(localStorageSpy).not.toHaveBeenCalled();
    expect(window.sessionStorage.length).toBe(0);
    expect(document.cookie).toBe("");
    expect(option).toBeDisabled();
  });

  it.each([
    ["INSUFFICIENT_GROUNDING", true],
    ["PERSONAL_LOOKUP", false],
    ["LEGAL_JUDGMENT", false],
    ["OUT_OF_SCOPE", false],
    ["PRIVACY_UNRESOLVED", false],
  ] as const)("renders the %s fallback reason and safe API copy", async (reason, eligible) => {
    const intent =
      reason === "OUT_OF_SCOPE"
        ? "OUT_OF_SCOPE"
        : reason === "PRIVACY_UNRESOLVED"
          ? "UNKNOWN"
          : "LOCAL_TAX_GENERAL";
    const response: ChatResponse = reason === "PRIVACY_UNRESOLVED" ? {
      request_id: "33333333-3333-4333-8333-333333333333",
      answer_status: "FALLBACK",
      intent: "UNKNOWN",
      confidence: null,
      sources: [],
      fallback: {
        reason: "PRIVACY_UNRESOLVED",
        title: "개인정보를 안전하게 처리하지 못했어요",
        message: "개인정보를 빼거나 표현을 바꿔서 다시 질문해 주세요.",
        next_actions: ["이름, 주소, 전화번호, 접수번호 등을 적지 마세요."],
        candidate_eligible: false,
        office: null,
      },
      context_token: null,
    } : {
      request_id: "33333333-3333-4333-8333-333333333333",
      answer_status: "FALLBACK",
      intent,
      confidence: null,
      sources: [],
      fallback: {
        reason,
        title: `${reason} 안내`,
        message: "개인정보를 빼거나 표현을 바꾸어 다시 질문해 주세요.",
        candidate_eligible: eligible,
        office: null,
      },
      context_token: null,
    } as ChatResponse;
    render(<ChatExperience transport={transportWith(vi.fn().mockResolvedValue(response))} />);

    ask("테스트 질문");

    const expectedTitle = reason === "PRIVACY_UNRESOLVED"
      ? "개인정보를 안전하게 처리하지 못했어요"
      : `${reason} 안내`;
    const expectedMessage = reason === "PRIVACY_UNRESOLVED"
      ? "개인정보를 빼거나 표현을 바꿔서 다시 질문해 주세요."
      : "개인정보를 빼거나 표현을 바꾸어 다시 질문해 주세요.";
    const title = await screen.findByText(expectedTitle);
    const fallbackArticle = title.closest("article");
    expect(fallbackArticle).not.toBeNull();
    expect(fallbackArticle).not.toHaveAttribute("role", "status");
    expect(screen.getByRole("region", { name: "대화 내용" })).toHaveAttribute("aria-live", "polite");
    expect(within(fallbackArticle as HTMLElement).getByText(expectedTitle)).toBeInTheDocument();
    expect(
      within(fallbackArticle as HTMLElement).getByText(
        expectedMessage,
      ),
    ).toBeInTheDocument();
    expect(within(fallbackArticle as HTMLElement).getByText(reason)).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /official/ })).not.toBeInTheDocument();
    if (reason === "PRIVACY_UNRESOLVED") {
      expect(
        within(fallbackArticle as HTMLElement).getByText(
          "이름, 주소, 전화번호, 접수번호 등을 적지 마세요.",
        ),
      ).toBeInTheDocument();
    }
  });

  it("prevents duplicate submission while a request is loading", async () => {
    let resolveResponse: ((response: ChatResponse) => void) | undefined;
    const pending = new Promise<ChatResponse>((resolve) => {
      resolveResponse = resolve;
    });
    const send = vi.fn().mockReturnValue(pending);
    render(<ChatExperience transport={transportWith(send)} />);

    ask("전입신고 알려줘");
    const submit = screen.getByRole("button", { name: "답변 확인 중" });
    expect(submit).toBeDisabled();
    fireEvent.click(submit);
    expect(send).toHaveBeenCalledTimes(1);
    const loadingState = screen.getByText("승인된 공식 근거를 확인하고 있어요.");
    expect(loadingState).toBeInTheDocument();
    expect(loadingState).not.toHaveAttribute("role", "status");

    resolveResponse?.(SUCCESS_RESPONSE);
    expect(await screen.findByText(SUCCESS_RESPONSE.summary)).toBeInTheDocument();
  });

  it("shows a value-free error and retries the same in-memory draft", async () => {
    const send = vi
      .fn()
      .mockRejectedValueOnce(new Error("raw upstream payload must stay hidden"))
      .mockResolvedValueOnce(SUCCESS_RESPONSE);
    render(<ChatExperience transport={transportWith(send)} />);

    ask("이사했는데 신고를 알려줘");

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "지금은 안전한 답변을 만들 수 없어요.",
    );
    expect(screen.queryByText(/raw upstream/)).not.toBeInTheDocument();
    expect(
      within(screen.getByRole("region", { name: "대화 내용" })).queryByText(
        "이사했는데 신고를 알려줘",
      ),
    ).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "다시 시도" }));
    expect(await screen.findByText(SUCCESS_RESPONSE.summary)).toBeInTheDocument();
    expect(send).toHaveBeenCalledTimes(2);
  });

  it("does not offer retry for a non-retryable validation error", async () => {
    const send = vi.fn().mockRejectedValue(new ChatTransportError(422, false));
    render(<ChatExperience transport={transportWith(send)} />);

    ask("잘못된 요청");

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "입력 내용을 확인한 뒤 새 질문을 보내 주세요.",
    );
    expect(screen.queryByRole("button", { name: "다시 시도" })).not.toBeInTheDocument();
  });

  it("preserves a new draft typed while the previous request is pending", async () => {
    let resolveResponse: ((response: ChatResponse) => void) | undefined;
    const pending = new Promise<ChatResponse>((resolve) => {
      resolveResponse = resolve;
    });
    render(<ChatExperience transport={transportWith(vi.fn().mockReturnValue(pending))} />);

    ask("첫 질문");
    fireEvent.change(screen.getByRole("textbox", { name: "민원 질문" }), {
      target: { value: "다음 질문" },
    });
    resolveResponse?.(SUCCESS_RESPONSE);

    await screen.findByText(SUCCESS_RESPONSE.summary);
    expect(screen.getByRole("textbox", { name: "민원 질문" })).toHaveValue("다음 질문");
  });

  it("shows a clear empty-office state without inventing institution details", async () => {
    const responseWithoutOffice = { ...SUCCESS_RESPONSE, office: null } satisfies ChatResponse;
    render(<ChatExperience transport={transportWith(vi.fn().mockResolvedValue(responseWithoutOffice))} />);
    fireEvent.change(screen.getByRole("combobox", { name: "지역 선택" }), {
      target: { value: "도담동" },
    });
    ask("전입신고 알려줘");

    expect(
      await screen.findByText("선택한 지역의 연결 가능한 공식 기관 정보가 없어요."),
    ).toBeInTheDocument();
  });

  it("keeps repeated institution card heading IDs unique across the transcript", async () => {
    const secondResponse = {
      ...SUCCESS_RESPONSE,
      request_id: "66666666-6666-4666-8666-666666666666",
    } satisfies ChatResponse;
    const send = vi.fn().mockResolvedValueOnce(SUCCESS_RESPONSE).mockResolvedValueOnce(secondResponse);
    render(<ChatExperience transport={transportWith(send)} />);
    fireEvent.change(screen.getByRole("combobox", { name: "지역 선택" }), {
      target: { value: "아름동" },
    });

    ask("전입신고 절차를 알려줘");
    await waitFor(() => expect(send).toHaveBeenCalledTimes(1));
    await screen.findByText("전입신고 절차를 알려줘");
    ask("전입신고 서류를 알려줘");

    await waitFor(() => expect(send).toHaveBeenCalledTimes(2));
    const officeHeadings = screen.getAllByRole("heading", { name: OFFICE.office_name });
    expect(new Set(officeHeadings.map((heading) => heading.id)).size).toBe(2);
  });
});
