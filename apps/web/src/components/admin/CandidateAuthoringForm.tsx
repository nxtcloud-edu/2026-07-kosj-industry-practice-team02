"use client";

import { useState, type FormEvent, type InvalidEvent } from "react";
import type { components } from "../../../../../packages/shared-contracts/src/generated/api";
import { RESERVED_CANDIDATE, isReservedCandidateTarget } from "@/lib/reserved-candidate";

type FailedQuestion = components["schemas"]["FailedQuestion"];
type KBCandidateCreate = components["schemas"]["KBCandidateCreate"];

type Props = Readonly<{
  failure: FailedQuestion;
  busy: boolean;
  onCancel: () => void;
  onSubmit: (draft: KBCandidateCreate) => void;
}>;

function lines(value: string): string[] {
  return value
    .split(/\r?\n/u)
    .map((item) => item.trim())
    .filter(Boolean);
}

const inputClass =
  "min-h-11 w-full rounded-btn-s border border-border bg-white px-3 text-admin-body text-text focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20";

const APPROVED_SOURCE_HOSTS = [
  "www.sejong.go.kr",
  "plus.gov.kr",
  "www.gov.kr",
  "www.law.go.kr",
  "www.wetax.go.kr",
  "www.sjwaste.kr",
] as const;

function isApprovedSourceUrl(value: string): boolean {
  try {
    const url = new URL(value);
    return (
      url.protocol === "https:" &&
      APPROVED_SOURCE_HOSTS.includes(
        url.hostname.toLowerCase() as (typeof APPROVED_SOURCE_HOSTS)[number],
      ) &&
      (url.port === "" || url.port === "443") &&
      url.username === "" &&
      url.password === "" &&
      url.hash === ""
    );
  } catch {
    return false;
  }
}

