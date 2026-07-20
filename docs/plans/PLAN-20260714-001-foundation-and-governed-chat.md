# PLAN-20260714-001 — local-first 기반과 승인형 민원 안내 수직 흐름

## 상태

Approved — 2026-07-15 사용자가 `진행`으로 최종 계획·초기 프로덕션 의존성·독립 local Git·개발 도구 설치·합성 fixture 한정 DeepSeek smoke를 승인. 공개/실제 시민 경계는 계속 별도 승인

> 구현 승인 후에는 `superpowers:subagent-driven-development` 또는 별도 세션의 `superpowers:executing-plans` 절차로 한 수직 흐름씩 실행하고, 각 흐름은 TDD와 완료 전 검증을 적용한다.

## 목표와 비목표

- 목표:
  - 원본 원격이 없는 현재 폴더를 재현 가능한 독립 모노레포로 스캐폴딩한다.
  - 승인된 ACTIVE KB만 사용하는 `/chat` 정상 답변·FOLLOWUP·4개 폴백을 구현한다.
  - 외부 LLM 전 PII 마스킹, 원문 DB/로그 미저장, 서버 결합 출처를 강제한다.
  - 실패 질문 텍스트의 30일 파기와 운영자-승인자 분리형 `/admin` 개선 루프를 구현한다.
  - local/private 환경에서 회귀·접근성·성능·백업 복구를 재현한다.
- 비목표:
  - 실제 GPS·지도, 신청/상태/개인별 세금 조회, 정부24·내부망 연계
  - 다국어·음성·자동 클러스터링·주간 AI 리포트
  - public admin, 기관 SSO/RBAC/전자결재
  - 별도 승인 없는 Vercel/Render/Supabase 공개 배포와 유료 외부 서비스

## 사용자 가치와 인수 기준

- 사용자 가치:
  - 시민은 공식 근거가 있을 때 출처·준비물·다음 행동까지 받고, 근거가 없을 때는 지어낸 답 대신 안전한 경로를 받는다.
  - 운영자는 지원 범위 안의 근거 부족 질문만 사람 검수·별도 승인으로 ACTIVE KB에 반영하고 개선 전후를 증명한다.
- Acceptance Criteria:
  - `/`, `/chat`, `/admin`이 local/private의 모바일·데스크톱에서 동작한다.
  - SUCCESS는 ACTIVE KB source 1개 이상과 서버 결합 출처 카드가 없으면 반환되지 않는다.
  - FOLLOWUP 2건, 네 폴백 8건, 정상 10건의 표본 계약과 KPI를 충족한다.
  - 외부 provider payload·DB·app/access/error log에서 raw question과 금지 PII 0건이다.
  - OUT_OF_SCOPE와 FOLLOWUP은 `failed_questions`에 행이 없고, 성공 질문은 텍스트가 저장되지 않는다.
  - `masked_question`은 생성 30일 후 NULL이며 `text_purged_at`이 기록되고 후보 FK·비텍스트 메타데이터는 유지된다.
  - 작성자 본인 승인과 DRAFT/PENDING 시민 검색 노출이 각각 0건이다.
  - REG-01이 승인 전 INSUFFICIENT_GROUNDING → 별도 승인 → 승인 후 출처 포함 SUCCESS를 완주한다.
  - 390px·430px, 키보드, 포커스, 본문 4.5:1, 200% zoom 기준을 통과한다.
  - 평균·p95·오류율과 제한적 100명/1분 스모크 결과 및 한계를 기록한다.
  - `/`는 4개 지원 분야·서비스 한계·`/chat` 진입을 제공하고 E2E로 검증한다.
  - 브라우저 현재 탭에서는 대화가 이어지지만 새로고침 후 사라지고, 서버/브라우저 영속 저장소/로그에는 transcript·context token이 0건이다.
  - `deepseek-v4-flash` 합성 경로는 thinking off, max 1024, concurrency 1, retry 최대 1, run당 실제 outbound attempt 30 이하를 경계 테스트로 증명한다.
  - 품질 화면은 EVENT/EVALUATION/MOCK을 합산하지 않고 배지를 숨기지 않으며, 감사 이력에는 질문·답변 snapshot이 없다.

## 권위 근거

