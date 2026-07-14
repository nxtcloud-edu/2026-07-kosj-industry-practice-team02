# 테스트 전략

## 테스트 피라미드

### Unit

- 보수적 PII redaction patterns와 불확실 입력의 외부 호출 차단
- intent/followup/fallback policy
- candidate eligibility
- ACTIVE-only retrieval
- source metadata attachment
- approval guard
- retention expiration
- context token sign/verify, exact 900-second TTL, closed claims, current request precedence
- DeepSeek outbound cap/retry/concurrency state machine

### Contract

- OpenAPI request/response validation
- JSON Schema for chat/KB/event
- FE generated types vs API
- enum and error code compatibility
- 200 ChatResponse의 SYSTEM_ERROR 거부와 503 SERVICE_UNAVAILABLE exact envelope
- `session_id` 거부, context token required/nullability, FALLBACK-null invariant의 OpenAPI/JSON Schema 동일 fixture

### Integration

- Postgres transaction for approval→ACTIVE KB
- event without question text
- failed question storage policy
- DeepSeek server fixture allowlist와 자유 입력 차단
- provider timeout/empty/schema invalid의 200 안전 대체 또는 503 분기
- DeepSeek exact model/thinking off/max 1024, hidden retry off, concurrency 1, run cap 28/29/30 경계
- tampered/expired/unknown context token의 silent new-conversation 처리와 token/secret DB·로그 0건
- Supabase empty DB reset/replay와 명시적 보상 rollback/replay
- office mapping

### E2E

- 정상 답변과 출처
- 모호 질문 FOLLOWUP
- PERSONAL_LOOKUP
- 지역·기관 카드
- 관리자 후보 작성/자기승인 차단/승인
- REG-01 개선 전후
- `/`의 4개 지원 분야·서비스 한계·`/chat` 진입
- current-tab transcript 연속성, 새로고침 후 소멸, 503 재시도·중복 전송 방지, empty office, rejected 후보 재작성

### Non-functional

- 390px/430px, 200% zoom
- keyboard focus and modal return
- contrast 4.5:1
- average/p95/error rate
- 100 virtual users, 1 minute, cached/fixed response path

## 표본과 회귀

- `data/evaluation/`의 20개 표본을 자동 또는 반자동 실행
- 결과는 전체 민원 정확도가 아니라 MVP 표본 결과
- `REG-01`은 별도 상태 변화 테스트

## 테스트 증거

각 구현 노트에 다음을 기록한다.

- 정확한 명령
- 통과/실패 개수
- 실행시간
- 실패 로그의 안전한 요약
- 화면 검증 이미지/경로
- 미실행 항목과 이유

## 금지

- 테스트를 통과시키려고 공식 데이터 값을 임의로 변경
- mock과 공식 결과를 같은 KPI로 합산
- LLM 랜덤 결과를 고정 정답처럼 과장
- 원문 PII를 fixture로 사용
- 클라이언트 `is_test` 값만 믿고 DeepSeek를 호출
- context token을 인증·공식 사실로 신뢰하거나 브라우저 storage/로그에 보관
