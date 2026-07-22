# TASKS.md — 현재 백로그

> 이 문서는 우선순위와 의존성을 보여주는 작업 인덱스다. 실제 작업을 시작하면 실행계획과 구현 노트를 연결한다.

## Phase 0 — 발견·결정·정리

| ID | 우선순위 | 담당 영역 | 작업 | 상태 | 의존성 | 완료 기준 |
|---|---|---|---|---|---|---|
| DISC-001 | P0 | Architecture·Security·Data·Docs | [저장소 감사와 최종 기준 드리프트 보고서](docs/discovery/INITIAL_DISCOVERY_REPORT.md) | Done | 없음 | 코드/문서/데이터/계약 충돌표와 [IMP-20260714-001](docs/implementation-notes/IMP-20260714-001-초기-저장소-발견-감사.md) 작성 |
| DISC-002 | P0 | Architecture·Product·Security | 아키텍처 영향 인터뷰 | Done | DISC-001 | batch 1~3 기록, 인간 결정형 A/Blocker 0 |
| DOC-001 | P0 | Architecture·Docs | 결정 로그·ADR·모호성·계약·DB draft 동기화 | Done | DISC-002 | D-009~024, ADR-0002~0010, OpenAPI 2.0.1-draft와 source-of-truth 정합성 검사 통과 |
| PLAN-001 | P0 | Architecture·전체 | [local-first 기반과 승인형 민원 안내 실행계획](docs/plans/PLAN-20260714-001-foundation-and-governed-chat.md) | Done | DISC-002, DOC-001 | 2026-07-15 사용자 `진행` 승인; 공개/실제 시민 경계는 별도 승인 유지 |
| COLLAB-001 | P0 | Platform·Security·Docs·Frontend | [private GitHub·Codex Cloud 협업 전환](docs/superpowers/specs/2026-07-20-github-codex-cloud-collaboration-design.md) | In Progress — Tasks 1~4 complete; Task 5 partial; Task 6 complete; Task 7 ready for human merge | D-047~D-058/ADR-0019/0020, approved [execution plan](docs/superpowers/plans/2026-07-20-github-codex-cloud-collaboration-transition.md), [owner checklist](docs/handoffs/HANDOFF-20260721-OWNER-GITHUB-CLOUD-CHECKLIST.md) | PR #5 merged at `9044ddb`. PR #4 was corrected to note `014`, head `37dfc8b`, exact note+INDEX two-file diff, CLEAN/MERGEABLE and hosted summaries green; Frontend collaborator/user merge pending. MFA/recovery yes/no도 Pending이며 public deployment/remote DB는 계속 차단한다 |
| MVP-001 | P0 | 전체 | [7/25 local/private 핵심 개선 루프](docs/superpowers/specs/2026-07-22-four-day-local-private-core-loop-mvp-design.md) | In Progress — non-DB core implemented; human/DB gates pending | Q-MVP-001=A/D-058/ADR-0020, Q-MVP-002/Q-DB-004/Q-API-002, [audit](docs/discovery/MVP_001_FOUR_DAY_LOCAL_PRIVATE_AUDIT.md), [approved plan](docs/superpowers/plans/2026-07-22-four-day-local-private-core-loop-mvp.md) | 계약·deterministic chat·`/api/v1/chat`·typed `/chat`·public-default admin router 0·gated fixture `/admin` 구현/자동 gate 완료. ACTIVE 19/20, actual readiness/admin/requery, 표본 T-16~T-18, durable retry, final demo는 Pending. DeepSeek tuning·100명·자동 backup·public deploy는 7/25 뒤 |

## Phase 1 — 프로젝트 스캐폴딩

| ID | 우선순위 | 담당 영역 | 작업 | 상태 | 의존성 | 완료 기준 |
|---|---|---|---|---|---|---|
| DEV-001 | P0 | Platform·FE·BE | 독립 Git·Node 24/pnpm·Python 3.12/uv 모노레포와 health | Done | PLAN-001 Approved | corrected fresh default·warm-offline 24/24와 actual API/Web smoke, final P0/P1/P2 0; DB·승인 seed 전 `/ready=503` 유지 |
| DEV-002 | P0 | Platform·Security | 환경변수·비밀관리·local 수동 검증 gate | Done | DEV-001 | 예제 환경, 비밀 스캔, raw body logging off, synthetic/offline env 복원과 clean gate 통과 |
| DB-001 | P0 | Backend·Data·Security | [Supabase SQL v1 migration·보상 rollback·권한](docs/discovery/DB_001_DISCOVERY_REPORT.md) | Done | DEV-001 Done, approved DB spec/plan, D-026~D-032, ADR-0012/0013/0014, verified local baseline; D-046/ADR-0018 public hardening decision | disposable local/private schema baseline만 검증, production-ready 아님. patched-only exact loopback, pgTAP 282·integration 8/8·6단계 replay. 공식 DB row 0·`/ready=503`; `00700`은 public 준비까지 보류되고 구현·검증 전 public/remote 금지 |
| CONTRACT-001 | P0 | FE·BE·QA | OpenAPI 3.0·공유 타입 생성 경로와 chat/admin/200/503/context 계약 | Done | DEV-001, D-045/D-058 | API 3.0.0-draft, shared 0.3.0, discriminated ChatResponse·PRIVACY_UNRESOLVED·strict admin/error/HTTPS fixture와 generated TypeScript/Pydantic drift 0; 87/87 PASS |

