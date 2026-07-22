// @vitest-environment jsdom

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
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
  window.localStorage.clear();
  window.sessionStorage.clear();
});

describe("local/private admin experience", () => {
  it("shows an accessible loading state, then masked failure data and the demo-only boundary", async () => {
    const pending = deferred<FailedQuestionListResponse>();
    const setItem = vi.spyOn(Storage.prototype, "setItem");
    render(<AdminExperience transport={createTransport({ listFailedQuestions: () => pending.promise })} />);

    expect(screen.getByText("운영 데이터를 불러오고 있어요.")).toBeInTheDocument();
    expect(screen.getByText("시연용 역할 선택 · 인증 아님")).toBeInTheDocument();

    pending.resolve({ items: [FAILURE], total: 1 });
    expect(await screen.findByRole("button", { name: /침대 프레임은 어떻게 버려요/ })).toBeInTheDocument();
    expect(screen.getByText(/^마스킹된 질문만 표시합니다\./)).toBeInTheDocument();
    expect(setItem).not.toHaveBeenCalled();
    expect(window.sessionStorage.length).toBe(0);
    expect(document.cookie).toBe("");
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
