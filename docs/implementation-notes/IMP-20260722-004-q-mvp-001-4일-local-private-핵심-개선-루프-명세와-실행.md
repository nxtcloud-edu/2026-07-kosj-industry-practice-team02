# IMP-20260722-004 — Q-MVP-001 4일 local/private 핵심 개선 루프 명세와 실행

- Date/Time (KST): 2026-07-22T02:10:51+09:00 ~ 2026-07-23T08:47:41+09:00
- Task ID: MVP-001 / Q-MVP-001
- Type: implementation
- Status: **Review / local-private AI scope complete; human Draft PR and manual demo·accessibility remain**
- Author/Agent: 사용자(PM·제품 결정), Codex owner(아키텍처·Backend·Data·Security·통합·문서), 병렬 agent(`/admin` Backend/Frontend)
- Branch: `codex/MVP-001-four-day-core-loop`
- Base commit: `origin/main@9044ddb`
- Related: D-058, ADR-0020, MVP-001 design/plan, DATA-SEED-002 plan, RFP-P0-001~012

## 1. 사용자 요청과 인수 기준

Q-MVP-001=A로 2026-07-25까지 local/private 핵심 개선 루프 MVP를 목표로 한다. source-of-truth와
현재 저장소를 대조해 4일 축소 명세와 날짜별·역할별 계획을 확정하고, owner/팀원 PR 경계,
19 ACTIVE, PII/chat 계약, 결정적 chat API와 `/chat`, 실패→후보→별도 승인→20번째 ACTIVE,
최소 `/admin`, 표본·회귀·보안·데모 순으로 즉시 실행한다.

완료 판정은 코드 존재가 아니라 실제 local DB의 19→20 ACTIVE와 재질의 개선, 표본 20/20,
보안·API·Web·DB 전체 gate를 요구한다. DeepSeek 품질 튜닝, 고급 UI, 100명 성능, 자동 백업,
public 배포는 7월 25일 뒤로 연기한다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who | 사용자/PM이 정책·DB migration·실제 데이터와 merge를 승인하고, Codex owner가 Backend/Data/Security/통합, Frontend 역할이 `/chat`·`/admin` UI를 담당 |
| When | 2026-07-22 시작, 2026-07-25 local/private 데모 목표 |
| Where | private GitHub `Sejong_AI`, Windows owner worktree, Docker/Supabase local, `/chat`, `/admin` |
| What | 승인된 공식 KB 기반 시민 답변과 실패 질문을 사람 승인으로 개선하는 한 바퀴 |
| Why | “모르면 지어내지 않고, 알면 끝까지 안내한다”를 외부 LLM·공개 배포보다 먼저 검증하기 위해 |
| How | PII 마스킹→결정적 분류→ACTIVE/OFFICIAL 검색→근거 gate→구조화 응답/폴백→실패·후보·별도 승인 |
| How much | initial 19→20 ACTIVE, 표본 20, 회귀 1, local/private, 외부 사용비 0원 |

## 3. 조사 파일과 시작 상태

- 권위: `AGENTS.md`, `docs/00_SOURCE_OF_TRUTH.md`, TEAM_DECISIONS, PROJECT_PLAN,
  RFP_MATRIX, ADR-0004/0007/0009/0010/0016/0017/0019/0020, 활성 contracts와 DB migration.
- 계획: MVP-001 4일 plan과 DATA-SEED-002 successor plan.
- 코드: PII core와 DB write/approve capability는 있었으나 `/api/v1/chat`, chat orchestration,
  최소 admin API/UI는 없었다.
- 데이터(역사적 시작 기준선): immutable `.1`과 corrected `.2` 19/3/10 artifact가 존재하지만 당시
  실제 DB import 전체 PASS는 없었고 `official_data=0.0.0-not-populated`였다. Section 17~18의 current
  actual evidence가 이 시작 상태를 이후 local 19→20·`/ready=200`으로 갱신한다.
- Git/GitHub: `origin/main@9044ddb`; PR #4는 head `37dfc8b`, OPEN/CLEAN/MERGEABLE, hosted checks green.

## 4. 선택한 설계와 버린 대안

### 선택

