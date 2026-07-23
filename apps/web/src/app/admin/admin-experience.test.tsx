// @vitest-environment jsdom

import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { components } from "../../../../../packages/shared-contracts/src/generated/api";

import {
  AdminExperience,
  type AdminActor,
  type AdminTransport,
} from "./admin-experience";

type FailedQuestion = components["schemas"]["FailedQuestion"];
type FailedQuestionListResponse = components["schemas"]["FailedQuestionListResponse"];
type KBCandidateCreate = components["schemas"]["KBCandidateCreate"];
type KBCandidateSummary = components["schemas"]["KBCandidateSummary"];

const FAILURE = {
  id: "11111111-1111-4111-8111-111111111111",
  intent: "BULKY_WASTE",
  fallback_reason: "INSUFFICIENT_GROUNDING",
  masked_question: "침대 프레임은 어떻게 버려요?",
  candidate_eligible: true,
  status: "NEW",
  created_at: "2026-07-24T01:00:00Z",
  text_expires_at: "2026-08-23T01:00:00Z",
  text_purged_at: null,
} satisfies FailedQuestion;

const GENERIC_FAILURE = {
  ...FAILURE,
  id: "33333333-3333-4333-8333-333333333333",
  masked_question: "책상 의자는 어떻게 버려요?",
} satisfies FailedQuestion;

const SECOND_BED_FAILURE = {
  ...FAILURE,
  id: "44444444-4444-4444-8444-444444444444",
  masked_question: "침대 1인용 프레임 수수료를 알려주세요.",
} satisfies FailedQuestion;

const WASTE_03_PAYLOAD = {
  failed_question_id: FAILURE.id,
  category: "BULKY_WASTE",
  title: "침대 프레임 배출 수수료",
  representative_question: "침대 2인용 프레임 수수료가 얼마예요?",
  answer_summary: "공식 품목표의 침대 프레임 수수료는 1인용침대 8,000원, 2인용침대 10,000원으로 표시됩니다.",
  procedure_steps: [
    "공식 품목표에서 침대 프레임의 1인용침대 또는 2인용침대 항목을 확인합니다.",
    "해당 수수료로 공식 배출 절차를 진행합니다.",
  ],
  required_documents: [],
  processing_time: null,
  fee: "1인용침대 8,000원; 2인용침대 10,000원",
  department: "세종특별자치시시설관리공단",
  source_title: "배출항목선택",
  source_url: "https://www.sjwaste.kr/wasteApp/appCategoryPopup.do?menuId=MENU00305",
  last_verified_at: "2026-07-18",
  caution: "공식 품목표의 1인용침대·2인용침대 항목을 그대로 따릅니다. 매트리스 포함 가격이나 실제 규격을 단정하지 않습니다.",
} satisfies KBCandidateCreate;

const DRAFT_CANDIDATE = {
  id: "22222222-2222-4222-8222-222222222222",
  failed_question_id: FAILURE.id,
  category: "BULKY_WASTE",
  title: "침대 프레임 배출 안내",
  representative_question: "침대 프레임은 어떻게 버리나요?",
  answer_summary: "침대 프레임은 대형폐기물로 신고한 뒤 배출해요.",
  procedure_steps: ["대형폐기물 배출을 신고해요."],
  required_documents: [],
  processing_time: null,
  fee: "규격별 수수료",
  department: "자원순환 담당",
  caution: null,
  source_title: "세종특별자치시 대형폐기물 안내",
  source_url: "https://example.invalid/official/waste",
  last_verified_at: "2026-07-20",
  data_origin: "OFFICIAL",
  status: "DRAFTED",
  created_by: "OPERATOR-LOCAL-001",
  reviewed_by: null,
  review_comment: null,
  activated_kb_id: null,
  approved_at: null,
  created_at: "2026-07-24T02:00:00Z",
  updated_at: "2026-07-24T02:00:00Z",
} satisfies KBCandidateSummary;

function candidate(status: KBCandidateSummary["status"]): KBCandidateSummary {
  return {
    ...DRAFT_CANDIDATE,
    status,
    reviewed_by: status === "APPROVED" || status === "REJECTED" ? "PM-LOCAL-001" : null,
    review_comment: status === "APPROVED" ? "공식 출처 확인" : status === "REJECTED" ? "근거 보완 필요" : null,
    activated_kb_id: status === "APPROVED" ? "KB-WASTE-03" : null,
    approved_at: status === "APPROVED" ? "2026-07-24T03:00:00Z" : null,
  };
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((next) => { resolve = next; });
  return { promise, resolve };
}

