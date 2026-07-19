# TASKS.md — 현재 백로그

> 이 문서는 우선순위와 의존성을 보여주는 작업 인덱스다. 실제 작업을 시작하면 실행계획과 구현 노트를 연결한다.

## Phase 0 — 발견·결정·정리

| ID | 우선순위 | 담당 영역 | 작업 | 상태 | 의존성 | 완료 기준 |
|---|---|---|---|---|---|---|
| DISC-001 | P0 | Architecture·Security·Data·Docs | [저장소 감사와 최종 기준 드리프트 보고서](docs/discovery/INITIAL_DISCOVERY_REPORT.md) | Done | 없음 | 코드/문서/데이터/계약 충돌표와 [IMP-20260714-001](docs/implementation-notes/IMP-20260714-001-초기-저장소-발견-감사.md) 작성 |
| DISC-002 | P0 | Architecture·Product·Security | 아키텍처 영향 인터뷰 | Done | DISC-001 | batch 1~3 기록, 인간 결정형 A/Blocker 0 |
| DOC-001 | P0 | Architecture·Docs | 결정 로그·ADR·모호성·계약·DB draft 동기화 | Done | DISC-002 | D-009~024, ADR-0002~0010, OpenAPI 2.0.1-draft와 source-of-truth 정합성 검사 통과 |
| PLAN-001 | P0 | Architecture·전체 | [local-first 기반과 승인형 민원 안내 실행계획](docs/plans/PLAN-20260714-001-foundation-and-governed-chat.md) | Done | DISC-002, DOC-001 | 2026-07-15 사용자 `진행` 승인; 공개/실제 시민 경계는 별도 승인 유지 |

## Phase 1 — 프로젝트 스캐폴딩

| ID | 우선순위 | 담당 영역 | 작업 | 상태 | 의존성 | 완료 기준 |
|---|---|---|---|---|---|---|
| DEV-001 | P0 | Platform·FE·BE | 독립 Git·Node 24/pnpm·Python 3.12/uv 모노레포와 health | Done | PLAN-001 Approved | corrected fresh default·warm-offline 24/24와 actual API/Web smoke, final P0/P1/P2 0; DB·승인 seed 전 `/ready=503` 유지 |
| DEV-002 | P0 | Platform·Security | 환경변수·비밀관리·local 수동 검증 gate | Done | DEV-001 | 예제 환경, 비밀 스캔, raw body logging off, synthetic/offline env 복원과 clean gate 통과 |
| DB-001 | P0 | Backend·Data·Security | [Supabase SQL v1 migration·보상 rollback·권한](docs/discovery/DB_001_DISCOVERY_REPORT.md) | Done | DEV-001 Done, approved [DB spec](docs/superpowers/specs/2026-07-16-db-001-layered-enforcement-design.md)·[parent plan](docs/superpowers/plans/2026-07-16-db-001-layered-enforcement.md), D-026~D-032, ADR-0012/0013/0014, [patched plan](docs/superpowers/plans/2026-07-17-q-sec-006-patched-supabase-cli.md), [verified report](docs/test-reports/DB-001-LOCAL-BASELINE.md), [handoff](docs/handoffs/HANDOFF-20260717-DB-001-LOCAL-BASELINE.md), [Draft closeout note](docs/implementation-notes/IMP-20260718-004-patched-supabase-cli와-db-001-local-baseline-완료.md); A-021/Q-SEC-003 separately blocks public release | disposable local/private baseline만 검증, production-ready 아님. pinned source/patch/runtime hashes, patched-only runner, bounded child process trees, exact one `127.0.0.1:54322`, pgTAP 282·integration 8/8·6단계 replay; 공식 seed 0·`/ready=503`; public/remote 금지 |
| CONTRACT-001 | P0 | FE·BE·QA | OpenAPI 2.0·공유 타입 생성 경로와 200/503·context 계약 | Done | DEV-001 | API 2.0.1-draft의 `/health`·ready-state `/ready` 200과 FALLBACK까지 fixture·생성 TypeScript·strict Pydantic drift 0, final P0/P1/P2 0 |

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
| DATA-SEED-001 | P0 | Backend·Data·Security | 승인 record의 immutable official release·버전 seed·lineage | In Progress | DATA-001 approved manifest, approved [Q-SEED-001 design](docs/superpowers/specs/2026-07-19-data-seed-immutable-release-design.md), approved [execution plan](docs/superpowers/plans/2026-07-19-data-seed-immutable-release-and-local-verification.md) | D-036/D-038/D-039/ADR-0016. `0.1.0-initial.1` 19/3/10, 기존 schema transactional seed, empty disposable compensation; task별 TDD·독립 review·actual DB cycle 진행, [IMP-20260719-008](docs/implementation-notes/IMP-20260719-008-data-seed-001-불변-공식-release와-local-seed-검증.md) |
| READY-001 | P0 | Backend·Data·Platform | 실제 DB·필수 승인 seed readiness probe 전환 | Blocked | DATA-SEED-001, DEV-001B | DB 연결과 필수 ACTIVE KB/기관 seed가 모두 준비될 때만 `/ready=200`; 결손/장애는 503 |
| AI-001 | P0 | AI/Data·Backend·Security | 보수적 PII 마스킹과 분류·검색·근거 gate·template 응답 | Blocked | DATA-SEED-001 | 표본 단위 테스트, provider payload/DB/log 원문 0, ACTIVE 전용 검색, PII 100%·성공률 동시 측정 |
| LLM-001 | P0 | AI/Data·Backend·Security | DeepSeek 합성 fixture adapter와 장애 fallback | Blocked | AI-001, PLAN-001 Approved | exact Flash/thinking off/max1024, hidden retry 0, retry≤1, concurrency 1, run attempt 28/29/30 경계, allowlist·schema/empty/429/timeout·template fallback |
| API-CHAT-001 | P0 | Backend·QA | `/api/v1/chat`·signed context와 공통 오류 계약 | Blocked | CONTRACT-001, AI-001, LLM-001 | SUCCESS/FOLLOWUP/FALLBACK 200, 안전 대체 없는 503, 900초 token/tamper reset/current request 우선/source 결합·token persistence 0 |
| WEB-HOME-001 | P0 | Frontend·QA | `/` 서비스 소개·4개 지원 분야·한계·`/chat` 진입 | Done | DEV-001 complete; Q-WEB-001=A/D-037; [execution plan](docs/superpowers/plans/2026-07-19-web-home-and-static-chat-shell.md) | 정적 `/chat`·home CTA, 입력/저장/외부 요청 0, 390/430/desktop·키보드·focus·contrast·실제 Chrome UI 200%·prod dependency gate PASS, [IMP-20260719-005](docs/implementation-notes/IMP-20260719-005-web-home과-정적-채팅-준비-화면.md) |
| WEB-CHAT-001 | P0 | Frontend·QA | `/chat` current-tab 대화·카드·출처·폴백·기관 | Blocked | API-CHAT-001, WEB-HOME-001 | 390/430px, 키보드·포커스·대비, 중복 전송·503 재시도·empty office, 새로고침 소멸·browser storage/token log 0 |