- local MVP 시민 정상 답변은 DeepSeek 없이 결정적 template를 사용한다.
- chat 응답은 status-discriminated API 3.0.0-draft이며 출처·기관은 서버가 DB metadata에서 결합한다.
- `PRIVACY_UNRESOLVED`는 질문/failed row/event/provider/source/context가 모두 0인 HTTP 200 고정 폴백이다.
- `/chat`은 same-origin fetch와 memory-only transcript/context를 사용한다.
- admin router는 기본/public 앱에 등록하지 않으며 local/private composition에서만 활성화한다.
  demo header는 인증이 아니다.
- `/admin` fixture는 `시연용 샘플`을 표시하며 MOCK 후보의 ACTIVE 승인을 UI와 transport에서 모두 차단한다.

### 제외·연기

- DeepSeek 시민 답변: 품질·비용·개인정보 tuning 뒤로 연기.
- 직접 `app_private` read 또는 admin DSN 우회: RLS/최소권한을 깨므로 제외.
- MOCK 후보 ACTIVE 승인: 공식/mock 혼합이므로 제외.
- T-16~T-18 임의 계약/DB 변경: Q-MVP-002 답 전 보류.
- 관리자 DB read migration: Q-DB-004 답 전 보류.
- durable chat idempotency header/DB key: Q-API-002 답 전 보류.

## 5. 구현 결과와 변경 범위

| 영역 | 결과 | 주요 파일 |
|---|---|---|
| 계약 | API `3.0.0-draft`, shared `0.3.0`; ChatResponse discriminated union, 5 fallback, strict admin/error/HTTPS 계약 | `contracts/**`, `packages/shared-contracts/**`, `apps/api/.../contracts/**` |
| chat core | 마스킹 consumer, 6 intent 분류, ACTIVE/OFFICIAL retrieval, grounding, template response, 900초 서명 context, safe event | `apps/api/src/sejong_ai_api/chat/**` |
| API | `/api/v1/chat`, 매 요청 repository readiness 재검사, request-id 일치; public-default admin router 0과 local fixed demo allowlist | `api/chat.py`, `api/admin.py`, `main.py`, `local.py`, `admin/**` |
| `/chat` | same-origin typed client, SUCCESS/FOLLOWUP/5 fallback, source/office, retry/error/loading, memory-only context, 항상 쉬운말 요청 | `apps/web/src/app/chat/**`, `apps/web/src/lib/chat-api.*`, `next.config.ts` |
| `/admin` | server-only env gate 뒤 fixture-only failure/detail/reason/candidate/submit/review UI, role split, purge 표시, mock badge·승인 차단 | `apps/web/src/app/admin/**` |
| E2E | `/chat` 9개와 `/admin` 3개를 390/430/desktop에서 검증; 단일 local server worker 3 고정 | `tools/web-e2e/e2e/**`, `playwright.config.ts` |
| 문서 | 4일 명세/plan/status, API/DoD/privacy/SOT, ambiguity·version·note 동기화 | `docs/**`, `versions/manifest.json` |

제품 의존성은 추가하지 않았다. `uv.lock`과 API package version 변경은 API package `0.3.0` 정렬이며
새 provider SDK나 production library 도입이 아니다.

## 6. 상태 머신·데이터·계약 영향

```text
citizen question
  -> PII mask
  -> policy/classification
  -> ACTIVE+OFFICIAL retrieval
  -> grounding gate
  -> SUCCESS / FOLLOWUP / FALLBACK
  -> eligible failure only
  -> OPERATOR reason + candidate + submit
  -> different APPROVER approve/reject
  -> ACTIVE KB
```

- SUCCESS source URL/title/date는 LLM/UI 생성이 아니라 repository record에서만 온다.
- OUT_OF_SCOPE/FOLLOWUP/PRIVACY_UNRESOLVED는 failed row를 만들지 않는다.
- PERSONAL_LOOKUP/LEGAL_JUDGMENT의 범위 밖 표본 저장 의미는 Q-MVP-002 전까지 미확정이다.
- 현재 DB에는 admin list/get read capability 4개가 없어 실제 admin composition은 비활성이다.
- actual DATA cycle은 3회 모두 concurrency A 뒤 B에서 `CAPABILITY_WRITE_DID_NOT_BLOCK code=2`로
  중단됐다. `eb74ac8` observer correction 뒤 네 번째 실행은 별도 운영 결정을 받기 전 금지다.
