"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import type { components } from "../../../../../packages/shared-contracts/src/generated/api";

import styles from "./admin.module.css";

type CandidateReviewRequest = components["schemas"]["CandidateReviewRequest"];
type FailedQuestion = components["schemas"]["FailedQuestion"];
type FailedQuestionDetailResponse = components["schemas"]["FailedQuestionDetailResponse"];
type FailedQuestionListResponse = components["schemas"]["FailedQuestionListResponse"];
type KBCandidateCreate = components["schemas"]["KBCandidateCreate"];
type KBCandidateCreateResponse = components["schemas"]["KBCandidateCreateResponse"];
type KBCandidateListResponse = components["schemas"]["KBCandidateListResponse"];
type KBCandidateReviewResponse = components["schemas"]["KBCandidateReviewResponse"];
type KBCandidateSubmitResponse = components["schemas"]["KBCandidateSubmitResponse"];
type KBCandidateSummary = components["schemas"]["KBCandidateSummary"];
type ReasonConfirmationRequest = components["schemas"]["ReasonConfirmationRequest"];
type ReasonConfirmationResponse = components["schemas"]["ReasonConfirmationResponse"];

export type AdminActor = Readonly<{
  role: "OPERATOR" | "APPROVER";
  actorId: string;
}>;

export interface AdminTransport {
  listFailedQuestions(actor: AdminActor): Promise<FailedQuestionListResponse>;
  getFailedQuestion(actor: AdminActor, id: string): Promise<FailedQuestionDetailResponse>;
  confirmReason(
    actor: AdminActor,
    id: string,
    request: ReasonConfirmationRequest,
  ): Promise<ReasonConfirmationResponse>;
  listCandidates(actor: AdminActor): Promise<KBCandidateListResponse>;
  createCandidate(actor: AdminActor, request: KBCandidateCreate): Promise<KBCandidateCreateResponse>;
  submitCandidate(actor: AdminActor, id: string): Promise<KBCandidateSubmitResponse>;
  reviewCandidate(
    actor: AdminActor,
    id: string,
    request: CandidateReviewRequest,
  ): Promise<KBCandidateReviewResponse>;
}

const ACTORS: Record<AdminActor["role"], AdminActor> = {
  OPERATOR: { role: "OPERATOR", actorId: "OPERATOR-LOCAL-001" },
  APPROVER: { role: "APPROVER", actorId: "PM-LOCAL-001" },
};

const STATUS_LABELS: Record<KBCandidateSummary["status"], string> = {
  DRAFTED: "작성 중",
  PENDING_APPROVAL: "승인 대기",
  APPROVED: "ACTIVE 반영 완료",
  REJECTED: "반려",
};

const INTENT_LABELS: Record<FailedQuestion["intent"], string> = {
  MOVE_IN_RESIDENT_REGISTRATION: "전입·주민등록",
  CERTIFICATE_ISSUANCE: "증명서 발급",
  BULKY_WASTE: "대형폐기물",
  LOCAL_TAX_GENERAL: "지방세 일반 안내",
};

type CandidateDraft = Pick<
  KBCandidateCreate,
  | "title"
  | "representative_question"
  | "answer_summary"
  | "department"
  | "source_title"
  | "source_url"
  | "last_verified_at"
>;

const EMPTY_DRAFT: CandidateDraft = {
  title: "",
  representative_question: "",
  answer_summary: "",
  department: "",
  source_title: "",
  source_url: "",
  last_verified_at: "",
};

function safeMessage(error: unknown) {
  void error;
  return "운영 데이터를 불러오지 못했어요. 잠시 후 다시 시도해 주세요.";
}