## Phase 3 — 관리자 개선 루프

| ID | 우선순위 | 담당 영역 | 작업 | 상태 | 의존성 | 완료 기준 |
|---|---|---|---|---|---|---|
| LOG-001 | P0 | Backend·Security·Data | 비식별 이벤트·실패 질문 저장과 30일 텍스트 파기 | Blocked | API-CHAT-001 | 원문 0, OUT_OF_SCOPE/FOLLOWUP 실패행 0, NULL purge·FK 보존·복구 테스트 |
| ADMIN-001 | P0 | FE·BE·Security | local/private 실패 질문 확인·사유 정정 | Blocked | LOG-001 | 목록/필터/상세/만료 빈 상태, public route 차단 |
| ADMIN-002 | P0 | FE·BE·PM·Security | KB 후보 작성·제출·별도 승인·반려·재작성 | Blocked | ADMIN-001 | 작성자 자기 승인·PII 후보·미승인 ACTIVE 각각 0, 반려 comment와 재작성 경로 동작 |
| REG-001 | P0 | 전체·QA | 침대 프레임 개선 전후 회귀 | Blocked | ADMIN-002 | 승인 전 폴백→승인 후 공식 출처 답변 완주 |

## Phase 4 — P1 품질·배포

| ID | 우선순위 | 담당 영역 | 작업 | 상태 | 의존성 | 완료 기준 |
|---|---|---|---|---|---|---|
| A11Y-001 | P1 | Frontend·QA | 쉬운 말·큰 글씨·대비·키보드 | Blocked | WEB-CHAT-001 | 자동+수동 접근성 체크리스트 통과 |
| QA-001 | P1 | QA·PM·AI/Data | 표본 20개 평가 리포트 | Blocked | REG-001 | KPI 계산·실패 분석·수치 출처 표시 |
| PERF-001 | P1 | Backend·QA | 평균/p95·100명 제한 스모크 | Blocked | API-CHAT-001 | deterministic 경로 결과와 실제 LLM 한계 분리 기록 |
| ADMIN-QUALITY-001 | P1 | FE·BE·QA·Security | 품질 카드·최소 감사 이력 | Blocked | ADMIN-002, QA-001 | EVENT/EVALUATION/MOCK 배지 항상 표시·비합산; action/actor/target/old-new status/changed fields와 질문·답변 snapshot 0 |
| DEMO-001 | P1 | PM·Platform·QA | local live→template fallback 데모 리허설 | Blocked | REG-001, PERF-001 | 인터넷/provider 장애에도 승인 KB 흐름 완주; 공개 URL·녹화는 별도 승인 항목 |
| BACKUP-001 | P1 | Platform·Backend·Security | local RPO/RTO·dump 보관·restore/purge drill | Blocked | LOG-001 | RPO24h/RTO60m, daily/pre-risk gitignored dump, 30일 삭제, restore 후 service-open 전 purge 1회 |
| DEPLOY-001 | P1 | Platform·Security·PM | 조건부 Vercel/Render/Supabase 공개 demo | Blocked | DEV-002, A-021/Q-SEC-003 해결, 별도 공개 배포 승인 | privileged function/public port hardening 뒤 계정·리전·CORS·비밀·로그·비용·admin gate 승인 시에만 URL/health/rollback |
| HANDOFF-001 | P1 | 전체·Docs | local-first 인수인계·운영 런북 | Blocked | ADMIN-QUALITY-001, DEMO-001, BACKUP-001 | 신규 개발자 clean local 재현·backup/restore 성공; 단일 PC 위험과 public 배포 선택 조건 분리 |

## P2 — 명시적 범위 변경 전 백로그 미생성

GPS·지도·상태조회·내부 시스템 연계·다국어·음성·고급 분석·전체 KB CRUD·SSO/RBAC/전자결재는 로드맵에만 남기며 구현 TASK를 만들지 않는다.

## 변경 규칙

- 상태: `Ready`, `In Progress`, `Blocked`, `Review`, `Done`, `Dropped`.
- 작업을 시작할 때 실행계획/구현 노트 링크를 추가한다.
- P2는 사용자의 명시적 범위 변경 전 TASKS에 구현 작업으로 추가하지 않는다.