export default function CandidateAuthoringForm({
  failure,
  busy,
  onCancel,
  onSubmit,
}: Props) {
  // 예약된 활성화 대상이면 서버가 보유한 공식 값을 채워 둔다. 그 밖에는 빈 칸으로 시작한다.
  const reserved = isReservedCandidateTarget(failure);
  const seed = reserved ? RESERVED_CANDIDATE : null;

  const [title, setTitle] = useState(seed?.title ?? "");
  const [representativeQuestion, setRepresentativeQuestion] = useState(
    seed?.representativeQuestion ?? failure.masked_question ?? "",
  );
  const [answerSummary, setAnswerSummary] = useState(seed?.answerSummary ?? "");
  const [procedureSteps, setProcedureSteps] = useState(
    seed ? seed.procedureSteps.join("\n") : "",
  );
  const [requiredDocuments, setRequiredDocuments] = useState(
    seed ? seed.requiredDocuments.join("\n") : "",
  );
  const [processingTime, setProcessingTime] = useState(seed?.processingTime ?? "");
  const [fee, setFee] = useState(seed?.fee ?? "");
  const [department, setDepartment] = useState(seed?.department ?? "");
  const [sourceTitle, setSourceTitle] = useState(seed?.sourceTitle ?? "");
  const [sourceUrl, setSourceUrl] = useState(seed?.sourceUrl ?? "");
  const [lastVerifiedAt, setLastVerifiedAt] = useState(seed?.lastVerifiedAt ?? "");
  const [caution, setCaution] = useState(seed?.caution ?? "");
  const [error, setError] = useState<string | null>(null);

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!isApprovedSourceUrl(sourceUrl)) {
      setError("허용된 공식 출처 주소를 사용해 주세요.");
      return;
    }
    setError(null);
    onSubmit({
      failed_question_id: failure.id,
      title,
      representative_question: representativeQuestion,
      category: failure.intent,
      answer_summary: answerSummary,
      procedure_steps: lines(procedureSteps),
      required_documents: lines(requiredDocuments),
      processing_time: processingTime || null,
      fee: fee || null,
      department,
      source_title: sourceTitle,
      source_url: sourceUrl,
      last_verified_at: lastVerifiedAt,
      caution: caution || null,
    });
  };

  return (
    <section
      aria-labelledby="candidate-authoring-title"
      className="mt-5 rounded-card border border-primary-border bg-white p-5 shadow-card"
    >
      <div className="mb-4">
        <h2 id="candidate-authoring-title" className="text-[20px] font-extrabold text-text">
          공식 KB 후보 작성
        </h2>
        <p className="mt-1 text-caption text-text-sub">
          운영자가 공식 출처를 확인해 직접 작성합니다. 저장 후 별도 승인자가 검수합니다.
        </p>
        {reserved ? (
          <p className="mt-2 rounded-btn-s bg-primary/5 px-3 py-2 text-caption text-text-sub">
            승인된 공식 출처에 이 민원의 등록 예정 항목이 있어 값을 채워 두었습니다.
            내용을 확인하고 필요하면 수정한 뒤 제출하세요. 반영 여부는 별도 승인자가 판정합니다.
          </p>
        ) : null}
      </div>
      <form
        onSubmit={submit}
        onInvalid={(event: InvalidEvent<HTMLFormElement>) => {
          event.preventDefault();
          setError("필수 입력 항목을 모두 작성해 주세요.");
          if (event.target instanceof HTMLElement) event.target.focus();
        }}
        className="grid gap-4 md:grid-cols-2"
      >
        <label className="grid gap-1.5 text-note font-bold text-text">
          제목
          <input required maxLength={200} value={title} onChange={(e) => setTitle(e.target.value)} className={inputClass} />
        </label>
        <label className="grid gap-1.5 text-note font-bold text-text">
          분야
          <input readOnly value={failure.intent} className={`${inputClass} bg-bg-sub`} />
        </label>
        <label className="grid gap-1.5 text-note font-bold text-text md:col-span-2">
          대표 질문
          <input required maxLength={1000} value={representativeQuestion} onChange={(e) => setRepresentativeQuestion(e.target.value)} className={inputClass} />
        </label>
        <label className="grid gap-1.5 text-note font-bold text-text md:col-span-2">
          답변 요약
          <textarea required rows={3} value={answerSummary} onChange={(e) => setAnswerSummary(e.target.value)} className={`${inputClass} py-2.5`} />
        </label>
        <label className="grid gap-1.5 text-note font-bold text-text">
          처리 절차 (한 줄에 한 단계)
          <textarea rows={4} value={procedureSteps} onChange={(e) => setProcedureSteps(e.target.value)} className={`${inputClass} py-2.5`} />
        </label>
        <label className="grid gap-1.5 text-note font-bold text-text">
          필요 서류 (한 줄에 하나)
          <textarea rows={4} value={requiredDocuments} onChange={(e) => setRequiredDocuments(e.target.value)} className={`${inputClass} py-2.5`} />
        </label>
        <label className="grid gap-1.5 text-note font-bold text-text">
          처리 시간 (선택)
          <input value={processingTime} onChange={(e) => setProcessingTime(e.target.value)} className={inputClass} />
        </label>
        <label className="grid gap-1.5 text-note font-bold text-text">
          수수료 (선택)
          <input value={fee} onChange={(e) => setFee(e.target.value)} className={inputClass} />
        </label>
        <label className="grid gap-1.5 text-note font-bold text-text">
          담당 부서
          <input required value={department} onChange={(e) => setDepartment(e.target.value)} className={inputClass} />
        </label>
        <label className="grid gap-1.5 text-note font-bold text-text">
          공식 출처명
          <input required value={sourceTitle} onChange={(e) => setSourceTitle(e.target.value)} className={inputClass} />
        </label>
        <label className="grid gap-1.5 text-note font-bold text-text md:col-span-2">
          공식 출처 URL
          <input required aria-label="공식 출처 URL" type="url" placeholder="https://www.sejong.go.kr/…" value={sourceUrl} onChange={(e) => setSourceUrl(e.target.value)} className={inputClass} />
          <span className="text-caption font-normal leading-5 text-text-sub">
            허용 출처: {APPROVED_SOURCE_HOSTS.join(", ")}
          </span>
        </label>
        <label className="grid gap-1.5 text-note font-bold text-text">
          출처 확인일
          <input required type="date" value={lastVerifiedAt} onChange={(e) => setLastVerifiedAt(e.target.value)} className={inputClass} />
        </label>
        <label className="grid gap-1.5 text-note font-bold text-text">
          주의사항 (선택)
          <input value={caution} onChange={(e) => setCaution(e.target.value)} className={inputClass} />
        </label>
        {error && <p role="alert" className="text-note font-bold text-danger md:col-span-2">{error}</p>}
        <div className="flex flex-wrap justify-end gap-2 md:col-span-2">
          <button type="button" onClick={onCancel} disabled={busy} className="min-h-11 rounded-btn-s border border-border px-4 text-admin-body font-bold text-text-sub">
            취소
          </button>
          <button type="submit" disabled={busy} className="min-h-11 rounded-btn-s bg-primary px-5 text-admin-body font-extrabold text-white disabled:opacity-50">
            {busy ? "저장 중…" : "후보 저장 후 승인 요청"}
          </button>
        </div>
      </form>
    </section>
  );
}