### Phase 1 실행 상세 — PLAN-20260715-002

| ID | 우선순위 | 담당 영역 | 작업 | 상태 | 의존성 | 완료 기준 |
|---|---|---|---|---|---|---|
| DEV-001A | P0 | Platform | exact runtime과 root workspace contract | Done | PLAN-001 | Node/pnpm/Python/uv exact pin, config RED→GREEN, remote 0 |
| DEV-001B | P0 | Backend·Platform | FastAPI health와 pre-DB readiness | Done | DEV-001A | `/health=200`, `/ready=503` exact, uv lock, ruff/mypy/pytest |
| DEV-001C | P0 | Frontend·Platform | 최소 접근 가능 Next.js shell | Done | DEV-001A | frozen pnpm install, lint/typecheck/unit/build, 390/430px QA, [IMP-20260715-005](docs/implementation-notes/IMP-20260715-005-접근-가능한-next-js-애플리케이션-shell.md) |
| DEV-002A | P0 | Security·Platform | 서비스별 env·metadata-only log·secret/browser scan | Done | DEV-001B, DEV-001C | raw body/sentinel/browser secret 0, [IMP-20260715-006](docs/implementation-notes/IMP-20260715-006-서비스별-환경변수와-안전-로그-경계.md) |
| CONTRACT-001A | P0 | FE·BE·QA | 승인 계약 불변조건과 공통 fixtures | Done | DEV-001B, DEV-001C | SUCCESS source≥1·office/context/503 양 계약 fixture 정합, [IMP-20260715-007](docs/implementation-notes/IMP-20260715-007-승인-계약-불변조건과-공통-fixture.md) |
| CONTRACT-001B | P0 | FE·BE·QA | 생성 TS·Pydantic model drift gate | Done | CONTRACT-001A | 재생성 diff 0, 동일 fixture 통과, [IMP-20260715-008](docs/implementation-notes/IMP-20260715-008-생성-typescript와-pydantic-계약-drift-gate.md) |
| DEV-001D | P0 | Platform·QA·Docs | clean local verify와 Phase 1 마감 | Done | DEV-002A, CONTRACT-001B | corrected snapshot default·warm-offline 24/24, actual API/Web smoke와 final read-only review 완료 |
| DEV-002B | P0 | Platform·Security·QA | fail-fast local verification과 환경 복원 경계 | Done | DEV-002A, CONTRACT-001B | 24단계 gate, child exit 보존, 성공/실패 출력 비노출, synthetic/offline env 복원과 fresh review 통과 |

## Phase 2 — 시민 질문 수직 흐름