- 실행 중 Docker container는 0개였고 `apps/api/.env` key-name 검사에는 `DATABASE_URL`만 있었다.
  값은 읽거나 출력하지 않았다. `CONTEXT_TOKEN_SECRET` 부재로 actual local app은 fail-closed다.

## 7. 버전 전후

| 축 | Before | After | 판정 |
|---|---|---|---|
| product spec | 2.2.5 | 2.3.0 | 4일 milestone |
| application | 0.3.0-pii-core | 0.5.0-local-core-loop-partial | DB actual 전 partial |
| web | 0.2.0-static-chat-shell | 0.3.0-chat-admin-mvp | chat actual client + admin fixture |
| API | 2.0.1-draft | 3.0.0-draft | 승인된 계약 freeze |
| shared contracts | 0.2.1 | 0.3.0 | generated TS 포함 |
| DB schema | 0.3.0-local | 0.3.0-local | migration 변경 0 |
| official data | 0.0.0-not-populated | 0.0.0-not-populated | actual PASS 없음 |
| mock data | 0.0.0-not-populated | 0.0.0-not-populated | UI memory fixture만 존재 |
| prompt | 0.0.2-deepseek-v4-flash-selected | 동일 | provider 미사용 |
| test suite | 1.0.0-collaboration | 1.1.0-core-loop | chat/admin/E2E 추가 |
| docs | 2.10.9 | 2.11.1 | 명세·상태·인수인계 |

## 8. 실행 명령과 실제 결과

| 명령 | 실제 결과 |
|---|---|
| `corepack pnpm --filter @sejong-ai/shared-contracts generate && ... test` | 87/87 PASS |
| `python -m pytest apps/api/tests -q` | 1516 passed, 11 skipped, 5 subtests passed; 3 sample policy + 8 local DB skip |
| `python -m ruff check apps/api/src apps/api/tests` | PASS |
| `python -m mypy apps/api/src apps/api/tests` | 60 source files PASS |
| `pnpm --filter @sejong-ai/web test -- --run` | 29/29 PASS |
| Web TypeScript + ESLint + Next build | PASS; `/`, `/chat` static, gated `/admin` dynamic build |
| `pnpm --dir tools/web-e2e test` | 최초 6-worker run 9 PASS/3 timeout; 원인 분리 후 worker=3 full 12/12 PASS |
| repository docs + focused docs/collaboration unittest | checker PASS; 21 PASS/1 symlink skip + 11 PASS |
| secret pattern + browser bundle scanner | PASS, 출력 0 |
| `scripts/verify.ps1 -Offline` | `PREFLIGHT-UV`에서 FAIL code 2; 현재 Windows PATH에 required `uv 0.11.28` 없음 |
| direct `unittest discover -s scripts/tests` | 최초 401 중 2 FAIL/2 skip: server-only Web env 이름의 stale assertion과 global uv 의존 runner test 확인 |
| 위 두 root regression focused rerun | 2/2 PASS: `API_INTERNAL_BASE_URL`/`NEXT_PUBLIC_*` 0 경계와 hermetic uv stub |
| direct root full unittest 재실행 | 401/401 PASS, 2 platform/local skip; 의도된 negative fixture의 `[FAIL]` 출력 포함 |
| `gh pr view 4 ...` | OPEN, non-draft, CLEAN/MERGEABLE, checks green |
| `docker ps ...` | command PASS, running container 0 |
| `git commit` / `git push -u origin codex/MVP-001-four-day-core-loop` | PASS; implementation commit `4b3f93a`, private branch published |
| `gh pr create --draft ...` | PASS; Draft owner-review PR #6, base `main`, auto-merge 0 |
| `gh pr checks 6 --watch` | PASS; collaboration policy와 Frontend CI hosted summary 모두 green |