function createFixtureAdminTransport(): AdminTransport {
  const failure: FailedQuestion = {
    id: "10000000-0000-4000-8000-000000000001",
    intent: "BULKY_WASTE",
    fallback_reason: "INSUFFICIENT_GROUNDING",
    masked_question: "침대 프레임은 어떻게 버려요?",
    candidate_eligible: true,
    status: "NEW",
    created_at: "2026-07-24T01:00:00Z",
    text_expires_at: "2026-08-23T01:00:00Z",
    text_purged_at: null,
  };
  let failures = [failure];
  let candidates: KBCandidateSummary[] = [];

  return {
    async listFailedQuestions() {
      return { items: failures, total: failures.length };
    },
    async getFailedQuestion(_actor, id) {
      const item = failures.find((entry) => entry.id === id);
      if (!item) throw new Error("not found");
      return { item };
    },
    async confirmReason(actor, id, request) {
      if (actor.role !== "OPERATOR") throw new Error("forbidden");
      failures = failures.map((entry) => entry.id === id
        ? { ...entry, fallback_reason: request.reason, status: "REASON_CONFIRMED" }
        : entry);
      return { id, status: "REASON_CONFIRMED" };
    },
    async listCandidates() {
      return { items: candidates, total: candidates.length };
    },
    async createCandidate(actor, request) {
      if (actor.role !== "OPERATOR") throw new Error("forbidden");
      const id = "20000000-0000-4000-8000-000000000001";
      candidates = [{
        ...request,
        id,
        procedure_steps: request.procedure_steps ?? [],
        required_documents: request.required_documents ?? [],
        processing_time: request.processing_time ?? null,
        fee: request.fee ?? null,
        caution: request.caution ?? null,
        data_origin: "MOCK",
        status: "DRAFTED",
        created_by: actor.actorId,
        reviewed_by: null,
        review_comment: null,
        activated_kb_id: null,
        approved_at: null,
        created_at: "2026-07-24T02:00:00Z",
        updated_at: "2026-07-24T02:00:00Z",
      }];
      return { id, status: "DRAFTED" };
    },
    async submitCandidate(actor, id) {
      if (actor.role !== "OPERATOR") throw new Error("forbidden");
      candidates = candidates.map((entry) => entry.id === id
        ? { ...entry, status: "PENDING_APPROVAL" }
        : entry);
      return { id, status: "PENDING_APPROVAL" };
    },
    async reviewCandidate(actor, id, request) {
      const current = candidates.find((entry) => entry.id === id);
      if (actor.role !== "APPROVER" || !current || current.created_by === actor.actorId) {
        throw new Error("forbidden");
      }
      if (request.decision === "APPROVED" && current.data_origin !== "OFFICIAL") {
        throw new Error("mock candidates cannot become ACTIVE");
      }
      candidates = candidates.map((entry) => entry.id === id
        ? {
            ...entry,
            status: request.decision,
            reviewed_by: actor.actorId,
            review_comment: request.review_comment,
            approved_at: request.decision === "APPROVED" ? "2026-07-24T03:00:00Z" : null,
            activated_kb_id: request.decision === "APPROVED" ? "KB-WASTE-03-DEMO" : null,
          }
        : entry);
      return { id, status: request.decision };
    },
  };
}

function StatusBadge({ status }: { status: KBCandidateSummary["status"] }) {
  return <span className={styles.statusBadge}>{STATUS_LABELS[status]}</span>;
}

function FailureText({ failure }: { failure: FailedQuestion }) {
  if (failure.masked_question) return <span className={styles.maskedQuestion}>{failure.masked_question}</span>;
  return <span className={styles.purgedText}>보관 기간이 지나 질문 텍스트가 파기되었습니다.</span>;
}

