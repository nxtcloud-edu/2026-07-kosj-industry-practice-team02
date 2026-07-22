"use client";

import { FormEvent, useCallback, useRef, useState } from "react";

import {
  type ChatRequest,
  type ChatResponse,
  type ChatTransport,
  ChatTransportError,
  type Office,
  createChatTransport,
} from "../../lib/chat-api";

type Exchange = Readonly<{
  id: string;
  office: Office | null;
  officeLookupAttempted: boolean;
  question: string;
  response: ChatResponse;
}>;

type FailedDraft = Readonly<{
  request: ChatRequest;
  retryable: boolean;
}>;

const REGION_OPTIONS = ["아름동", "도담동", "조치원읍"] as const;

function OfficeCard({ office, headingId }: { office: Office; headingId: string }) {
  return (
    <section className="office-card" aria-labelledby={headingId}>
      <p className="card-label">안내 기관</p>
      <h3 id={headingId}>{office.office_name}</h3>
      <dl className="fact-list">
        <div>
          <dt>주소</dt>
          <dd>{office.address}</dd>
        </div>
        <div>
          <dt>전화</dt>
          <dd>{office.phone}</dd>
        </div>
        {office.opening_hours ? (
          <div>
            <dt>운영 시간</dt>
            <dd>{office.opening_hours}</dd>
          </div>
        ) : null}
      </dl>
      <div className="card-links">
        {office.source_url ? <a href={office.source_url}>{office.source_title}</a> : <span>{office.source_title}</span>}
        {office.map_url ? <a href={office.map_url}>공식 지도 링크</a> : null}
      </div>
      <p className="verified-date">확인일 <time dateTime={office.last_verified_at}>{office.last_verified_at}</time></p>
    </section>
  );
}

function SuccessAnswer({ exchange }: { exchange: Exchange }) {
  const { response } = exchange;
  if (response.answer_status !== "SUCCESS") return null;

  return (
    <article className="answer-card answer-success" aria-labelledby={`answer-${exchange.id}`}>
      <p className="answer-state">공식 근거를 확인했어요</p>
      <h2 id={`answer-${exchange.id}`}>{response.summary ?? "확인된 민원 안내"}</h2>
      {response.procedure_steps?.length ? (
        <section aria-label="진행 순서">
          <h3>이렇게 하세요</h3>
          <ol className="answer-list">
            {response.procedure_steps.map((step) => <li key={step}>{step}</li>)}
          </ol>
        </section>
      ) : null}
      {response.required_documents?.length ? (
        <section aria-label="필요 서류">
          <h3>필요 서류</h3>
          <ul className="answer-list">
            {response.required_documents.map((document) => <li key={document}>{document}</li>)}
          </ul>
        </section>
      ) : null}
      <dl className="fact-list answer-facts">
        {response.processing_time ? <div><dt>처리 기간</dt><dd>{response.processing_time}</dd></div> : null}
        {response.fee ? <div><dt>수수료</dt><dd>{response.fee}</dd></div> : null}
        {response.department ? <div><dt>담당</dt><dd>{response.department}</dd></div> : null}
      </dl>
      <section className="source-section" aria-label="공식 출처">
        <h3>공식 출처</h3>
        <ul className="source-list">
          {response.sources.map((source) => (
            <li key={source.source_id}>
              <a href={source.url}>{source.title}</a>
              <span>확인일 <time dateTime={source.last_verified_at}>{source.last_verified_at}</time></span>
            </li>
          ))}
        </ul>
      </section>
      {exchange.office ? (
        <OfficeCard office={exchange.office} headingId={`office-${exchange.id}-${exchange.office.id}`} />
      ) : null}
      {exchange.officeLookupAttempted && !exchange.office ? (
        <p className="empty-office">선택한 지역의 연결 가능한 공식 기관 정보가 없어요.</p>
      ) : null}
    </article>
  );
}

function FollowupAnswer({
  exchange,
  disabled,
  onSelect,
}: {
  exchange: Exchange;
  disabled: boolean;
  onSelect: (option: string) => void;
}) {
  const { response } = exchange;
  if (response.answer_status !== "FOLLOWUP") return null;

  return (
    <article className="answer-card answer-followup" aria-labelledby={`answer-${exchange.id}`}>
      <p className="answer-state">조금 더 알려 주세요</p>
      <h2 id={`answer-${exchange.id}`}>어떤 민원을 도와드릴까요?</h2>
      <div className="followup-options" aria-label="후속 질문 선택지">
        {response.followup_options.map((option) => (
          <button key={option} type="button" disabled={disabled} onClick={() => onSelect(option)}>
            {option}
          </button>
        ))}
      </div>
    </article>
  );
}

function FallbackAnswer({ exchange }: { exchange: Exchange }) {
  const { response } = exchange;
  if (response.answer_status !== "FALLBACK") return null;

  return (
    <article className="answer-card answer-fallback" aria-labelledby={`answer-${exchange.id}`}>
      <p className="fallback-code">{response.fallback.reason}</p>
      <h2 id={`answer-${exchange.id}`}>{response.fallback.title}</h2>
      <p>{response.fallback.message}</p>
      {response.fallback.next_actions?.length ? (
        <ul className="answer-list">
          {response.fallback.next_actions.map((action) => <li key={action}>{action}</li>)}
        </ul>
      ) : null}
      {response.fallback.office ? (
        <OfficeCard
          office={response.fallback.office}
          headingId={`office-${exchange.id}-${response.fallback.office.id}`}
        />
      ) : null}
    </article>
  );
}