첫 E2E 실패는 두 spec×3 viewport가 단일 local Next server에 6 worker로 붙으며 hydration 전에
controlled input fill이 실행된 test-harness concurrency 문제였다. 기존 수준인 3 worker로 고정한 뒤
전체 12개가 통과했다. Next build의 다중 worktree lockfile root warning은 비차단 경고로 남는다.
루트 full suite의 두 실패는 각각 의도한 same-origin 경계와 테스트 격리 누락에서 발생했으며,
두 focused 회귀는 수정 후 통과했다. exact uv가 없는 환경이므로 root offline runner 전체 PASS는
아직 주장하지 않는다.

마지막 Web 재실행의 첫 시도는 pnpm이 non-TTY에서 stale modules directory 재구성을 확인하려다
`ERR_PNPM_ABORTED_REMOVE_MODULES_DIR_NO_TTY`로 중단됐다. `CI=true`와 frozen/offline install로
현재 lockfile 그대로 작업공간을 복구한 뒤 unit 29/29, TypeScript, ESLint를 다시 통과했다.

독립 최종 diff review는 Critical 0, Important 7이었다. 코드로 닫을 수 있는 항목은 fixed demo
actor allowlist와 required header, server-only `/admin` 404 gate, fresh readiness, omitted office URL의
non-null JSON 직렬화, 무동작 쉬운말 토글 제거/항상 쉬운말 요청으로 교정했다. 남은 세 정책 표본,
durable retry idempotency, 실제 admin DB read는 각각 Q-MVP-002/Q-API-002/Q-DB-004 인간 결정에
직결되므로 Draft PR merge blocker로 유지한다.

## 9. 보안·개인정보·접근성·성능

- 원문 질문, context token, secret, DSN을 DB/access/error log나 산출물에 넣지 않았다.
- 개인정보 불확실 응답은 값 없는 고정 copy이며 외부 provider 호출 0이다.
- admin API router는 default/public 앱에서 등록되지 않아 404이며, 활성 local composition은 exact
  `OPERATOR-LOCAL-001`/`PM-LOCAL-001` role pair만 허용한다.
  Web `/admin`은 server-only `ADMIN_UI_ENABLED=true`가 아니면 404이며 public 활성화는 0이다.
- HTTPS-only source/office/candidate URL을 계약/Pydantic/DB model 경계에서 검증한다.
- `/chat`과 `/admin`은 storage/cookie/analytics 0, keyboard labels/skip link, 390/430/desktop
  overflow를 자동 검증했다. 최종 수동 대비/화면 리허설은 남았다.
- 성능 100명·자동 backup·public CORS/deployment는 연기됐으며 통과로 세지 않는다.

## 10. 공식 데이터와 mock 구분

- 공식 후보: PM 승인 19 KB/3 office/10 mapping의 immutable `.2` artifact. 실제 DB ACTIVE 증거는 없음.
- 20번째 목표 `KB-WASTE-03`: 기존 PM-approved official source를 실제 사람 승인 흐름으로만 생성한다.
- `/admin` 기본 화면 데이터는 memory-only MOCK이며 `시연용 샘플`로 표시하고 ACTIVE 승인 버튼을
  비활성화한다. manifest `mock_data`를 승격하지 않는다.

## 11. 마이그레이션·롤백·복구

- 이번 변경은 DB migration 0이므로 schema rollback은 없다.
- 계약/API/Web은 본 branch commit을 revert한다. generated TS는 OpenAPI에서 재생성한다.
- local app은 설정 또는 DB readiness가 없으면 `/ready`, `/chat`을 닫고, default/public 앱은
  admin router를 등록하지 않아 404를 반환한다.
- 향후 Q-DB-004=A면 `00650` forward/rollback·pgTAP·replay를 별도 계획/노트로 만든다.
- `.1`/`.2` immutable release는 수정하지 않는다. actual DB 실패 시 official version을 올리지 않는다.

## 12. 인간이 반드시 알아야 하거나 결정할 내용

1. Q-MVP-002: T-16~T-18을 `UNKNOWN`+개인조회/법적판단 reason으로 유지할지(A 권고),
   OUT_OF_SCOPE로 합칠지 결정해야 한다.