function CandidateCard({
  actor,
  candidate,
  busy,
  onRefresh,
  transport,
}: {
  actor: AdminActor;
  candidate: KBCandidateSummary;
  busy: boolean;
  onRefresh: () => Promise<void>;
  transport: AdminTransport;
}) {
  const [reviewComment, setReviewComment] = useState("");
  const [actionError, setActionError] = useState<string | null>(null);
  const isOwnCandidate = candidate.created_by === actor.actorId;
  const canReview = actor.role === "APPROVER" && candidate.status === "PENDING_APPROVAL" && !isOwnCandidate;
  const canApprove = canReview && candidate.data_origin === "OFFICIAL";

  async function submit() {
    setActionError(null);
    try {
      await transport.submitCandidate(actor, candidate.id);
      await onRefresh();
    } catch {
      setActionError("승인 요청을 처리하지 못했어요.");
    }
  }

  async function review(decision: CandidateReviewRequest["decision"]) {
    setActionError(null);
    try {
      await transport.reviewCandidate(actor, candidate.id, {
        decision,
        review_comment: reviewComment.trim(),
      });
      await onRefresh();
    } catch {
      setActionError("검수 결과를 반영하지 못했어요.");
    }
  }

  return (
    <article className={styles.candidateCard} aria-label={candidate.title}>
      <div className={styles.cardHeading}>
        <div>
          <p className={styles.kicker}>KB 후보</p>
          <h3>{candidate.title}</h3>
        </div>
        <StatusBadge status={candidate.status} />
      </div>
      {candidate.data_origin === "MOCK" ? <p className={styles.mockBadge}>시연용 샘플</p> : null}
      <p>{candidate.answer_summary}</p>
      <dl className={styles.auditList}>
        <div><dt>작성자</dt><dd>작성 {candidate.created_by}</dd></div>
        <div><dt>검수자</dt><dd>{candidate.reviewed_by ? `검수 ${candidate.reviewed_by}` : "아직 없음"}</dd></div>
        <div><dt>공식 출처</dt><dd><a href={candidate.source_url}>{candidate.source_title}</a></dd></div>
        <div><dt>확인일</dt><dd><time dateTime={candidate.last_verified_at}>{candidate.last_verified_at}</time></dd></div>
        {candidate.activated_kb_id ? <div><dt>ACTIVE KB</dt><dd>{candidate.activated_kb_id}</dd></div> : null}
      </dl>

      {actor.role === "OPERATOR" && candidate.status === "DRAFTED" ? (
        <button className={styles.primaryButton} type="button" disabled={busy} onClick={() => void submit()}>
          승인 요청
        </button>
      ) : null}

      {actor.role === "APPROVER" && candidate.status === "PENDING_APPROVAL" ? (
        <div className={styles.reviewPanel}>
          {isOwnCandidate ? <p>작성자와 검수자가 같아 검수할 수 없습니다.</p> : null}
          {candidate.data_origin === "MOCK" ? <p>시연용 샘플은 ACTIVE로 승인할 수 없습니다.</p> : null}
          <label htmlFor={`review-comment-${candidate.id}`}>검수 의견</label>
          <textarea
            id={`review-comment-${candidate.id}`}
            rows={3}
            value={reviewComment}
            onChange={(event) => setReviewComment(event.target.value)}
          />
          <div className={styles.buttonRow}>
            <button
              className={styles.primaryButton}
              type="button"
              disabled={!canApprove || busy || !reviewComment.trim()}
              onClick={() => void review("APPROVED")}
            >
              승인하고 ACTIVE 반영
            </button>
            <button
              className={styles.secondaryButton}
              type="button"
              disabled={!canReview || busy || !reviewComment.trim()}
              onClick={() => void review("REJECTED")}
            >
              반려
            </button>
          </div>
        </div>
      ) : null}
      {candidate.review_comment ? <p className={styles.reviewComment}>검수 의견: {candidate.review_comment}</p> : null}
      {actionError ? <p role="alert" className={styles.inlineError}>{actionError}</p> : null}
    </article>
  );
}