export function ChatExperience({ transport = createChatTransport() }: { transport?: ChatTransport }) {
  const [question, setQuestion] = useState("");
  const [selectedRegion, setSelectedRegion] = useState<ChatRequest["selected_region"]>(null);
  const [exchanges, setExchanges] = useState<Exchange[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [failedDraft, setFailedDraft] = useState<FailedDraft | null>(null);
  const contextTokenRef = useRef<string | null>(null);
  const inFlightRef = useRef(false);

  const sendRequest = useCallback(async (request: ChatRequest) => {
    if (inFlightRef.current) return;
    inFlightRef.current = true;
    setIsLoading(true);
    setFailedDraft(null);

    try {
      const response = await transport.send(request);
      const shouldShowOfficeState = response.answer_status === "SUCCESS" && Boolean(request.selected_region);
      const office = response.answer_status === "SUCCESS" ? response.office : null;

      contextTokenRef.current = response.answer_status === "FALLBACK" ? null : response.context_token;
      setExchanges((current) => [
        ...current,
        {
          id: response.request_id,
          office,
          officeLookupAttempted: shouldShowOfficeState,
          question: request.question,
          response,
        },
      ]);
      setQuestion((current) => (current.trim() === request.question ? "" : current));
    } catch (error) {
      setFailedDraft({
        request,
        retryable: !(error instanceof ChatTransportError) || error.retryable,
      });
    } finally {
      inFlightRef.current = false;
      setIsLoading(false);
    }
  }, [transport]);

  const submitQuestion = useCallback((nextQuestion: string, contextToken = contextTokenRef.current) => {
    const trimmed = nextQuestion.trim();
    if (!trimmed || inFlightRef.current) return;

    void sendRequest({
      question: trimmed,
      selected_region: selectedRegion ?? null,
      simple_language: true,
      context_token: contextToken,
    });
  }, [selectedRegion, sendRequest]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    submitQuestion(question);
  }

  return (
    <div className="chat-workspace">
      <section className="chat-intro" aria-labelledby="chat-page-title">
        <p className="eyebrow">승인된 공식 정보로 안내해요</p>
        <h1 id="chat-page-title">민원을 물어보세요</h1>
        <p>알 수 있는 내용은 출처와 다음 행동까지, 모르는 내용은 지어내지 않고 안전하게 안내합니다.</p>
      </section>

      <section className="transcript-panel" aria-label="대화 내용" aria-live="polite" aria-relevant="additions text">
        {exchanges.length === 0 ? (
          <div className="empty-chat">
            <p>아직 대화가 없어요.</p>
            <p>전입신고, 증명서, 대형폐기물, 지방세 일반 안내를 물어보세요.</p>
          </div>
        ) : (
          <ol className="transcript-list">
            {exchanges.map((exchange, index) => (
              <li key={exchange.id} className="exchange">
                <div className="citizen-message">
                  <p className="message-speaker">나</p>
                  <p>{exchange.question}</p>
                </div>
                <SuccessAnswer exchange={exchange} />
                <FollowupAnswer
                  exchange={exchange}
                  disabled={isLoading || index !== exchanges.length - 1}
                  onSelect={(option) => submitQuestion(option, exchange.response.context_token)}
                />
                <FallbackAnswer exchange={exchange} />
              </li>
            ))}
          </ol>
        )}

        {isLoading ? <p className="loading-state">승인된 공식 근거를 확인하고 있어요.</p> : null}
        {failedDraft ? (
          <div className="error-state" role="alert">
            <p>
              {failedDraft.retryable
                ? "지금은 안전한 답변을 만들 수 없어요. 잠시 후 다시 시도해 주세요."
                : "입력 내용을 확인한 뒤 새 질문을 보내 주세요."}
            </p>
            {failedDraft.retryable ? (
              <button type="button" onClick={() => void sendRequest(failedDraft.request)}>다시 시도</button>
            ) : null}
          </div>
        ) : null}
      </section>

      <form className="chat-composer" onSubmit={handleSubmit} aria-label="민원 질문 작성">
        <div className="field-group region-field">
          <label htmlFor="chat-region">지역 선택</label>
          <select
            id="chat-region"
            value={selectedRegion ?? ""}
            onChange={(event) => setSelectedRegion((event.target.value || null) as ChatRequest["selected_region"])}
          >
            <option value="">선택 안 함</option>
            {REGION_OPTIONS.map((region) => <option key={region} value={region}>{region}</option>)}
          </select>
        </div>
        <div className="field-group question-field">
          <label htmlFor="chat-question">민원 질문</label>
          <textarea
            id="chat-question"
            value={question}
            maxLength={1000}
            rows={3}
            placeholder="예: 이사했는데 전입신고 어떻게 해요?"
            onChange={(event) => setQuestion(event.target.value)}
          />
        </div>
        <button className="send-button" type="submit" disabled={isLoading || !question.trim()}>
          {isLoading ? "답변 확인 중" : "질문 보내기"}
        </button>
        <p className="privacy-note">주민등록번호, 전화번호, 상세 주소 같은 개인정보는 입력하지 마세요.</p>
      </form>
    </div>
  );
}