2. Q-DB-004: 실제 admin DB read를 위한 local `00650` migration을 승인할지(A 권고) 결정해야 한다.
3. Q-API-002: durable `Idempotency-Key` 공개 header와 DB identity를 추가할지(A 권고) 결정해야 한다.
4. DATA actual 네 번째 실행은 별도 결정이 필요하다. 현재 ACTIVE 19·READY 200을 주장할 수 없다.
5. local 실행 전 값 노출 없이 32-byte 이상 `CONTEXT_TOKEN_SECRET`을 설정해야 한다.
6. PR #4는 merge 가능하지만 아직 OPEN이다. 사용자/팀원이 검토·병합해야 한다.
7. 이번 owner 결과는 [Draft PR #6](https://github.com/tskwak111/Sejong_AI/pull/6)이며 자동
   merge하지 않는다. PR #4를 먼저 병합한 뒤 최신 `main`을 반영·재검증해야 한다.

## 13. AI 내부 구현 세부 — 인간이 굳이 이해하지 않아도 되는 내용

- classifier keyword table, stable tie tuple, response builder helper, request-id dependency override,
  fixture factory, CSS module 분리, E2E worker 수는 동결 계약/인수 기준 안의 내부 구현이다.
- admin service의 protocol/fake와 exception mapping은 실제 DB adapter가 생겨도 공개 contract를 바꾸지 않는다.

## 14. 재현·인수인계

1. 이 branch에서 shared contract generate/test를 실행한다.
2. API full pytest, Ruff, Mypy를 실행한다.
3. Web unit, TypeScript, ESLint, Next build 뒤 Playwright를 실행한다.
4. secret/docs/root 검사를 실행하고 결과를 이 노트에 추가한다.
5. Q-MVP-002/Q-DB-004/Q-API-002 답을 반영한다.
6. 별도 승인 시 Docker/Supabase actual DATA를 한 번 실행해 19/3/10, cleanup, READY를 검증한다.
7. Q-DB-004=A면 admin read migration/adapter 뒤 실제 실패→후보→별도 승인→20 ACTIVE→재질의를 검증한다.

## 15. 남은 위험과 현재 완료 판정

- 완료: 4일 명세/계획, `.2` filesystem 교정, PII/chat/admin 계약, deterministic chat core,
  `/api/v1/chat`, typed `/chat`, disabled admin API, fixture `/admin`, 자동 code/web 보안 경계.
- 미완료: actual DB 19, actual readiness, Q-MVP-002 3표본, admin DB reads, 20번째 ACTIVE,
  actual 재질의 회귀, 전체 DB/root gate, final manual demo.
- 따라서 이 요청은 **부분 완료**이며 7월 25일 MVP 전체 완료로 표시하지 않는다.

## 16. 자체 리뷰

- [x] 승인 범위 안의 독립 코드/계약/UI 구현
- [x] product dependency 추가 0, public/LLM/remote DB 사용 0
- [x] API/contract/Web/E2E fresh gate
- [x] source-of-truth/ambiguity/plan/version 동기화
- [x] 구현 노트와 INDEX 갱신
- [ ] Q-MVP-002/Q-DB-004/Q-API-002 인간 결정
- [ ] local DB 19→20 actual 개선 루프와 final demo

## 17. 2026-07-22 continuation — approved core-loop integration evidence

### 승인·설계

- D-059/Q-MVP-002=A: `PERSONAL_LOOKUP`·`LEGAL_JUDGMENT`는 공개 `intent=UNKNOWN`과 정확한
  reason, `candidate_eligible=false`이며 local MVP에서는 question text·event·failed row·candidate가 0이다.
- D-060/Q-DB-004=A: local/private `00650` admin read capability와 matching rollback/pgTAP/repository를
  승인했다. public admin은 계속 기본 비활성이다.
- D-061/Q-API-002=A 및 D-063: optional UUID `Idempotency-Key`, correlation ID와 독립인 HMAC
  digest/claim token, 5분 lease, 정확한 24시간 TTL, startup+60초 purge/fail-closed readiness를 채택했다.
- D-064: immutable `.2`의 supported actual local seed PASS를 `official_data=0.1.0-initial.2`로
  승격했다. 00670 exact KB binding은 별도 진행 중이며 이 노트의 완료 증거가 아니다.

### 실제 결과와 버전

DATA-SEED actual continuation은 baseline·identity·forced rollback (`tables=8 partial=0`)·concurrency
A/B·KB 19/office 3/mapping 10 seed·replay 1·second-seed 및 compensation guard·final citizen 19/
exclusions 0/operational 0·cleanup을 PASS했고 final process/container는 0이다. `.2` bytes는 변경하지
않았고 DSN·비밀·질문 원문을 출력하지 않았다.

| 축 | 이전 | 현재 |
|---|---|---|
| product spec | 2.3.0 | 2.3.1 |
| application/web/api/shared | 0.5.0 / 0.3.0 / 3.0.0 / 0.3.0 | 0.6.0 / 0.4.0 / 3.1.0 / 0.4.0 |
| DB schema / official data | 0.3.0-local / 0.0.0-not-populated | 0.4.0-local / 0.1.0-initial.2 |
| test suite / docs | 1.1.0 / 2.11.1 | 1.2.1 / 2.12.2 |

Focused evidence: API chat/admin/local/repository 100 PASS, admin source policy 29 PASS, contracts
89/89 PASS, Web unit 35/35 and 390/430/desktop E2E 15/15 PASS, 당시 section-17 기준 DB pgTAP 8 files/320 and
supported seed cycle PASS. The first root integration attempt is **not** final green: one stale Web
environment expectation was fixed and focused PASS; nine Windows PowerShell subprocess timeouts remain
transient/unresolved at root-gate level, although a representative timeout test passed individually.

### 보안·인수인계·남은 위험

- raw question/PII/secret/DSN/provider payload persistence remains 0. Actual candidate URL validation
  now rejects userinfo, non-default port, fragment, sensitive query keys and encoded PII and permits
  only the approved six official hosts.
- default Web `/admin` is fixture; actual transport requires explicit local flags. Default/public API
  admin remains disabled. DeepSeek actual, remote DB, public deployment, auto-merge and `00700` remain
  prohibited/pending.
- Historical section-17 checkpoint의 next gates는 configured `/ready=200`, distinct-author 20th
  ACTIVE/requery와 full root/DB/API/Web/security였다. Section 18의 final evidence가 이를 완료했다.
  AI-internal details (claim factories, adapter/fake structure, background purge loop) may change only
  while preserving the approved contracts and evidence boundaries.

## 18. 2026-07-22 actual closeout continuation — local/private 19→20 evidence

### 무엇·누가·언제·어디서·왜·어떻게

2026-07-22 KST에 Codex owner와 독립 검토자가 Windows local/private runner와 final local DB에서
MVP-001의 실제 핵심 개선 루프를 다시 실행했다. 목적은 immutable initial `.2`의 19건 seed 증거와
별개로, application readiness 및 `KB-WASTE-03`의 실패→사유 확인→후보→다른 승인자 승인→재질의
SUCCESS를 한 번 연결하는 것이었다. 공개 환경, remote DB, 실제 시민 입력, DeepSeek actual 호출,
공개 관리자, 배포는 사용하지 않았다.

### 실제 실행 결과

- DATA-SEED-002 fresh run은 exact identity, forced rollback `tables=8`/`partial=0`, concurrency A/B,
  KB/office/mapping `19/3/10`, replay 1, second-seed block, compensation block, final citizen 19 /
  exclusions 0 / operational 0 및 cleanup까지 PASS했다. final process/container는 0이다.
- dedicated Windows `run_local_api`는 final DB에서 `/ready=200`을 확인했다. 이는 local app factory의
  evidence이며 import-safe 기본 앱의 503 또는 public/remote readiness를 바꾸지 않는다.
- clean actual regression은 initial ACTIVE 19에서 시작해 fallback, 같은 logical key K1의 business
  replay(서로 다른 correlation), 정확히 한 건의 NEW failure, reason confirm, public_id 없는 HTTP
  candidate create, submit, same-writer fake approver 차단, `PM-LOCAL-001` 승인, K2 SUCCESS와
  `KB-WASTE-03`의 정확한 server-bound source, old K1 fallback을 순서대로 PASS했다. final ACTIVE는
  20, 네 분야는 각 5건, target은 정확히 한 번이다. 종료 뒤 `/ready=200`을 다시 확인했다.
- 이 과정은 local runtime projection의 20번째 ACTIVE를 증명하지만 immutable `.2` release의 19/3/10
  공식 artifact를 수정하거나 새 공식 source data를 만들지 않았다. 상세 분리는
  [`MVP-001 KB-WASTE-03 local workflow lineage`](../data-lineage/MVP-001-KB-WASTE-03-LOCAL-WORKFLOW.md)에
  기록한다.

### HTTP 422 발견·TDD 보정

첫 canonical candidate regression은 service에 도달하기 전 HTTP 422로 실패했다. 원인은 FastAPI가 JSON
object를 먼저 `dict`로 파싱한 뒤, strict UUID/date Pydantic field가 canonical wire string을 거부한
것이다. RED regression을 고정한 후 admin request field validator를 최소 변경해 **정확한 canonical
UUID/date wire string만** 받아 내부 strict type으로 변환했다. 전역 strictness, 다른 coercion 금지,
public_id server binding은 유지했다. implementation probe와 independent re-review는 Critical/Important/
Minor `0/0/0`이었고, HTTP bugfix re-review도 `0/0/0`이었다. regression runner의 사전 review `0/0/1`
minor는 exit-failure unit이 없다는 지적뿐이며 implementation probe는 PASS했다.

### 검증 명령과 결과

| 범위 | 실측 결과 |
|---|---|
| DATA disposable runner | fresh PASS; DB source gate pgTAP 9 files/356 tests, rollback absence/reapply 36/36 |
| Windows local API runner | `/ready=200`, independent review `0/0/0`, later focused 67 PASS (runner-own 14와 adjacent 46 포함) |
| actual regression | final 19→20 flow PASS; focused API 85 PASS 및 final `test_api` 16 PASS |
| API final full gate | 1,640 PASS, DB-only 8 skip, 기존 Starlette warning 1, subtests 5; Ruff format/check 및 strict Mypy 64 files PASS |
| Web final gate | unit 48/48, lint/typecheck/build PASS (workspace-root warning only), 390/430/desktop E2E 15/15 PASS |
| Contracts/sample | generate drift check와 contract 89 PASS; exact T-01~T-20 + meta test 21 PASS/skip 0 |
| Clean disposable DB | pgTAP 9 files/356 assertions, API DB integration 8/8 PASS |
| current-tree scanners | direct scanner exit 0, self-scan PASS, independent review Critical/Important/Minor `0/0/0` |
| root aggregate | `scripts/verify.ps1 -Offline` PASS |

API/Web/contracts/E2E/scanner, clean disposable DB와 root offline aggregate는 fresh PASS다. 표본
T-01~T-20은 별도 [결과 보고서](../test-reports/MVP-001-SAMPLE-20-RESULT.md)에 20/20 numerator를
기록했다. 이 표본은 deterministic pure-service 평가이며 provider/remote/public 또는 HTTP source-card
QA가 아니다. 100-user smoke, 자동 backup, DeepSeek tuning/actual, advanced UI, public deployment와
`00700`은 계속 deferred다.

### 보안·개인정보·접근성·성능·롤백

- raw question, answer snapshot, DSN, token, provider payload와 secret을 새 evidence에 기록하지 않았다.
  canonical regression의 실패 텍스트는 local policy 경계 안에서만 처리했고 public admin은 계속 금지다.
- `KB-WASTE-03` source title/URL/확인일은 LLM이 만들지 않고 서버가 approved metadata에서 결합했다.
  same-writer approve block과 idempotency K1/K2 경계도 실제 흐름에서 확인했다.
- Web의 390/430/desktop E2E 15/15, unit 48/48, typecheck/lint/build는 fresh final PASS다.
  workspace-root warning은 비차단 경고였고, 이번 결과는 100명 용량 보증이 아니다.
- API performance gate의 첫 parallel 실행은 `2.007s`로 threshold를 정직하게 초과했다. 같은 test의
  isolated 3회는 `1.07s`/`1.18s`/`1.06s`, isolated full suite도 PASS해 parallel-load artifact로
  판정했다. product performance code 수정은 하지 않았고 root 직렬 gate 결과는 계속 기다린다.
- current-tree scanner는 처음 synthetic fixture의 active-source pattern을 탐지했다. scanner를 완화하지
  않고 local variable rename과 source-split fixture로 교정했으며 direct exit 0, self-scan PASS와
  독립 review `0/0/0`을 확인했다. admin HTTP adapter final review도 `0/0/0`이다.
- atomic idempotency correction과 admin concurrent approval race correction은 각각 독립 final review
  Critical/Important/Minor `0/0/0`을 통과했다.
- rollback은 현재 9개 migration의 역순 `00670 → 00660 → 00650 → 00600 → 00500 → 00400 →
  00300 → 00200 → 00100`, absence/reapply 36/36 증거를 따른다. `.1`/`.2`는 immutable이며 local
  candidate/runtime 결과를 되돌려도 source release를 수정하지 않는다.

### 버전·인수인계·인간과 AI 경계

manifest의 product/API/shared/official-data 버전은 각각 `2.3.1`/`3.1.0-draft`/`0.4.0`/
`0.1.0-initial.2`를 유지한다. application은 `0.6.0-local-core-loop`, test suite는
`1.2.1-core-loop-closeout`, documentation은 `2.12.2`로 승격한다.

인간이 확인할 일은 Draft PR review/merge, 수동 demo·접근성 검수와 public/remote/DeepSeek/`00700`을
여는 별도 승인이다. validator의 내부 변환, test fake/claim factory, Windows runner 구현은 승인된
contract를 유지하는 AI 내부 세부다. local/private AI scope는 Review 단계이며 public-ready가 아니다.

### 최종 DB 복구와 실패 시도 기록

- 첫 command 시도는 direct `uv`가 PATH에 없어 실행되지 않았고 repository venv 명령으로 바로잡았다.
- Codex 실행 래퍼에서 `CI=true; corepack pnpm --dir apps/web test`를 호출하면 실행 직전 Web 개발
  의존성 407개가 production-only 상태로 제거되는 환경 부작용이 재현됐다. manifest와 lockfile은
  바뀌지 않았으며 frozen offline lockfile로 복구한 뒤 동일한 잠금 버전 Vitest/ESLint/TypeScript
  실행 파일로 Web 48/48, lint, typecheck를 확인했다.
- 존재하지 않는 `scripts/check_current_tree_secrets.py` 호출은 파일 부재로 실행되지 않았다. 현재 저장소의
  canonical PowerShell current-tree scanner와 Python Git-history scanner로 바로잡아 둘 다 PASS했다.
- 지원하지 않는 `--help` 조합은 runner가 mutation 전에 거부했다.
- populated final20 DB에 empty-DB precondition을 가진 pgTAP/API integration을 잘못 실행해 실패했고,
  API purge 검사가 demo failed-question text를 파기했다. 출력에는 secret, DSN, raw user value가 없었다.
- 이를 성공으로 덮지 않고 full reset 후 clean disposable pgTAP 9/356과 API DB integration 8/8을
  통과시켰다. 그 뒤 immutable `.2` seed와 actual 19→20 개선 loop/requery를 재실행해 final ACTIVE 20,
  four categories×5, target once와 `/ready=200`을 복원했다.
- clean integration이 30-day purge와 policy row-zero 경계를 증명한다. final DB는 local/private demo
  state이며 public admin authentication이나 production readiness 증거가 아니다.
- 잔여 Web 경쟁 조건 수정 뒤 root offline aggregate와 E2E 15/15를 다시 실행해 PASS했다. final DB
  read-only probe의 초기 PowerShell `-c` quoting/root-venv 시도는 실행되지 않았고, `app_private` 직접
  조회는 의도한 least-privilege 권한 경계에서 거부됐다. DB mutation은 없었다. repository API venv,
  `app_api.list_active_kb` capability와 Windows selector event-loop policy로 교정한 최종 probe는
  `/ready=200`, ACTIVE 20, `KB-WASTE-03` 정확히 1건을 PASS했다.