| ID | 우선순위 | 담당 영역 | 작업 | 상태 | 의존성 | 완료 기준 |
|---|---|---|---|---|---|---|
| DATA-001 | P0 | AI/Data·Backend 작성, PM 승인 | 공식 KB 20건·기관 3건·지역×민원 매핑 12건 staging 작성·전수 검수 | Done | [DATA plan](docs/superpowers/plans/2026-07-18-data-001-staging-and-review-package.md), D-033/D-035, ADR-0015 | PM-LOCAL-001의 35건 승인 evidence와 exact 19/3/10 projection materialize·63-test/canonical/hash review PASS; official release/seed/DB 변화 0, [IMP-20260719-004](docs/implementation-notes/IMP-20260719-004-data-001-pm-승인-증거-확정.md) |
| DATA-SEED-001 | P0 | Backend·Data·Security | 승인 record의 initial immutable official release·버전 seed·lineage | Blocked | DATA-001 approved manifest, D-036/D-038/D-039 | `.1` filesystem 19/3/10 release·dispatcher·offline gate PASS, actual DB는 legacy single-row guard에서 write 전 차단된 historical execution. `.1` 불변 보존하고 D-044의 DATA-SEED-002가 교정 소유. [lineage](docs/data-lineage/DATA-SEED-001-0.1.0-initial.1.md), [report](docs/test-reports/DATA-SEED-001-LOCAL-VERIFICATION.md) |
| DATA-SEED-002 | P0 | Backend·Data·Security | [immutable `.2` successor와 actual DB 재검증](docs/superpowers/specs/2026-07-20-data-seed-002-successor-release-correction-design.md) | Blocked — `.2` published; actual concurrency B | D-044/D-058/ADR-0017/0020, approved DATA-001 19/3/10, [approved execution plan](docs/superpowers/plans/2026-07-20-data-seed-002-successor-release-correction.md), [lineage](docs/data-lineage/DATA-SEED-002-0.1.0-initial.2.md), [report](docs/test-reports/DATA-SEED-002-LOCAL-VERIFICATION.md) | `.1`/v1 불변과 `.2` publication/dispatcher 검증 완료. actual 3회는 A까지 PASS, B는 `CAPABILITY_WRITE_DID_NOT_BLOCK`; cleanup PASS. OID-equality observer `eb74ac8` 독립 검토 0/0/0·commit 완료, 별도 실행 결정 전 재실행 0. PostgreSQL ACTIVE 19·READY 미주장, `official_data=0.0.0-not-populated` 유지 |
| READY-001 | P0 | Backend·Data·Platform | 실제 DB·필수 승인 seed readiness probe 전환 | Blocked | DATA-SEED-002 actual PASS, DEV-001B | DB 연결과 필수 ACTIVE KB/기관 seed가 모두 준비될 때만 `/ready=200`; 결손/장애는 503 |
| AI-001A | P0 | Backend·Security | [순수 fail-closed PII 마스킹 코어](docs/superpowers/specs/2026-07-20-ai-001-pii-masking-design.md)와 frozen v1 합성 평가셋 | Done | D-041/D-042/D-043, approved written spec, A-032 Resolved, [approved execution plan](docs/superpowers/plans/2026-07-20-ai-001a-pii-masking-core.md), [IMP-006](docs/implementation-notes/IMP-20260720-006-ai-001a-pii-마스킹-코어-구현.md) | privacy 1,161·architecture+privacy 1,165+5 subtests·full API 1,318+8 DB skips+5 subtests PASS. 13범주·5 reason, frozen 74 불변, actual 77 원문 유출 0·safe 219 오탐 0, raw/log/I/O/dependency 0, API/DB/data/provider/route 불변 |
| PII-CONSUMER-001 | P0 | Backend·Frontend 팀원·Security·Contract | `PRIVACY_UNRESOLVED` HTTP 200 consumer 계약 | Done for local/private | D-045/D-058/ADR-0004/0020 | source/context/office/provider/text/failed row/event/candidate 0, 고정 시민 copy, OpenAPI/JSON Schema/Pydantic/TS 동시 변경; persistent metadata는 reserved `00700` 뒤 별도 |
| AI-001 | P0 | AI/Data·Backend·Security | 보수적 PII 마스킹과 분류·검색·근거 gate·template 응답 | In Progress — deterministic core complete; actual DB pending | DATA-SEED-002, AI-001A, PII-CONSUMER-001, Q-MVP-002 | raw sentinel 격리, ACTIVE/OFFICIAL retrieval, grounding/template/context unit PASS. 표본 17/20; T-16~T-18과 actual 19 DB는 Pending |
| LLM-001 | P0 | AI/Data·Backend·Security | DeepSeek 합성 fixture adapter와 장애 fallback | Deferred after 2026-07-25 | AI-001, PLAN-001 Approved | Q-MVP-001 축소 범위에서 provider 호출 0; 품질·쿼터·retry/429/timeout tune은 후속 P1 |
| API-CHAT-001 | P0 | Backend·QA | `/api/v1/chat`·signed context와 공통 오류 계약 | In Progress — route complete; actual readiness pending | CONTRACT-001, AI-001 | SUCCESS/FOLLOWUP/FALLBACK/PRIVACY/503, 900초 token/tamper reset/source 결합·safe log 구현. idempotency와 actual DB `/ready=200`은 Pending |
| WEB-HOME-001 | P0 | Frontend 팀원·QA | `/` 서비스 소개·4개 지원 분야·한계·`/chat` 진입 | Done | DEV-001 complete; Q-WEB-001=A/D-037; [execution plan](docs/superpowers/plans/2026-07-19-web-home-and-static-chat-shell.md) | 정적 `/chat`·home CTA, 입력/저장/외부 요청 0, 390/430/desktop·키보드·focus·contrast·실제 Chrome UI 200%·prod dependency gate PASS, [IMP-20260719-005](docs/implementation-notes/IMP-20260719-005-web-home과-정적-채팅-준비-화면.md) |
| WEB-CHAT-001 | P0 | Frontend 팀원·QA | `/chat` current-tab 대화·카드·출처·폴백·기관 | In Progress — UI/client complete; actual DB E2E pending | API-CHAT-001, WEB-HOME-001 | same-origin typed client, 5 fallback/FOLLOWUP/source/office, 중복 전송·503 retry, memory/storage/cookie 0; unit 28 전체 및 `/chat` E2E 9 PASS |