- RFP ID: SFR-001~006, DAR-001~003, PER-001~002, SER-001~003, QUR-001~002, COR-001~002
- source-of-truth: `docs/source-of-truth/TEAM_DECISIONS.md`, `PROJECT_PLAN.md`, `PRIVACY_POLICY.md`, `APPROVAL_POLICY.md`, `KB_GUIDE.md`, `REGRESSION_TEST.md`
- ADR: ADR-0002~0010
- 관련 발견/결정: `docs/discovery/INITIAL_DISCOVERY_REPORT.md`, `docs/discovery/INTERVIEW_ANSWERS.md`, D-009~D-024
- 관련 구현 노트: `IMP-20260714-001`~`IMP-20260714-004`

## 현재 상태와 조사 결과

- 활성 코드: `apps/web`, `apps/api`, `packages/shared-contracts`는 placeholder이며 실행 코드·manifest·test가 없다.
- 활성 데이터: source registry 20행은 staging이고 작성/승인이 완료되지 않았다. ACTIVE KB·기관·mock seed는 0건이다.
- 활성 계약: OpenAPI 2.0.0-draft, DB 논리 초안 0.2.0-draft. 200 정책 응답/503 시스템 불능, 15분 client-carried context, Q-PRIV-001 텍스트 파기를 반영했지만 앱·실행 migration은 아니다.
- legacy 참고: 정적 UI 아이디어와 일부 mock만 참고 가능하며 10개 분야/P2/가짜 공식 데이터는 복사하지 않는다.
- 확인한 명령: `rg --files`, PowerShell 인벤토리/JSON/CSV 검사, Git 경계 검사, package validator, scope drift checker, 제한적 secret/PII 검색.
- 발견한 충돌:
  - workspace는 아직 유효한 Git 저장소가 아니다.
  - Node 24.12.0·Docker CLI 29.2.1은 있으나 pnpm·uv·Supabase CLI와 앱 의존성이 없고 Docker engine은 꺼져 있다. Python 기본은 3.14.0으로 승인 기준 3.12와 다르다.
  - DeepSeek 기존 잔액·local/private 합성 경계와 정확한 `deepseek-v4-flash`/thinking off/max 1024/concurrency 1/retry 1/run cap 30이 확정됐다. 아직 key 입력·패키지 설치·실제 호출은 0건이다.
  - 이 PC는 RAM 15.6GiB, Intel Arc 표시 메모리 2GiB로 확인됐다. 20B급 local model은 안정적 데모 기본값으로 부적합하고 4B급도 실제 한국어 품질·latency benchmark가 필요하다.
  - Supabase CLI 버전 SQL migration을 선택했지만 도구 설치·Docker local stack·migration은 계획 승인 전 실행하지 않았다.
  - 원격 저장소·CI 없이 local 수동 검증하므로 단일 PC 백업과 명령 증거만 있다.
  - 앱이 없으므로 build/test/lint/typecheck/E2E를 실행할 수 없다.
  - 인간 결정형 A/Blocker는 모두 해소됐고, 공개 배포·실제 시민 외부 LLM·원격 Git/CI는 현재 구현과 분리된 미래 승인 사항이다.

> 역사적 상태 주석(2026-07-20): 이 계획 본문의 `현재`, `남은`, `deferred` 표현은 2026-07-14
> 승인 시점의 기록이다. 이후 private source remote와 collaboration CI는 ADR-0019/COLLAB-001이
> successor로 소유한다. local-only Docker/Supabase/DeepSeek gate는 계속 유효하다.

## 미지의 영역과 인터뷰

| ID | 영향 | 질문 | 상태 | 결정 |
|---|---|---|---|---|
| Q-REPO-001 | Git·rollback·CI | 새 독립 저장소 여부 | Resolved | 새 local repo, `main`; 실행은 계획 승인 후 |
| Q-DEV-001 | 모든 manifest·CI | runtime/package manager | Resolved | Node 24.x+pnpm, Python 3.12+uv |
| Q-DATA-001 | 시민 근거·일정 | 작성/승인/기한 | Resolved | AI/Data·Backend 작성, PM 승인, 2026-07-20 |
| Q-LLM-002 | 공급자·비용 | 실제 provider와 비용 경로 | Resolved | 사용자 기존 DeepSeek 잔액, 새 충전 없음 |
| Q-LLM-003 | 개인정보·외부 처리 | 호스팅 provider 허용 범위 | Resolved for synthetic demo | local/private 서버 검증 합성 fixture만; 실제 시민/public 금지 |
| Q-DB-001 | schema·migration·RLS·rollback | Supabase CLI SQL vs Alembic | Resolved | Supabase CLI versioned SQL; 실행은 계획 승인 후 |
| Q-PRIV-002 | 외부 payload·품질 | 이름·상세주소 오탐/누락 기준 | Resolved | 보수적 마스킹; 완화는 80% 미달 원인 입증+재승인 |
| Q-CHAT-001 | API·보관·UX | 브라우저 전달형 구조화 문맥 vs 서버 TTL 세션 | Resolved | current-tab transcript + 15분 signed context token; 서버 세션·raw transcript 없음 |
| Q-API-001 | HTTP·FE·관측 | SYSTEM_ERROR 200 vs 503 | Resolved | 정책 응답 200, 안전 대체 없는 시스템 불능 503 |
| Q-CI-001 | 원격 백업·gate | private remote+CI vs local Git | Resolved for current phase | local Git+수동 gate, 원격/CI deferred |
| Q-LLM-004 | 모델·비용·지연 | DeepSeek V4 model과 app hard cap | Resolved | `deepseek-v4-flash`, thinking off, max 1024, concurrency 1, retry 1, run outbound attempt 30 |