export function AdminExperience({
  transport: providedTransport,
  initialRole = "OPERATOR",
}: {
  transport?: AdminTransport;
  initialRole?: AdminActor["role"];
}) {
  const usesFixture = !providedTransport;
  const [transport] = useState(() => providedTransport ?? createFixtureAdminTransport());
  const [role, setRole] = useState<AdminActor["role"]>(initialRole);
  const actor = ACTORS[role];
  const [failures, setFailures] = useState<FailedQuestion[]>([]);
  const [candidates, setCandidates] = useState<KBCandidateSummary[]>([]);
  const [selectedFailure, setSelectedFailure] = useState<FailedQuestion | null>(null);
  const [draft, setDraft] = useState<CandidateDraft>(EMPTY_DRAFT);
  const [isLoading, setIsLoading] = useState(true);
  const [isBusy, setIsBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [announcement, setAnnouncement] = useState("");

  const refreshCandidates = useCallback(async () => {
    const response = await transport.listCandidates(actor);
    setCandidates(response.items);
  }, [actor, transport]);

  const loadDashboard = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [failureResponse, candidateResponse] = await Promise.all([
        transport.listFailedQuestions(actor),
        transport.listCandidates(actor),
      ]);
      setFailures(failureResponse.items);
      setCandidates(candidateResponse.items);
    } catch (caught) {
      setError(safeMessage(caught));
    } finally {
      setIsLoading(false);
    }
  }, [actor, transport]);

  useEffect(() => {
    let cancelled = false;

    Promise.all([
      transport.listFailedQuestions(actor),
      transport.listCandidates(actor),
    ]).then(([failureResponse, candidateResponse]) => {
      if (cancelled) return;
      setFailures(failureResponse.items);
      setCandidates(candidateResponse.items);
      setError(null);
    }).catch((caught: unknown) => {
      if (!cancelled) setError(safeMessage(caught));
    }).finally(() => {
      if (!cancelled) setIsLoading(false);
    });

    return () => { cancelled = true; };
  }, [actor, transport]);

  const selectedHasCandidate = useMemo(
    () => selectedFailure ? candidates.some((item) => item.failed_question_id === selectedFailure.id) : false,
    [candidates, selectedFailure],
  );

  async function openFailure(id: string) {
    setIsBusy(true);
    setError(null);
    try {
      const response = await transport.getFailedQuestion(actor, id);
      setSelectedFailure(response.item);
      setDraft(EMPTY_DRAFT);
    } catch (caught) {
      setError(safeMessage(caught));
    } finally {
      setIsBusy(false);
    }
  }

  async function confirmReason() {
    if (!selectedFailure) return;
    setIsBusy(true);
    try {
      await transport.confirmReason(actor, selectedFailure.id, {
        reason: selectedFailure.fallback_reason,
      });
      const confirmed: FailedQuestion = { ...selectedFailure, status: "REASON_CONFIRMED" };
      setSelectedFailure(confirmed);
      setFailures((current) => current.map((item) => item.id === confirmed.id ? confirmed : item));
      setAnnouncement("사유 확인 완료");
    } catch {
      setError("사유를 확정하지 못했어요. 잠시 후 다시 시도해 주세요.");
    } finally {
      setIsBusy(false);
    }
  }

  async function createCandidate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedFailure) return;
    setIsBusy(true);
    setError(null);
    try {
      await transport.createCandidate(actor, {
        failed_question_id: selectedFailure.id,
        category: selectedFailure.intent,
        ...draft,
        procedure_steps: [],
        required_documents: [],
        processing_time: null,
        fee: null,
        caution: null,
      });
      await refreshCandidates();
      setAnnouncement("KB 후보를 작성했습니다.");
      setDraft(EMPTY_DRAFT);
    } catch {
      setError("KB 후보를 작성하지 못했어요. 입력값을 확인해 주세요.");
    } finally {
      setIsBusy(false);
    }
  }

  function updateDraft(field: keyof CandidateDraft, value: string) {
    setDraft((current) => ({ ...current, [field]: value }));
  }

  return (
    <div className={styles.workspace}>
      <section className={styles.intro} aria-labelledby="admin-title">
        <p className={styles.kicker}>local/private 핵심 개선 루프</p>
        <h1 id="admin-title">AI 민원 운영센터</h1>
        <p>근거가 부족했던 질문을 확인하고, 작성자와 다른 검수자를 거쳐 공식 KB로 반영합니다.</p>
        {usesFixture ? <p className={styles.mockBadge}>시연용 샘플 데이터</p> : null}
        <p className={styles.demoBoundary}>시연용 역할 선택 · 인증 아님</p>
        <label htmlFor="demo-role">시연 역할</label>
        <select
          id="demo-role"
          value={role}
          onChange={(event) => setRole(event.target.value as AdminActor["role"])}
        >
          <option value="OPERATOR">작성 운영자 · OPERATOR-LOCAL-001</option>
          <option value="APPROVER">별도 승인자 · PM-LOCAL-001</option>
        </select>
        <p className={styles.actorLine}>현재 시연 actor: {actor.actorId}</p>
      </section>

      <p className={styles.privacyBoundary}>마스킹된 질문만 표시합니다. 질문 원문·브라우저 저장소·쿠키·분석 도구를 사용하지 않습니다.</p>
      <p className={styles.liveRegion} aria-live="polite">{announcement}</p>

      {isLoading ? <p className={styles.statePanel}>운영 데이터를 불러오고 있어요.</p> : null}
      {error ? (
        <div className={styles.errorPanel} role="alert">
          <p>{error}</p>
          <button type="button" onClick={() => void loadDashboard()}>다시 불러오기</button>
        </div>
      ) : null}

      {!isLoading && !error ? (
        <div className={styles.columns}>
          <section className={styles.panel} aria-labelledby="failure-list-title">
            <div className={styles.panelHeading}>
              <div>
                <p className={styles.kicker}>운영 큐</p>
                <h2 id="failure-list-title">실패 질문</h2>
              </div>
              <span>{failures.length}건</span>
            </div>
            {failures.length === 0 ? (
              <p className={styles.emptyState}>확인할 실패 질문이 없습니다.</p>
            ) : (
              <ul className={styles.failureList}>
                {failures.map((failure) => (
                  <li key={failure.id}>
                    <button type="button" onClick={() => void openFailure(failure.id)}>
                      <span>{INTENT_LABELS[failure.intent]}</span>
                      <FailureText failure={failure} />
                      <small>{failure.fallback_reason} · {failure.status}</small>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className={styles.panel} aria-labelledby="failure-detail-title">
            <p className={styles.kicker}>작성 단계</p>
            <h2 id="failure-detail-title">실패 질문 상세</h2>
            {!selectedFailure ? (
              <p className={styles.emptyState}>왼쪽 목록에서 질문을 선택하세요.</p>
            ) : (
              <div className={styles.detailStack}>
                <FailureText failure={selectedFailure} />
                <dl className={styles.auditList}>
                  <div><dt>분류</dt><dd>{INTENT_LABELS[selectedFailure.intent]}</dd></div>
                  <div><dt>저장 사유</dt><dd>{selectedFailure.fallback_reason}</dd></div>
                  <div><dt>텍스트 만료</dt><dd><time dateTime={selectedFailure.text_expires_at}>{selectedFailure.text_expires_at}</time></dd></div>
                </dl>
                {role === "OPERATOR" && selectedFailure.status === "NEW" ? (
                  <button className={styles.primaryButton} type="button" disabled={isBusy} onClick={() => void confirmReason()}>
                    사유 확정
                  </button>
                ) : null}
                {selectedFailure.status === "REASON_CONFIRMED" ? <p className={styles.confirmed}>사유 확인 완료</p> : null}
                {selectedFailure.status === "REASON_CONFIRMED" && !selectedFailure.candidate_eligible ? (
                  <p className={styles.purgedText}>후보 전환 대상이 아닙니다.</p>
                ) : null}

                {role === "OPERATOR"
                  && selectedFailure.status === "REASON_CONFIRMED"
                  && selectedFailure.candidate_eligible
                  && !selectedHasCandidate ? (
                  <form className={styles.candidateForm} onSubmit={createCandidate}>
                    <h3>KB 후보 작성</h3>
                    <label htmlFor="candidate-title">후보 제목</label>
                    <input id="candidate-title" required value={draft.title} onChange={(event) => updateDraft("title", event.target.value)} />
                    <label htmlFor="candidate-question">대표 질문</label>
                    <input id="candidate-question" required value={draft.representative_question} onChange={(event) => updateDraft("representative_question", event.target.value)} />
                    <label htmlFor="candidate-summary">답변 요약</label>
                    <textarea id="candidate-summary" rows={4} required value={draft.answer_summary} onChange={(event) => updateDraft("answer_summary", event.target.value)} />
                    <label htmlFor="candidate-department">담당 부서</label>
                    <input id="candidate-department" required value={draft.department} onChange={(event) => updateDraft("department", event.target.value)} />
                    <label htmlFor="candidate-source-title">공식 출처명</label>
                    <input id="candidate-source-title" required value={draft.source_title} onChange={(event) => updateDraft("source_title", event.target.value)} />
                    <label htmlFor="candidate-source-url">공식 출처 URL</label>
                    <input id="candidate-source-url" type="url" required value={draft.source_url} onChange={(event) => updateDraft("source_url", event.target.value)} />
                    <label htmlFor="candidate-verified-date">공식 확인일</label>
                    <input id="candidate-verified-date" type="date" required value={draft.last_verified_at} onChange={(event) => updateDraft("last_verified_at", event.target.value)} />
                    <button className={styles.primaryButton} type="submit" disabled={isBusy}>KB 후보 작성</button>
                  </form>
                ) : null}
              </div>
            )}
          </section>
        </div>
      ) : null}

      {!isLoading && !error ? (
        <section className={styles.panel} aria-labelledby="candidate-list-title">
          <div className={styles.panelHeading}>
            <div>
              <p className={styles.kicker}>승인 흐름</p>
              <h2 id="candidate-list-title">KB 후보와 ACTIVE 상태</h2>
            </div>
            <span>{candidates.length}건</span>
          </div>
          {candidates.length === 0 ? (
            <p className={styles.emptyState}>작성된 KB 후보가 없습니다.</p>
          ) : (
            <div className={styles.candidateGrid}>
              {candidates.map((item) => (
                <CandidateCard
                  key={item.id}
                  actor={actor}
                  candidate={item}
                  busy={isBusy}
                  onRefresh={refreshCandidates}
                  transport={transport}
                />
              ))}
            </div>
          )}
        </section>
      ) : null}
    </div>
  );
}