## Phase 3 — 관리자 개선 루프

| ID | 우선순위 | 담당 영역 | 작업 | 상태 | 의존성 | 완료 기준 |
|---|---|---|---|---|---|---|
| LOG-001 | P0 | Backend·Security·Data | 비식별 이벤트·실패 질문 저장과 30일 텍스트 파기 | In Progress — service tests complete; actual DB pending | API-CHAT-001, Q-MVP-002 | 원문 0과 OUT_OF_SCOPE/FOLLOWUP/PRIVACY 행 0 unit 검증. actual insert/purge/FK와 PERSONAL/LEGAL 저장 의미는 Pending |
| ADMIN-001 | P0 | Frontend 팀원·Backend·Security | local/private 실패 질문 확인·사유 정정 | In Progress — route/service+fixture UI complete | LOG-001, Q-DB-004 | default 403, 목록/필터/상세/만료/role unit PASS. DB read capability와 actual composition은 Pending |
| ADMIN-002 | P0 | Frontend 팀원·Backend·PM·Security | KB 후보 작성·제출·별도 승인·반려·재작성 | In Progress — service+fixture UI complete | ADMIN-001, Q-DB-004 | PII recheck/self-approval/mock ACTIVE 차단·approve/reject unit/E2E PASS. actual OFFICIAL 20번째 ACTIVE는 Pending |
| REG-001 | P0 | 전체·QA | 침대 프레임 개선 전후 회귀 | Blocked | ADMIN-002 | 승인 전 폴백→승인 후 공식 출처 답변 완주 |

## Phase 4 — P1 품질·배포

| ID | 우선순위 | 담당 영역 | 작업 | 상태 | 의존성 | 완료 기준 |
|---|---|---|---|---|---|---|
| A11Y-001 | P1 | Frontend 팀원·QA | 쉬운 말·큰 글씨·대비·키보드 | In Progress — automated 390/430/desktop PASS | WEB-CHAT-001 | Playwright 12/12; final manual contrast/large-text/demo checklist Pending |
| QA-001 | P1 | QA·PM·AI/Data | 표본 20개 평가 리포트 | In Progress — 17/20 | REG-001, Q-MVP-002 | T-16~T-18 정책 결정과 actual regression 뒤 KPI 계산·실패 분석·수치 출처 표시 |
| PERF-001 | P1 | Backend·QA | 평균/p95·100명 제한 스모크 | Deferred after 2026-07-25 | API-CHAT-001 | Q-MVP-001에서 토요일 뒤로 명시적 연기 |
| ADMIN-QUALITY-001 | P1 | Frontend 팀원·Backend·QA·Security | 품질 카드·최소 감사 이력 | Blocked | ADMIN-002, QA-001 | EVENT/EVALUATION/MOCK 배지 항상 표시·비합산; action/actor/target/old-new status/changed fields와 질문·답변 snapshot 0 |
| DEMO-001 | P1 | PM·Platform·QA | local live→template fallback 데모 리허설 | Blocked | REG-001, PERF-001 | 인터넷/provider 장애에도 승인 KB 흐름 완주; 공개 URL·녹화는 별도 승인 항목 |
| BACKUP-001 | P1 | Platform·Backend·Security | local RPO/RTO·dump 보관·restore/purge drill | Deferred after 2026-07-25 | LOG-001 | 자동 백업은 Q-MVP-001에서 연기; 실제 데이터 전 수동 recovery 경계 유지 |
| DEPLOY-001 | P1 | Platform·Security·PM | 조건부 Vercel/Render/Supabase 공개 demo | Blocked | DEV-002, D-046의 deferred `00700` 구현·검증, 별도 공개 배포 승인 | privileged function/public port hardening 뒤 계정·리전·CORS·비밀·로그·비용·admin gate 승인 시에만 URL/health/rollback |
| HANDOFF-001 | P1 | 전체·Docs | local-first 인수인계·운영 런북 | Blocked | ADMIN-QUALITY-001, DEMO-001, BACKUP-001 | 신규 개발자 clean local 재현·backup/restore 성공; 단일 PC 위험과 public 배포 선택 조건 분리 |

## P2 — 명시적 범위 변경 전 백로그 미생성

GPS·지도·상태조회·내부 시스템 연계·다국어·음성·고급 분석·전체 KB CRUD·SSO/RBAC/전자결재는 로드맵에만 남기며 구현 TASK를 만들지 않는다.

## 변경 규칙

- 상태: `Ready`, `In Progress`, `Blocked`, `Review`, `Done`, `Dropped`.
- 작업을 시작할 때 실행계획/구현 노트 링크를 추가한다.
- P2는 사용자의 명시적 범위 변경 전 TASKS에 구현 작업으로 추가하지 않는다.