## 제안 설계

- 데이터 흐름:

```text
브라우저 raw question+화면 transcript(현재 탭 메모리)
→ optional 15분 signed context token 전달
→ API 길이/형식·token 서명/TTL/closed claim 검사
→ PII 탐지·마스킹
→ intent/scope 분류
→ ACTIVE KB intent+keyword/metadata 검색
→ 근거 gate
→ 서버 allowlist 합성 fixture만 승인된 DeepSeek V4 또는 disabled/template adapter
→ JSON schema 검증
→ 서버가 source_id를 KB metadata와 결합
→ 시민 응답
→ SUCCESS/FOLLOWUP은 새 context token 가능, FALLBACK은 null
→ 질문 없는 interaction_event
→ 지원 범위 내 실패만 masked_question(30일)
→ 운영자 후보 작성 → 다른 PM 승인자 → ACTIVE KB
```

- 컴포넌트 경계:
  - `apps/web`: `/`, `/chat`, local/private `/admin`; API·DB 비밀 없음.
  - `apps/api`: route → application service → domain policy → repository/provider. 마스킹 전 provider 경로가 존재하지 않게 한다.
  - `packages/shared-contracts`: OpenAPI 생성 타입·enum; 수동 중복 타입 금지.
  - `supabase/migrations/`: Supabase CLI SQL 단일 실행 계보. `database/schema-v1.draft.sql`은 논리 참고본.
  - `data/official`: 작성·PM 승인·출처·확인일·lineage가 완료된 레코드만 ACTIVE seed.
  - context signer/verifier: Python 표준 라이브러리 HMAC-SHA-256, closed enum/ID claims, 900초 TTL. 인증/공식 사실 용도가 아니며 DB/session/log 없음.
- API/DB 변경:
  - OpenAPI 2.0 draft의 200 `ChatResponse`와 503 `SERVICE_UNAVAILABLE`, 상태별 schema, 관리자 응답 schema를 구현과 정합화한다. `session_id`를 거부하고 request/response `context_token` 계약과 FALLBACK-null을 고정한다.
  - DB는 ACTIVE/승인 불변조건, OUT_OF_SCOPE 행 금지, 텍스트 파기 job, backend-only 권한을 migration/test로 고정한다.
- 보안/개인정보:
  - raw request body logging 금지, app DB에서 IP/device ID 미수집, provider key는 server env만 사용한다.
  - DeepSeek adapter는 server fixture allowlist를 강제하고 실제 시민·PII·민감정보·public 요청을 거부한다. 기본 disk cache를 전제로 최소 KB context만 보낸다.
  - transcript/token은 current-tab memory만 사용하고 token에는 free text·PII·URL·KB 본문을 넣지 않는다. 만료/위변조는 문맥 없음으로 처리하며 token과 secret을 저장·로그하지 않는다.
  - local/private admin header는 인증으로 표현하지 않는다. public env에서는 관리자 route가 404/403이어야 한다.
  - 공식/mock/test 데이터를 열과 UI 배지로 분리한다.
- 실패/장애 처리:
  - LLM 실패+KB 충분이면 서버 템플릿 SUCCESS, 근거 부족이면 정책 FALLBACK, 안전 대체가 없는 실제 서비스 불능만 503 `SERVICE_UNAVAILABLE`을 적용한다.
  - 실제 provider는 timeout 1회 제한 재시도, circuit/fallback, 질문 없는 request-id/latency logging을 사용한다.
  - DB/provider 장애 때 raw question을 임시 저장하지 않는다.

