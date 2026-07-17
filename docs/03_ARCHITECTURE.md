# 시스템 아키텍처 기준

## 1. 권장 물리 구조

```text
Browser
  ├─ /, /chat, /admin — Next.js
  ├─ current-tab transcript + opaque 15-minute context token
  └─ HTTPS JSON
        ↓
FastAPI /api/v1
  ├─ input validation
  ├─ PII redaction
  ├─ intent/followup/fallback policy
  ├─ retrieval
  ├─ provider adapter
  ├─ response validation
  ├─ source metadata attachment
  ├─ event logging
  └─ admin workflow
        ↓
Supabase PostgreSQL
  ├─ ACTIVE KB and source metadata
  ├─ official offices/mappings
  ├─ interaction events without question text
  ├─ masked failed questions
  ├─ candidates and approval states
  └─ minimal audit events
```

## 2. 모노레포 권장 구조

```text
apps/web       Next.js
apps/api       FastAPI
packages/shared-contracts  generated/shared types
contracts      OpenAPI and JSON Schema source
supabase/migrations  timestamp-ordered executable DB authority
database       logical projection, reverse-order local compensation, absence proof
data           official/evaluation/mock separated
docs           source-of-truth, ADR, notes, reports
scripts        reproducible project tooling
```

기존 스타터는 `legacy/`로 유지한다. 신규 앱 스캐폴딩 전 Codex가 패키지 관리자, 런타임 버전, 마이그레이션 도구, CI 환경을 인터뷰한다.

## 3. Chat 처리 경계

1. 요청 검증과 길이 제한
2. optional context token의 서명·TTL·closed claim 검증; 실패하면 문맥 없음으로 계속
3. 서버 내부 PII 탐지·마스킹
4. 지원 범위/모호성/개인 조회/법적 판단 사전 규칙
5. ACTIVE KB 검색
6. 근거 충족 판단
7. 근거가 있으면 provider adapter 또는 템플릿으로 구조화 답변
8. JSON Schema 검증
9. 서버가 source_id로 출처 메타데이터 결합
10. 텍스트 없는 interaction event 저장
11. 필요한 경우 masked failed question 저장
12. SUCCESS/FOLLOWUP에만 새 구조화 context token 발급 가능; FALLBACK은 null

## 4. LLM adapter

공급자 모델은 정확히 `deepseek-v4-flash`로 고정한다. thinking off, max output 1024, concurrency 1, 논리 요청당 재시도 최대 1회, 명시적 process run당 재시도를 포함한 실제 outbound attempt 총 30회를 강제한다. 도메인 서비스가 공급자 SDK에 직접 의존하지 않도록 다음 인터페이스를 둔다.

```python
class LLMProvider(Protocol):
    async def classify_or_answer(self, request: GroundedRequest) -> GroundedResult: ...
```

요구사항:

- 입력은 마스킹된 질문과 허용된 KB 청크만
- DeepSeek 입력은 서버 allowlist로 확인한 local/private 합성 fixture만; 실제 시민·public 요청은 disabled/template
- 출력은 스키마 검증 가능한 구조화 객체
- timeout/retry/circuit-breaker 경계
- 공급자 장애 시 KB 템플릿 또는 안전 폴백
- 공급자 이름/모델/latency는 관측 가능하되 질문 텍스트 로그 금지
- `DEEPSEEK_ENABLED=false` 기본, 서버 allowlist synthetic evaluation mode에서만 활성; hidden retry·preflight provider call·cap reset endpoint 금지

## 4.1 대화 문맥 경계

- transcript와 token은 현재 브라우저 탭 메모리에만 두고 새로고침 시 폐기한다.
- 서버 session/chat table을 만들지 않고 token·질문·답변을 DB/로그/analytics에 저장하지 않는다.
- HMAC-SHA-256 token은 암호화가 아니므로 version, enum, 서버 정의 option ID, `iat`/`exp` 외 claim을 금지한다.
- token은 인증·권한·공식 사실이 아니며 현재 요청의 안전 분류, ACTIVE KB 검색, source 결합을 매번 재실행한다.

## 5. 검색 전략

KB 20건에서는 키워드·메타데이터·question_examples를 기본으로 한다. 임베딩은 보조 점수이며, 공급자/차원에 DB를 영구 결합하지 않도록 adapter를 둔다.

초기 권장 흐름:

```text
intent filter
→ exact/keyword aliases
→ metadata/service match
→ optional embedding rerank (MVP flag off)
→ evidence threshold
```

근거 충족 기준은 코드와 테스트에서 명시해야 하며 단순 LLM 자신감 점수로 판단하지 않는다.

## 6. 관리자 승인 흐름

```text
NEW
→ REASON_CONFIRMED
→ DRAFTED
→ PENDING_APPROVAL
→ APPROVED | REJECTED
→ APPROVED transaction creates/activates KB
```

- created_by != reviewed_by
- 운영자 역할은 approve 불가
- 승인 트랜잭션과 ACTIVE 생성은 원자적
- 후보 답변/출처는 사람 입력
- audit는 action/status/field names만

## 7. 장애 전략

- LLM 실패 + KB 충분: 서버 템플릿 답변
- LLM 실패 + KB 부족: 정책 근거 부족 폴백 200; 필수 분류·검색·응답 조립과 안전 대체까지 불능일 때만 503
- DB 실패: 질문 원문을 파일/큐에 임시 저장하지 않음
- source metadata 불일치: 직접 답변 차단
- 배포 장애: 로컬 seed/고정 데모 경로; 공개 URL·녹화본은 별도 발표/배포 승인 항목

## 8. DB-001 local/private 경계

- `app_private`에는 7 enum과 8 업무 table을 두고 Data API 노출 schema에서 제외한다.
- 브라우저·`PUBLIC`·`anon`·`authenticated`는 업무 table에 직접 접근하지 않는다.
- `sejong_backend`는 NOLOGIN capability role이며 base-table DML 대신 검토된 `app_api`
  함수만 실행한다. FastAPI repository도 고정 SQL 9개만 사용한다.
- RLS는 8 table 모두 ENABLE+FORCE이고 owner-only policy를 사용한다.
- 시민 read는 `ACTIVE + OFFICIAL` KB와 `OFFICIAL` 기관만 반환한다.
- executable authority는 forward migration 6개이며 disposable-local compensation은
  `00600 → 00500 → 00400 → 00300 → 00200 → 00100`이다.
- `database/schema-v1.draft.sql`은 `0.3.0-local` 후보의 읽기 전용 논리 투영이며 권한·함수·trigger
  실행 근거가 아니다.
- manifest는 Q-SEC-005/A-023 IPv6 local port blocker로 `0.2.0-draft`를 유지한다. exact loopback과
  full gate 전에는 후보 shape를 완료 기준선으로 부르지 않는다.
- A-021/Q-SEC-003 기본값 B에 따라 A-023 해소 뒤 승격 가능한 기준선도 local/private에
  한정한다. 기존 privileged function 21개의 search-path hardening 전에는 remote/public 배포,
  public admin/API, public backend DB credential 사용을 차단하고 `00700`을 임의로 만들지 않는다.