function createTransport(overrides: Partial<AdminTransport> = {}): AdminTransport {
  return {
    listFailedQuestions: vi.fn().mockResolvedValue({ items: [FAILURE], total: 1 }),
    getFailedQuestion: vi.fn().mockResolvedValue({ item: FAILURE }),
    confirmReason: vi.fn().mockResolvedValue({ id: FAILURE.id, status: "REASON_CONFIRMED" }),
    listCandidates: vi.fn().mockResolvedValue({ items: [], total: 0 }),
    createCandidate: vi.fn().mockResolvedValue({ id: DRAFT_CANDIDATE.id, status: "DRAFTED" }),
    submitCandidate: vi.fn().mockResolvedValue({ id: DRAFT_CANDIDATE.id, status: "PENDING_APPROVAL" }),
    reviewCandidate: vi.fn().mockResolvedValue({ id: DRAFT_CANDIDATE.id, status: "APPROVED" }),
    ...overrides,
  };
}

function actor(role: AdminActor["role"]): AdminActor {
  return role === "OPERATOR"
    ? { role, actorId: "OPERATOR-LOCAL-001" }
    : { role, actorId: "PM-LOCAL-001" };
}

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  window.localStorage.clear();
  window.sessionStorage.clear();
});

describe("local/private admin experience", () => {
  it("uses only the actual same-origin admin API in explicit actual mode", async () => {
    const fetcher = vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/api/v1/admin/failed-questions")) {
        return new Response(JSON.stringify({ items: [FAILURE], total: 1 }), {
          status: 200,
          headers: { "content-type": "application/json" },
        });
      }
      if (url.endsWith("/api/v1/admin/kb-candidates")) {
        return new Response(JSON.stringify({ items: [], total: 0 }), {
          status: 200,
          headers: { "content-type": "application/json" },
        });
      }
      void init;
      return new Response(null, { status: 404 });
    });

    render(<AdminExperience transportMode="actual" fetcher={fetcher as typeof fetch} />);

    expect(await screen.findByRole("button", { name: /침대 프레임은 어떻게 버려요/ })).toBeInTheDocument();
    expect(screen.getByText("실제 local DB API 연결")).toBeInTheDocument();
    expect(screen.queryByText("시연용 샘플 데이터")).not.toBeInTheDocument();
    expect(fetcher).toHaveBeenCalledTimes(2);
    for (const [, init] of fetcher.mock.calls) {
      expect(init?.headers).toMatchObject({
        "X-Demo-Actor-Id": "OPERATOR-LOCAL-001",
        "X-Demo-Role": "OPERATOR",
      });
    }
  });

  it("shows an accessible loading state, then masked failure data and the demo-only boundary", async () => {
    const pending = deferred<FailedQuestionListResponse>();
    const setItem = vi.spyOn(Storage.prototype, "setItem");
    render(<AdminExperience transport={createTransport({ listFailedQuestions: () => pending.promise })} />);

    expect(screen.getByText("운영 데이터를 불러오고 있어요.")).toBeInTheDocument();
    expect(screen.getByText("시연용 역할 선택 · 인증 아님")).toBeInTheDocument();
    expect(screen.getByText("시연용 샘플 데이터")).toBeInTheDocument();
    expect(screen.queryByText("실제 local DB API 연결")).not.toBeInTheDocument();

    pending.resolve({ items: [FAILURE], total: 1 });
    expect(await screen.findByRole("button", { name: /침대 프레임은 어떻게 버려요/ })).toBeInTheDocument();
    expect(screen.getByText(/^마스킹된 질문만 표시합니다\./)).toBeInTheDocument();
    expect(setItem).not.toHaveBeenCalled();
    expect(window.sessionStorage.length).toBe(0);
    expect(document.cookie).toBe("");
  });

  it("keeps the newest failure selected when detail requests resolve out of order", async () => {
    const olderDetail = deferred<{ item: FailedQuestion }>();
    const newerDetail = deferred<{ item: FailedQuestion }>();
    const transport = createTransport({
      listFailedQuestions: vi.fn().mockResolvedValue({ items: [GENERIC_FAILURE, FAILURE], total: 2 }),
      getFailedQuestion: vi.fn((_actor, id) => (
        id === FAILURE.id ? newerDetail.promise : olderDetail.promise
      )),
    });
    render(<AdminExperience transport={transport} />);

    const genericButton = await screen.findByRole("button", { name: /책상 의자는 어떻게 버려요/ });
    fireEvent.click(genericButton);
    fireEvent.click(screen.getByRole("button", { name: /침대 프레임은 어떻게 버려요/ }));

    await act(async () => {
      newerDetail.resolve({ item: FAILURE });
      await newerDetail.promise;
    });
    const detailPanel = screen.getByRole("heading", { name: "실패 질문 상세" }).closest("section");
    expect(detailPanel).not.toBeNull();
    expect(within(detailPanel!).getByText(FAILURE.masked_question!)).toBeInTheDocument();

    await act(async () => {
      olderDetail.resolve({ item: GENERIC_FAILURE });
      await olderDetail.promise;
    });
    expect(within(detailPanel!).getByText(FAILURE.masked_question!)).toBeInTheDocument();
    expect(within(detailPanel!).queryByText(GENERIC_FAILURE.masked_question!)).not.toBeInTheDocument();
  });

  it("clears selected failure, draft, and error when the demo role changes", async () => {
    const transport = createTransport({
      listFailedQuestions: vi.fn().mockResolvedValue({ items: [GENERIC_FAILURE, FAILURE], total: 2 }),
      getFailedQuestion: vi.fn(async (_actor, id) => {
        if (id === GENERIC_FAILURE.id) throw new Error("detail unavailable");
        return { item: FAILURE };
      }),
    });
    render(<AdminExperience transport={transport} />);

    fireEvent.click(await screen.findByRole("button", { name: /침대 프레임은 어떻게 버려요/ }));
    fireEvent.click(await screen.findByRole("button", { name: "사유 확정" }));
    fireEvent.click(await screen.findByRole("button", { name: "검수된 KB-WASTE-03 자료 불러오기" }));
    expect(screen.getByRole("textbox", { name: "후보 제목" })).toHaveValue(WASTE_03_PAYLOAD.title);

    fireEvent.click(screen.getByRole("button", { name: /책상 의자는 어떻게 버려요/ }));
    expect(await screen.findByRole("alert")).toBeInTheDocument();
    fireEvent.change(screen.getByRole("combobox", { name: "시연 역할" }), {
      target: { value: "APPROVER" },
    });

    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.getByText("왼쪽 목록에서 질문을 선택하세요.")).toBeInTheDocument();

    fireEvent.change(screen.getByRole("combobox", { name: "시연 역할" }), {
      target: { value: "OPERATOR" },
    });
    fireEvent.click(await screen.findByRole("button", { name: /침대 프레임은 어떻게 버려요/ }));
    fireEvent.click(await screen.findByRole("button", { name: "사유 확정" }));
    expect(await screen.findByRole("textbox", { name: "후보 제목" })).toHaveValue("");
  });

  it("ignores a reason confirmation that completes after the demo role changes", async () => {
    const confirmation = deferred<{ id: string; status: "REASON_CONFIRMED" }>();
    const transport = createTransport({
      confirmReason: vi.fn(() => confirmation.promise),
    });
    render(<AdminExperience transport={transport} />);

    fireEvent.click(await screen.findByRole("button", { name: /침대 프레임은 어떻게 버려요/ }));
    fireEvent.click(await screen.findByRole("button", { name: "사유 확정" }));
    fireEvent.change(screen.getByRole("combobox", { name: "시연 역할" }), {
      target: { value: "APPROVER" },
    });
    expect(screen.getByText("왼쪽 목록에서 질문을 선택하세요.")).toBeInTheDocument();

    await act(async () => {
      confirmation.resolve({ id: FAILURE.id, status: "REASON_CONFIRMED" });
      await confirmation.promise;
    });

    expect(screen.getByText("왼쪽 목록에서 질문을 선택하세요.")).toBeInTheDocument();
    expect(screen.queryByText("사유 확인 완료")).not.toBeInTheDocument();
  });

  it("sends one reason confirmation when the operator clicks twice in one render batch", async () => {
    const confirmation = deferred<{ id: string; status: "REASON_CONFIRMED" }>();
    const transport = createTransport({
      confirmReason: vi.fn(() => confirmation.promise),
    });
    render(<AdminExperience transport={transport} />);

    fireEvent.click(await screen.findByRole("button", { name: /침대 프레임은 어떻게 버려요/ }));
    const confirmButton = await screen.findByRole("button", { name: "사유 확정" });
    act(() => {
      confirmButton.click();
      confirmButton.click();
    });

    expect(transport.confirmReason).toHaveBeenCalledTimes(1);
    expect(confirmButton).toBeDisabled();

    await act(async () => {
      confirmation.resolve({ id: FAILURE.id, status: "REASON_CONFIRMED" });
      await confirmation.promise;
    });

    expect(await screen.findAllByText("사유 확인 완료")).not.toHaveLength(0);
  });

  it("ignores candidate completion and refresh after the demo role changes", async () => {
    const confirmedFailure = {
      ...FAILURE,
      status: "REASON_CONFIRMED",
    } satisfies FailedQuestion;
    const creation = deferred<{ id: string; status: "DRAFTED" }>();
    const listCandidates = vi.fn().mockResolvedValue({ items: [], total: 0 });
    const transport = createTransport({
      listFailedQuestions: vi.fn().mockResolvedValue({ items: [confirmedFailure], total: 1 }),
      getFailedQuestion: vi.fn().mockResolvedValue({ item: confirmedFailure }),
      listCandidates,
      createCandidate: vi.fn(() => creation.promise),
    });
    render(<AdminExperience transport={transport} />);

    fireEvent.click(await screen.findByRole("button", { name: /침대 프레임은 어떻게 버려요/ }));
    fireEvent.click(await screen.findByRole("button", { name: "검수된 KB-WASTE-03 자료 불러오기" }));
    fireEvent.click(screen.getByRole("button", { name: "KB 후보 작성" }));
    await waitFor(() => expect(transport.createCandidate).toHaveBeenCalledTimes(1));

    fireEvent.change(screen.getByRole("combobox", { name: "시연 역할" }), {
      target: { value: "APPROVER" },
    });
    expect(screen.getByText("왼쪽 목록에서 질문을 선택하세요.")).toBeInTheDocument();
    await waitFor(() => expect(listCandidates).toHaveBeenCalledTimes(2));

    await act(async () => {
      creation.resolve({ id: DRAFT_CANDIDATE.id, status: "DRAFTED" });
      await creation.promise;
      await Promise.resolve();
    });

    expect(listCandidates).toHaveBeenCalledTimes(2);
    expect(screen.getByText("왼쪽 목록에서 질문을 선택하세요.")).toBeInTheDocument();
    expect(screen.queryByText("KB 후보를 작성했습니다.")).not.toBeInTheDocument();
  });

  it("keeps failure B selected when confirmation for failure A completes later", async () => {
    const confirmation = deferred<{ id: string; status: "REASON_CONFIRMED" }>();
    const transport = createTransport({
      listFailedQuestions: vi.fn().mockResolvedValue({ items: [FAILURE, GENERIC_FAILURE], total: 2 }),
      getFailedQuestion: vi.fn(async (_actor, id) => ({
        item: id === FAILURE.id ? FAILURE : GENERIC_FAILURE,
      })),
      confirmReason: vi.fn(() => confirmation.promise),
    });
    render(<AdminExperience transport={transport} />);

    fireEvent.click(await screen.findByRole("button", { name: /침대 프레임은 어떻게 버려요/ }));
    fireEvent.click(await screen.findByRole("button", { name: "사유 확정" }));
    fireEvent.click(screen.getByRole("button", { name: /책상 의자는 어떻게 버려요/ }));

    const detailPanel = screen.getByRole("heading", { name: "실패 질문 상세" }).closest("section");
    expect(detailPanel).not.toBeNull();
    expect(await within(detailPanel!).findByText(GENERIC_FAILURE.masked_question!)).toBeInTheDocument();

    await act(async () => {
      confirmation.resolve({ id: FAILURE.id, status: "REASON_CONFIRMED" });
      await confirmation.promise;
    });

    expect(within(detailPanel!).getByText(GENERIC_FAILURE.masked_question!)).toBeInTheDocument();
    expect(within(detailPanel!).queryByText(FAILURE.masked_question!)).not.toBeInTheDocument();
    expect(screen.queryByText("사유 확인 완료")).not.toBeInTheDocument();
  });

  it("preserves failure B draft when candidate creation for failure A completes later", async () => {
    const confirmedA = { ...FAILURE, status: "REASON_CONFIRMED" } satisfies FailedQuestion;
    const confirmedB = { ...SECOND_BED_FAILURE, status: "REASON_CONFIRMED" } satisfies FailedQuestion;
    const creation = deferred<{ id: string; status: "DRAFTED" }>();
    const transport = createTransport({
      listFailedQuestions: vi.fn().mockResolvedValue({ items: [confirmedA, confirmedB], total: 2 }),
      getFailedQuestion: vi.fn(async (_actor, id) => ({
        item: id === confirmedA.id ? confirmedA : confirmedB,
      })),
      createCandidate: vi.fn(() => creation.promise),
    });
    render(<AdminExperience transport={transport} />);

    fireEvent.click(await screen.findByRole("button", { name: /침대 프레임은 어떻게 버려요/ }));
    fireEvent.click(await screen.findByRole("button", { name: "검수된 KB-WASTE-03 자료 불러오기" }));
    fireEvent.click(screen.getByRole("button", { name: "KB 후보 작성" }));
    await waitFor(() => expect(transport.createCandidate).toHaveBeenCalledTimes(1));

    fireEvent.click(screen.getByRole("button", { name: /침대 1인용 프레임 수수료/ }));
    const detailPanel = screen.getByRole("heading", { name: "실패 질문 상세" }).closest("section");
    expect(detailPanel).not.toBeNull();
    expect(await within(detailPanel!).findByText(confirmedB.masked_question!)).toBeInTheDocument();
    fireEvent.click(await screen.findByRole("button", { name: "검수된 KB-WASTE-03 자료 불러오기" }));
    expect(screen.getByRole("textbox", { name: "후보 제목" })).toHaveValue(WASTE_03_PAYLOAD.title);

    await act(async () => {
      creation.resolve({ id: DRAFT_CANDIDATE.id, status: "DRAFTED" });
      await creation.promise;
      await Promise.resolve();
    });

    expect(within(detailPanel!).getByText(confirmedB.masked_question!)).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "후보 제목" })).toHaveValue(WASTE_03_PAYLOAD.title);
    expect(screen.queryByText("KB 후보를 작성했습니다.")).not.toBeInTheDocument();
  });

  it("loads the reviewed KB-WASTE-03 template only for the eligible bed-frame failure and submits its full canonical payload", async () => {
    const transport = createTransport({
      listFailedQuestions: vi.fn().mockResolvedValue({ items: [GENERIC_FAILURE, FAILURE], total: 2 }),
      getFailedQuestion: vi.fn(async (_actor, id) => ({
        item: id === FAILURE.id ? FAILURE : GENERIC_FAILURE,
      })),
    });
    render(<AdminExperience transport={transport} />);

    fireEvent.click(await screen.findByRole("button", { name: /책상 의자는 어떻게 버려요/ }));
    fireEvent.click(await screen.findByRole("button", { name: "사유 확정" }));
    expect(await screen.findByRole("heading", { name: "KB 후보 작성" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "검수된 KB-WASTE-03 자료 불러오기" })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /침대 프레임은 어떻게 버려요/ }));
    fireEvent.click(await screen.findByRole("button", { name: "사유 확정" }));
    const templateButton = await screen.findByRole("button", { name: "검수된 KB-WASTE-03 자료 불러오기" });
    fireEvent.click(templateButton);

    expect(screen.getByRole("textbox", { name: "후보 제목" })).toHaveValue(WASTE_03_PAYLOAD.title);
    expect(screen.getByRole("textbox", { name: "대표 질문" })).toHaveValue(WASTE_03_PAYLOAD.representative_question);
    expect(screen.getByRole("textbox", { name: "답변 요약" })).toHaveValue(WASTE_03_PAYLOAD.answer_summary);
    expect(screen.getByRole("textbox", { name: "담당 부서" })).toHaveValue(WASTE_03_PAYLOAD.department);
    expect(screen.getByRole("textbox", { name: "공식 출처명" })).toHaveValue(WASTE_03_PAYLOAD.source_title);
    expect(screen.getByRole("textbox", { name: "공식 출처 URL" })).toHaveValue(WASTE_03_PAYLOAD.source_url);
    expect(screen.getByLabelText("공식 확인일")).toHaveValue(WASTE_03_PAYLOAD.last_verified_at);
    const preview = screen.getByRole("region", { name: "검수 전 확인" });
    expect(within(preview).getByText(WASTE_03_PAYLOAD.procedure_steps[0])).toBeInTheDocument();
    expect(within(preview).getByText(WASTE_03_PAYLOAD.procedure_steps[1])).toBeInTheDocument();
    expect(within(preview).getByText(WASTE_03_PAYLOAD.fee!)).toBeInTheDocument();
    expect(within(preview).getByText(WASTE_03_PAYLOAD.caution!)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "KB 후보 작성" }));

    await waitFor(() => expect(transport.createCandidate).toHaveBeenCalledWith(actor("OPERATOR"), WASTE_03_PAYLOAD));
    const submitted = vi.mocked(transport.createCandidate).mock.calls[0]?.[1] as Record<string, unknown>;
    expect(submitted).not.toHaveProperty("public_id");
  });

  it("keeps later KB-WASTE-03 submissions canonical when a transport mutates submitted arrays", async () => {
    const received: KBCandidateCreate[] = [];
    const createCandidate = vi.fn(async (_actor: AdminActor, request: KBCandidateCreate) => {
      received.push({
        ...request,
        procedure_steps: [...(request.procedure_steps ?? [])],
        required_documents: [...(request.required_documents ?? [])],
      });
      request.procedure_steps![0] = "transport-mutated procedure";
      request.required_documents!.push("transport-mutated document");
      return { id: DRAFT_CANDIDATE.id, status: "DRAFTED" as const };
    });
    const transport = createTransport({ createCandidate });
    render(<AdminExperience transport={transport} />);

    fireEvent.click(await screen.findByRole("button", { name: /침대 프레임은 어떻게 버려요/ }));
    fireEvent.click(await screen.findByRole("button", { name: "사유 확정" }));

    for (let submission = 1; submission <= 2; submission += 1) {
      fireEvent.click(await screen.findByRole("button", { name: "검수된 KB-WASTE-03 자료 불러오기" }));
      fireEvent.click(screen.getByRole("button", { name: "KB 후보 작성" }));
      await waitFor(() => expect(received).toHaveLength(submission));
    }

    expect(received[1]).toEqual(WASTE_03_PAYLOAD);
  });

  it("creates one candidate when the operator submits the form twice in one render batch", async () => {
    const confirmedFailure = {
      ...FAILURE,
      status: "REASON_CONFIRMED",
    } satisfies FailedQuestion;
    const creation = deferred<{ id: string; status: "DRAFTED" }>();
    const listCandidates = vi.fn()
      .mockResolvedValueOnce({ items: [], total: 0 })
      .mockResolvedValueOnce({ items: [DRAFT_CANDIDATE], total: 1 });
    const transport = createTransport({
      listFailedQuestions: vi.fn().mockResolvedValue({ items: [confirmedFailure], total: 1 }),
      getFailedQuestion: vi.fn().mockResolvedValue({ item: confirmedFailure }),
      listCandidates,
      createCandidate: vi.fn(() => creation.promise),
    });
    render(<AdminExperience transport={transport} />);

    fireEvent.click(await screen.findByRole("button", { name: /침대 프레임은 어떻게 버려요/ }));
    fireEvent.click(await screen.findByRole("button", { name: "검수된 KB-WASTE-03 자료 불러오기" }));
    const createButton = screen.getByRole("button", { name: "KB 후보 작성" });
    const form = createButton.closest("form");
    expect(form).not.toBeNull();
    act(() => {
      form!.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
      form!.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
    });

    expect(transport.createCandidate).toHaveBeenCalledTimes(1);
    expect(createButton).toBeDisabled();

    await act(async () => {
      creation.resolve({ id: DRAFT_CANDIDATE.id, status: "DRAFTED" });
      await creation.promise;
    });

    expect(await screen.findByRole("heading", { name: DRAFT_CANDIDATE.title })).toBeInTheDocument();
    expect(screen.getByText("KB 후보를 작성했습니다.")).toBeInTheDocument();
  });

  it("moves an eligible failure through reason confirmation, draft, submit, separate approval, and ACTIVE", async () => {
    const listCandidates = vi.fn()
      .mockResolvedValueOnce({ items: [], total: 0 })
      .mockResolvedValueOnce({ items: [DRAFT_CANDIDATE], total: 1 })
      .mockResolvedValueOnce({ items: [candidate("PENDING_APPROVAL")], total: 1 })
      .mockResolvedValueOnce({ items: [candidate("PENDING_APPROVAL")], total: 1 })
      .mockResolvedValueOnce({ items: [candidate("APPROVED")], total: 1 });
    const transport = createTransport({ listCandidates });
    render(<AdminExperience transport={transport} />);

    fireEvent.click(await screen.findByRole("button", { name: /침대 프레임은 어떻게 버려요/ }));
    expect(await screen.findByRole("heading", { name: "실패 질문 상세" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "사유 확정" }));
    expect(await screen.findAllByText("사유 확인 완료")).not.toHaveLength(0);

    fireEvent.change(screen.getByRole("textbox", { name: "후보 제목" }), {
      target: { value: DRAFT_CANDIDATE.title },
    });
    fireEvent.change(screen.getByRole("textbox", { name: "대표 질문" }), {
      target: { value: DRAFT_CANDIDATE.representative_question },
    });
    fireEvent.change(screen.getByRole("textbox", { name: "답변 요약" }), {
      target: { value: DRAFT_CANDIDATE.answer_summary },
    });
    fireEvent.change(screen.getByRole("textbox", { name: "담당 부서" }), {
      target: { value: DRAFT_CANDIDATE.department },
    });
    fireEvent.change(screen.getByRole("textbox", { name: "공식 출처명" }), {
      target: { value: DRAFT_CANDIDATE.source_title },
    });
    fireEvent.change(screen.getByRole("textbox", { name: "공식 출처 URL" }), {
      target: { value: DRAFT_CANDIDATE.source_url },
    });
    fireEvent.change(screen.getByLabelText("공식 확인일"), {
      target: { value: DRAFT_CANDIDATE.last_verified_at },
    });
    fireEvent.click(screen.getByRole("button", { name: "KB 후보 작성" }));

    expect(await screen.findByRole("heading", { name: DRAFT_CANDIDATE.title })).toBeInTheDocument();
    expect(transport.createCandidate).toHaveBeenCalledWith(
      actor("OPERATOR"),
      expect.objectContaining({
        failed_question_id: FAILURE.id,
        category: "BULKY_WASTE",
        title: DRAFT_CANDIDATE.title,
      } satisfies Partial<KBCandidateCreate>),
    );

    fireEvent.click(screen.getByRole("button", { name: "승인 요청" }));
    expect(await screen.findByText("승인 대기")).toBeInTheDocument();

    fireEvent.change(screen.getByRole("combobox", { name: "시연 역할" }), {
      target: { value: "APPROVER" },
    });
    fireEvent.change(await screen.findByRole("textbox", { name: "검수 의견" }), {
      target: { value: "공식 출처 확인" },
    });
    fireEvent.click(screen.getByRole("button", { name: "승인하고 ACTIVE 반영" }));

    expect(await screen.findByText("ACTIVE 반영 완료")).toBeInTheDocument();
    expect(screen.getByText("KB-WASTE-03")).toBeInTheDocument();
    expect(screen.getByText("작성 OPERATOR-LOCAL-001")).toBeInTheDocument();
    expect(screen.getByText("검수 PM-LOCAL-001")).toBeInTheDocument();
    expect(transport.reviewCandidate).toHaveBeenCalledWith(actor("APPROVER"), DRAFT_CANDIDATE.id, {
      decision: "APPROVED",
      review_comment: "공식 출처 확인",
    });
  });

  it("sends only one submit request when an operator rapidly clicks twice", async () => {
    const submission = deferred<{ id: string; status: "PENDING_APPROVAL" }>();
    const transport = createTransport({
      listCandidates: vi.fn().mockResolvedValue({ items: [DRAFT_CANDIDATE], total: 1 }),
      submitCandidate: vi.fn(() => submission.promise),
    });
    render(<AdminExperience transport={transport} />);

    const card = await screen.findByRole("article", { name: DRAFT_CANDIDATE.title });
    const submitButton = within(card).getByRole("button", { name: "승인 요청" });
    fireEvent.click(submitButton);
    fireEvent.click(submitButton);

    expect(transport.submitCandidate).toHaveBeenCalledTimes(1);
    expect(submitButton).toBeDisabled();

    await act(async () => {
      submission.resolve({ id: DRAFT_CANDIDATE.id, status: "PENDING_APPROVAL" });
      await submission.promise;
    });
  });

  it("sends only one review request when an approver rapidly clicks twice", async () => {
    const review = deferred<{ id: string; status: "APPROVED" }>();
    const pending = candidate("PENDING_APPROVAL");
    const transport = createTransport({
      listCandidates: vi.fn().mockResolvedValue({ items: [pending], total: 1 }),
      reviewCandidate: vi.fn(() => review.promise),
    });
    render(<AdminExperience transport={transport} initialRole="APPROVER" />);

    const card = await screen.findByRole("article", { name: DRAFT_CANDIDATE.title });
    fireEvent.change(within(card).getByRole("textbox", { name: "검수 의견" }), {
      target: { value: "공식 출처 확인" },
    });
    const approveButton = within(card).getByRole("button", { name: "승인하고 ACTIVE 반영" });
    fireEvent.click(approveButton);
    fireEvent.click(approveButton);

    expect(transport.reviewCandidate).toHaveBeenCalledTimes(1);
    expect(approveButton).toBeDisabled();

    await act(async () => {
      review.resolve({ id: DRAFT_CANDIDATE.id, status: "APPROVED" });
      await review.promise;
    });
  });

  it("does not let a previous actor action refresh overwrite the current actor candidate state", async () => {
    const submission = deferred<{ id: string; status: "PENDING_APPROVAL" }>();
    const pending = candidate("PENDING_APPROVAL");
    const listCandidates = vi.fn()
      .mockResolvedValueOnce({ items: [DRAFT_CANDIDATE], total: 1 })
      .mockResolvedValueOnce({ items: [pending], total: 1 })
      .mockResolvedValue({ items: [DRAFT_CANDIDATE], total: 1 });
    const transport = createTransport({
      listCandidates,
      submitCandidate: vi.fn(() => submission.promise),
    });
    render(<AdminExperience transport={transport} />);

    const operatorCard = await screen.findByRole("article", { name: DRAFT_CANDIDATE.title });
    fireEvent.click(within(operatorCard).getByRole("button", { name: "승인 요청" }));
    await waitFor(() => expect(transport.submitCandidate).toHaveBeenCalledTimes(1));

    fireEvent.change(screen.getByRole("combobox", { name: "시연 역할" }), {
      target: { value: "APPROVER" },
    });
    expect(await screen.findByText("승인 대기")).toBeInTheDocument();

    await act(async () => {
      submission.resolve({ id: DRAFT_CANDIDATE.id, status: "PENDING_APPROVAL" });
      await submission.promise;
      await Promise.resolve();
    });

    expect(screen.getByText("승인 대기")).toBeInTheDocument();
    expect(screen.queryByText("초안")).not.toBeInTheDocument();
    expect(listCandidates).toHaveBeenCalledTimes(2);
  });

  it("prevents an author from reviewing their own candidate", async () => {
    const selfAuthored = {
      ...candidate("PENDING_APPROVAL"),
      created_by: "PM-LOCAL-001",
    } satisfies KBCandidateSummary;
    const transport = createTransport({
      listCandidates: vi.fn().mockResolvedValue({ items: [selfAuthored], total: 1 }),
    });
    render(<AdminExperience transport={transport} initialRole="APPROVER" />);

    const ownCandidate = await screen.findByRole("article", { name: DRAFT_CANDIDATE.title });
    expect(within(ownCandidate).getByText("작성자와 검수자가 같아 검수할 수 없습니다.")).toBeInTheDocument();
    expect(within(ownCandidate).getByRole("button", { name: "반려" })).toBeDisabled();
    expect(within(ownCandidate).getByRole("button", { name: "승인하고 ACTIVE 반영" })).toBeDisabled();
  });

  it("lets a different approver reject a pending candidate with a review comment", async () => {
    const pending = candidate("PENDING_APPROVAL");
    const transport = createTransport({
      listCandidates: vi.fn()
        .mockResolvedValueOnce({ items: [pending], total: 1 })
        .mockResolvedValueOnce({ items: [candidate("REJECTED")], total: 1 }),
      reviewCandidate: vi.fn().mockResolvedValue({ id: DRAFT_CANDIDATE.id, status: "REJECTED" }),
    });
    render(<AdminExperience transport={transport} initialRole="APPROVER" />);

    const card = await screen.findByRole("article", { name: DRAFT_CANDIDATE.title });
    fireEvent.change(within(card).getByRole("textbox", { name: "검수 의견" }), {
      target: { value: "근거 보완 필요" },
    });
    const rejectButton = within(card).getByRole("button", { name: "반려" });
    expect(rejectButton).not.toBeDisabled();
    fireEvent.click(rejectButton);

    await waitFor(() => expect(transport.reviewCandidate).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(within(card).queryByRole("button", { name: "반려" })).not.toBeInTheDocument());
    expect(within(card).getByText("반려")).toBeInTheDocument();
    expect(transport.reviewCandidate).toHaveBeenCalledWith(actor("APPROVER"), DRAFT_CANDIDATE.id, {
      decision: "REJECTED",
      review_comment: "근거 보완 필요",
    });
  });

  it("never lets a demo MOCK candidate be approved into ACTIVE", async () => {
    const mockCandidate = {
      ...candidate("PENDING_APPROVAL"),
      data_origin: "MOCK",
    } satisfies KBCandidateSummary;
    const transport = createTransport({
      listCandidates: vi.fn().mockResolvedValue({ items: [mockCandidate], total: 1 }),
    });
    render(<AdminExperience transport={transport} initialRole="APPROVER" />);

    const card = await screen.findByRole("article", { name: DRAFT_CANDIDATE.title });
    fireEvent.change(within(card).getByRole("textbox", { name: "검수 의견" }), {
      target: { value: "시연용 샘플 확인" },
    });

    expect(within(card).getByText("시연용 샘플은 ACTIVE로 승인할 수 없습니다.")).toBeInTheDocument();
    expect(within(card).getByRole("button", { name: "승인하고 ACTIVE 반영" })).toBeDisabled();
    expect(within(card).getByRole("button", { name: "반려" })).not.toBeDisabled();
  });

  it("shows expired text safely and never offers candidate authoring for an ineligible failure", async () => {
    const ineligible = {
      ...FAILURE,
      fallback_reason: "PERSONAL_LOOKUP",
      masked_question: null,
      candidate_eligible: false,
      status: "REASON_CONFIRMED",
      text_purged_at: "2026-08-23T01:05:00Z",
    } satisfies FailedQuestion;
    const transport = createTransport({
      listFailedQuestions: vi.fn().mockResolvedValue({ items: [ineligible], total: 1 }),
      getFailedQuestion: vi.fn().mockResolvedValue({ item: ineligible }),
    });
    render(<AdminExperience transport={transport} />);

    fireEvent.click(await screen.findByRole("button", { name: /보관 기간이 지나/ }));
    expect(await screen.findByText("후보 전환 대상이 아닙니다.")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "KB 후보 작성" })).not.toBeInTheDocument();
    expect(screen.getAllByText("보관 기간이 지나 질문 텍스트가 파기되었습니다.")).toHaveLength(2);
  });

  it("renders empty and value-free error states with retry", async () => {
    const listFailedQuestions = vi.fn()
      .mockRejectedValueOnce(new Error("raw upstream payload must stay hidden"))
      .mockResolvedValueOnce({ items: [], total: 0 });
    render(<AdminExperience transport={createTransport({ listFailedQuestions })} />);

    expect(await screen.findByRole("alert")).toHaveTextContent("운영 데이터를 불러오지 못했어요.");
    expect(screen.queryByText(/raw upstream/)).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "다시 불러오기" }));
    expect(await screen.findByText("확인할 실패 질문이 없습니다.")).toBeInTheDocument();
    expect(listFailedQuestions).toHaveBeenCalledTimes(2);
  });
});