### 최종 계획 승인에 포함할 초기 의존성

- Web production: `next`, `react`, `react-dom`.
- API production: `fastapi`, `uvicorn`, `pydantic`, `psycopg[binary,pool]`, `httpx`.
- Context signing은 Python 표준 라이브러리만 사용하고 JWT/세션 패키지를 추가하지 않는다. DeepSeek는 별도 SDK 대신 이미 필요한 `httpx`로 직접 adapter를 구현한다.
- Development/test: TypeScript, Tailwind CSS, ESLint, Vitest/Testing Library, Playwright, axe-core, Pytest, pytest-asyncio, Ruff, Mypy와 Supabase CLI. 이는 런타임 제품 의존성과 분리해 lockfile에 고정한다.
- 정확한 호환 patch 버전은 구현 1단계에서 공식 호환성 확인과 lock resolution 후 기록한다. 위 production 목록 밖 패키지는 다시 승인받는다.

## 단계별 구현

각 단계는 이전 단계의 인수 기준과 테스트가 통과하고 구현 노트·버전·diff 자체 리뷰가 끝나야 다음 단계로 넘어간다.

1. **저장소·도구·환경 스캐폴딩과 health**
   - 변경: 독립 Git `main` 초기화와 `codex/DEV-001-repo-scaffold`, root workspace/lock, `apps/web`, `apps/api`, `.env.example`, local run scripts, `/health`, `/ready` 기본 계약.
   - 설치: 승인된 Node 24.x+pnpm, Python 3.12+uv와 위 초기 의존성 목록. 이 최종 계획의 `진행` 승인을 목록 승인으로 간주하며 목록 밖 production package는 추가 승인.
   - 테스트: clean install, web lint/typecheck/build, API lint/typecheck/unit, health/ready smoke, secret scan.
   - 완료 증거: 신규 개발자가 문서만으로 로컬 두 앱을 기동하고 health 200을 재현.
2. **버전 migration과 공식 KB/기관 데이터**
   - 변경: Supabase CLI 초기 SQL migration, 명시적 보상/rollback SQL, backend-only 권한, seed importer, source registry lineage; AI/Data·Backend 작성, PM 승인.
   - 테스트: empty DB `db reset` replay·보상 rollback/replay, ACTIVE만 검색, 자기 승인·OUT_OF_SCOPE·파기 제약, 공식/mock 분리.
   - 완료 증거: PM 승인된 KB 20건·기관 3건·지역×민원 매핑 10~12건, 작성자≠승인자, 출처/확인일 누락 0.
3. **질문 마스킹·분류·검색·구조화 응답 도메인**
   - 변경: 보수적 PII redactor, intent/scope classifier, keyword/metadata retriever, grounding gate, provider protocol, 합성 fixture allowlist, JSON validator, source resolver, DeepSeek atomic run counter.
   - 테스트: 이름·주소 포함 PII fixture, 자유 입력 provider 차단, payload spy, 정상/모호/폴백 표본, DRAFT/PENDING 노출 0, LLM 출처 metadata 생성 무시, exact model/thinking/max, hidden retry off, concurrency 1, count 28/29/30 경계.
   - 완료 증거: 원문 persistence/log 0, 표본의 결정적 template 경로 통과.
4. **`/api/v1/chat`과 `/chat`**
   - 변경: signed context token, chat API·503 공통 오류 envelope, `/` 소개·지원 분야·진입, 정상 카드·출처·후속질문·4개 폴백·지역/기관 카드, 쉬운 말·큰 글씨.
   - 테스트: OpenAPI/JSON Schema 동일 fixture에서 `session_id` 거부·context required/nullability·FALLBACK null, tamper/expiry silent reset, 900초 TTL, current request region 우선, 200/503 분기, 390/430px E2E, 키보드·focus·contrast, loading 중복 전송 방지·503 재시도·empty office.
   - 완료 증거: 홈 E2E와 정상 10/모호 2/폴백 8 시나리오, 사용자-visible source/next action, current-tab 연속성·새로고침 소멸, token/secret persistence/log 0.
5. **이벤트와 실패 질문 텍스트 수명**
   - 변경: text-free events, eligible failure 저장, 30일 멱등 NULL purge, purge empty state, backup restore pre-open hook.
   - 테스트: DB/log raw search 0, OUT_OF_SCOPE/FOLLOWUP row 0, 경계시각·재실행·FK 보존·복구 후 purge.
   - 완료 증거: 파기 전후 schema/API/admin 상태와 최소 감사 로그.
6. **local/private `/admin` 개선 루프**
   - 변경: 실패 목록/상세·사유 확인, 후보 작성/제출/반려 후 재작성, 다른 승인자 승인, 원자적 ACTIVE 생성, 품질 카드, 최소 감사 이력.
   - 테스트: 역할·자기 승인·상태 머신·PII 후보 차단·public route off·mock 배지, audit action/actor/target/old-new status/changed fields와 질문·답변 snapshot 0.
   - 완료 증거: 운영자/PM 역할로 전체 흐름을 재현하고 승인 전 시민 노출 0.
7. **REG-01 개선 전후 회귀와 품질 강화**
   - 변경: 침대 프레임 fixture, 표본 평가 리포트, 접근성·성능·회귀 gate.
   - 테스트: 승인 전 fallback→승인 후 출처 SUCCESS, 100명/1분 제한 smoke, 평균/p95/error 측정, EVENT/EVALUATION/MOCK 비합산·배지 항상 표시.
   - 완료 증거: 수치 출처와 한계가 UI·보고서에 표시되고 mock이 공식 성과로 합산되지 않음.
8. **local demo·백업·인수인계; 공개 배포는 별도 승인 조건부**
   - 변경: local live→provider disabled/template 대체 runbook, 매일/위험 migration·milestone 전 gitignored logical dump, 30일 dump 삭제, RPO 24h/RTO 60m, 신규 개발자 handoff. 계정/리전/비밀/CORS/log/admin gate가 별도 승인된 경우에만 managed config를 추가한다.
   - 테스트: seed reset/replay와 dump restore drill, 복구 후 서비스 개방 전 retention purge, secret rotation, public admin denial, rollback, 단일 PC 손실 잔여 위험 기록.
   - 완료 증거: 신규 개발자 clean local 재현·restore 1회와 인간 승인 범위가 분리된 handoff. 녹화본은 발표 승인이 있을 때만 보조 산출물.

## 테스트 계획

- 단위: domain enum/state, masking, grounding, source resolver, retention clock, authorization.
- 계약: OpenAPI parse/lint, generated type drift, JSON Schema examples, 200 `ChatResponse`의 SYSTEM_ERROR 거부, 503 exact envelope, 상태별 response invariants.
- 문맥 보안: `session_id` 거부, 900초 TTL, claim allowlist, tamper/expiry reset, FALLBACK null, current request 우선, token/secret의 DB·log·browser storage 0.
- 통합: PostgreSQL migration/rollback, ACTIVE filter, approval transaction, purge FK retention, provider test double.
- E2E: 3 pages, 20 sample questions, operator→approver→requery, admin public-off.
- 보안/PII: payload spy, DB/log recursive scan, secret scan, candidate PII rejection, raw request logging disabled.
- 접근성: automated axe 계열 검사+키보드/포커스/zoom/contrast 수동 체크.
- 성능: deterministic cached/template route로 100 virtual users/1 minute; 실제 LLM path는 별도 latency/quota report.
- LLM guard: exact model/config, synthetic allowlist, outbound attempt 28/29/30 경계, retry 포함 cap, max in-flight 1, hidden retry 0, cap 이후 network 0.

## 버전 변경 계획

- app/web: 스캐폴딩 완료 시 `0.1.0`.
- api: 현재 `2.0.0-draft`; Q-CHAT-001의 `session_id` 제거/required nullable context를 ADR-0010의 major draft로 기록. 첫 수직 흐름 구현 시 같은 계약을 동결하고 호환 변경만 minor/patch로 관리.
- schema: 현재 `0.2.0-draft`; timestamp migration 계보는 semantic version과 분리하고 첫 실행·검증 완료 시 manifest를 호환 가능한 `0.3.0-local`로 올린다.
- data: PM 승인 seed 전 `0.0.0-not-populated`, 20 KB/3 office 승인 후 `0.1.0`.
- prompts: provider/model policy는 `0.0.2-deepseek-v4-flash-selected`; 실제 prompt 작성·평가 승인 후 `0.1.0`.
- tests: 현재 `0.3.0-spec`, scaffold 실행 테스트 추가 후 호환 minor, 회귀 완료 `1.0.0` 검토.
- docs: 각 slice와 구현 노트마다 patch/minor 갱신.

## 위험과 롤백

- 위험: DeepSeek cap 우회·숨은 retry·기존 잔액 소진·기본 disk cache.
  - 조기 신호: outbound attempt 30 초과, 동시 호출 2+, 실제 시민 payload 시도, 잔액 부족/429.
  - 롤백: provider flag off, disabled/template로 격리, 합성 fixture 외 전송 0건을 재검증하고 실제 LLM 완료를 주장하지 않음.
- 위험: 공식 데이터 7/20 지연.
  - 조기 신호: 7/18까지 작성·PM 승인 50% 미만.
  - 롤백: 승인된 일부 KB만 ACTIVE; mock으로 대체하거나 공식 완료를 과장하지 않음.
- 위험: migration/RLS/retention 복잡도.
  - 조기 신호: empty DB reset/replay·보상 rollback/replay 또는 purge FK test 실패.
  - 롤백: 직전 migration down/DB 재생성; 운영 데이터 삭제는 인간 승인 후.
- 위험: PII 누락.
  - 조기 신호: payload spy/DB scan에서 원문 또는 변형 PII 발견.
  - 롤백: 외부 provider flag off, affected local synthetic rows purge, 회귀 fixture 추가.
- 위험: public admin 오노출.
  - 조기 신호: public env에서 admin route 2xx.
  - 롤백: deploy 중단·route/env gate off; local/private로 복귀.
- 위험: context token을 암호화/인증으로 오해하거나 transcript/token을 저장.
  - 조기 신호: free-text claim, local/session storage, token/secret 로그, token으로 ACTIVE/source 판단.
  - 롤백: token 발급 flag off·secret rotate, 완전 무문맥 요청으로 복귀, leak sentinel 0 재검증.
- 위험: 원격 Git/CI/off-device backup 부재로 단일 PC 전체 손실.
  - 조기 신호: 24시간 초과 dump, restore 증거 없음.
  - 롤백: 승인 seed+migration으로 재생성; 비재현 데이터 손실 가능성을 숨기지 않고 원격 연결 전까지 수용.

## 인간이 승인해야 하는 사항

- 현재 남은 인터뷰 A/Blocker는 없다.
- 이 계획과 명시된 초기 production dependency 목록을 승인하고 구현을 시작한다는 명시적 `진행`/`구현 시작`. exact patch는 lockfile 생성 시 기록한다.
- 이 승인은 독립 local Git 초기화, 개발 도구 설치, local/private 합성 fixture의 30회 cap 안 DeepSeek live smoke를 허용하지만 key 값을 저장소/로그에 넣는 것은 허용하지 않는다.
- 이 승인은 공개 배포, 실제 시민·PII의 외부 LLM 전송, 원격 저장소/CI, 실제 사용자 데이터, 파괴적 DB 삭제, 목록 밖 production dependency를 허용하지 않는다.

같은 계약 안의 helper 분리, fixture, formatting, internal naming, private refactor는 AI가 자율 처리한다.

## 진행 기록

- 2026-07-14: DISC-001 완료. 활성 코드 0, Git 경계·공식 데이터·보안·retention gap 확인.
- 2026-07-14: 인터뷰 batch 1 반영. D-009~D-015, ADR-0002/0004/0005/0007, OpenAPI/DB draft 0.2.0 동기화.
- 2026-07-14: 인터뷰 batch 2 반영. DeepSeek 합성 전용, Supabase SQL, 보수적 마스킹, 503, local 수동 gate 확정. OpenAPI 1.0.0-draft와 ADR-0008/0009 동기화.
- 2026-07-14: 인터뷰 batch 3 반영. DeepSeek Flash guard와 client-carried signed context 확정, A/Blocker 0, OpenAPI 2.0.0-draft와 ADR-0010 동기화.
- 2026-07-14: 상태를 Draft/Review로 전환. 제품 코드·Git init·도구 설치·외부 호출 0.
- 2026-07-15: 사용자가 `진행`을 명시해 계획과 초기 production dependency 목록을 승인. Phase 1 저장소·도구·health 구현 시작.

## 결과와 회고

- 실제 결과: 아직 실행 전.
- 계획과 달라진 점: hosted provider를 exact DeepSeek Flash guard로 좁혔고 실제 시민 호출 대신 합성 fixture 경계를 추가했다. DB는 Supabase CLI SQL, 기술 장애는 503, chat memory는 서버 무세션 signed context로 확정했다.
- 다음 단계: 사용자가 이 계획과 초기 dependency 목록을 검토하고 `진행`/`구현 시작`으로 명시 승인. 승인 전 구현 없음.
