# 모호성·미지의 영역 레지스터

Codex는 초기 감사에서 이 목록을 검증하고 추가/해결한다. 이미 결정된 것은 재질문하지 않는다.

| ID | 우선도 | 영역 | 현재 상태 | 질문/결정 | 기본 추천 |
|---|---|---|---|---|---|
| A-001 | A | LLM | Resolved | `deepseek-v4-flash`, thinking off, max 1024, concurrency 1, retry 1, run당 외부 전송 시도 30회; 합성 전용 | Q-LLM-004 / D-023 / ADR-0005 |
| A-002 | A | 개발환경 | Resolved | Node 24.x+pnpm, Python 3.12+uv; exact patch는 스캐폴딩에서 고정 | Q-DEV-001 / D-010 |
| A-003 | A | DB/배포 | Resolved for local; public deferred | Supabase CLI 버전 SQL migration과 Docker local stack 사용. 공개 DB·원격 push는 별도 승인 | Q-DB-001 / ADR-0008; 설치는 계획 승인 후 |
| A-004 | A | Admin 보안 | Resolved | local/private 전용, 공개 시 서버측 gate 없이는 관리자 경로 비활성 | Q-SEC-001 / ADR-0007 |
| A-005 | A | 데이터 | Resolved | AI/Data·Backend 작성, PM 승인, 2026-07-20 목표 | Q-DATA-001 / D-011 |
| A-006 | B | 마스킹 | Resolved with review gate | 이름·상세주소는 재현율 우선 보수적 감지. 과잉 마스킹이 성공률 80% 미달 원인으로 입증돼도 B 전환은 재승인 | Q-PRIV-002 / ADR-0004 |
| A-007 | B | 검색 | Defaulted / Deferred | MVP는 keyword/metadata만 사용하고 embedding flag는 off | ADR-0006; 품질 근거와 비용 승인 전 활성화 금지 |
| A-008 | B | CI | Resolved for current phase; deferred | local Git+수동 검증 gate. 원격/CI는 사용자가 다시 요청할 때 결정 | Q-CI-001 / D-021 |
| A-009 | B | 데모 | Defaulted / Deferred | 현재 완료 기준은 local live demo+재시작 runbook. 공개 URL·녹화본은 별도 발표/배포 승인 시 선택 | D-013/D-021 범위의 0원·local-first 기본값 |
| A-010 | C | UI | Defaultable | 디자인 시스템 세부 | 기존 아이디어노트 톤, 접근성 우선 |
| A-011 | C | 코드 | Defaultable | 모듈 명명·파일 분할 | framework conventions |
| A-012 | A | 저장소 | Resolved | 원본 원격 없음; 독립 Git repo와 `main` 사용 | Q-REPO-001 / D-009; init은 계획 승인 후 |
| A-013 | A | 개인정보 | Resolved | 30일 후 masked text만 파기, 행·비텍스트 메타·후보 FK 유지 | Q-PRIV-001 / ADR-0004 |
| A-014 | A | 대화 | Resolved | 현재 탭 메모리 transcript + 15분 서명형 client-carried context token; 서버 세션·raw transcript 없음 | Q-CHAT-001 / D-024 / ADR-0010 |
| A-015 | B | 오류 계약 | Resolved | 정책 응답은 200, 안전 대체가 없는 기술 장애는 503 `SERVICE_UNAVAILABLE` envelope | Q-API-001 / ADR-0009 |
| A-016 | B | 복구 | Defaulted for disposable local demo; public deferred | 재현 가능한 migration+승인 seed 우선, 파괴 변경/마일스톤 전 gitignored 수동 dump, local RPO 24h/RTO 60m, 30일 넘은 dump 삭제, 복구 후 개방 전 retention 재실행 | 실제/비재현 데이터·공개 운영 전 인간 재승인 |
| A-017 | B | DB 안전 경계 | Resolved | Q-DB-002: DB function/trigger/RLS/GRANT + 백엔드 이중 검증 | 2026-07-16 사용자 A 승인 / D-025 / ADR-0011 |
| A-018 | A | DB role 보안 | Resolved | Q-SEC-002=A: non-superuser PG17 runner 유지, 허용된 role 속성 재적용+catalog 검증, unsafe role fail closed | D-026 / ADR-0011; privileged auto-downgrade/bootstrap 없음 |
| A-019 | A | 관리자 workflow | Resolved | Q-WF-001=A: 별도 backend-only `confirm_failed_question_reason(uuid,text,text,text)` capability | D-027 / ADR-0011; event 자동 사유 불변, failure 사유·적격성 재계산 |
| A-020 | A | DB trigger 권한 | Resolved | Q-DB-003=A: 새 `00600`에서 ACTIVE-question validator 하나만 SECURITY DEFINER+owner/`search_path=pg_catalog, pg_temp`/revoke 검증, compensation은 INVOKER | D-028 / ADR-0012; 사용자의 직전 추천안 뒤 계속 진행 지시를 A 승인으로 해석, 문자 A 직접 입력 아님; `pg_temp` 마지막 명시는 D/Internal 보안 보정 |
| A-021 | B | 기존 DB function 보안 | Open / Deferred — local Task 9 blocker 아님, public release blocker | read-only audit의 privileged execution graph는 `app_api` SECURITY DEFINER 9개+중첩/trigger `app_private` 13개=22개다. `00600` validator만 교정돼 unsafe `pg_catalog`-only path는 21개다. application relation/helper는 qualified이고 dynamic SQL은 0이다. data-type shadow DoS는 high-confidence plausible, privilege escalation은 conservative medium-confidence inference이며 exploit은 재현하지 않았다. | Q-SEC-003 A 추천: exact 22 signatures에 새 `00700` property-only migration. B/default: local-only 완료는 허용하되 remote/public 배포·public admin/API·public backend DB credential은 해결 전 차단 |
| A-022 | A | local Docker port 보안 1차 결정 | Resolved decision / remediation insufficient | Q-SEC-004=A로 Docker Desktop `PortBindingBehavior=default-local-port-binding`을 적용·재시작했다. 빈 HostIP probe는 IPv4 `127.0.0.1`과 IPv6 wildcard `::`를 함께 만들었고 explicit `127.0.0.1` probe만 단일 loopback이었다. | D-029; 승인 결정은 기록하되 exact local 완료 근거로 사용하지 않음 |
| A-023 | A | local Docker IPv6 port 보안 2차 결정 | Resolved decision / remediation insufficient | Q-SEC-005=A로 `local-only-port-binding`을 적용·재시작했지만 HostIP 생략 probe는 다시 `127.0.0.1`+`::`였다. explicit `127.0.0.1` control만 단일 loopback이었다. | D-030; 승인 설정은 유지하지만 exact local 완료 근거로 사용하지 않음 |
| A-024 | A | local Supabase CLI port 공급망 | Resolved decision / implementation in progress | Q-SEC-006=A. official v2.109.1 exact source의 local DB start HostIP만 `127.0.0.1`로 지정하는 project-local patched CLI를 source/tag/commit·patch·Go 1.25.11·binary SHA-256과 함께 pin한다. 서면 명세와 실행계획은 승인됐다. | D-031 / ADR-0013; 구현·검증 전 DB runtime/manifest 승격 차단 |
| A-025 | A | Windows patched CLI build workspace | Resolved decision / revised plan awaiting approval | 사용자가 2026-07-18 Q-TOOL-001=A를 명시했다. 두 checkout만 `.tools/s/{a,b}`로 줄이고 pinned relative max 134자·absolute cap 248자를 pre-checkout gate로 강제한다. 기존 장경로 partial artifact는 자동 삭제하지 않는다. | D-032 / ADR-0014; Task 2C TDD·독립 review와 수정 계획 승인 전 Task 3/DB-001 중단 |

## 우선도 정의

- A: 구현 전 인간 결정 필요
- B: 빠른 인간 결정이 유리
- C: AI 기본값 가능, 기록 필요
- D: 내부 구현 판단

현재 인간 결정형 A/Blocker는 없다. Q-SEC-002와 Q-WF-001은 2026-07-16에
해결됐고, Q-DB-003은 D-028/ADR-0012, Q-SEC-004는 D-029, Q-SEC-005는 D-030으로 2026-07-17에 해결됐다. Task 9의 역사적 RED는
real DB 6 pass/2 approval fail이었고 `00600` 구현 뒤 full pgTAP 282, integration 8/8,
6단계 replay와 독립 review가 완료됐다. 그러나 Task 10 quality review에서 실제 host wildcard
publish가 발견됐고 승인된 두 Docker Desktop 보정도 IPv6 wildcard를 남겼으므로 DB-001은
`0.3.0-local` 후보를 아직 승격하지 않는다. A-024는 D-031/ADR-0013으로 결정되고 서면
명세도 승인됐지만 Task 1/2/2A/2B 뒤 실제 Task 3 재실행에서 PowerShell 5.1 장경로 cleanup이
부분 실패했다. A-025는 Q-TOOL-001=A/D-032/ADR-0014로 해결됐고 수정 계획 승인과 Task 2C
TDD·독립 review·실제 검증 gate가 남아 local 완료는 계속 차단된다. A-021은 B/High
public-release blocker다.

## 열린 인터뷰 질문

Q-SEC-003. 기존 privileged function 22개의 search path를 public release 전에 어떻게 보정할 것인가
- 왜 지금 필요한가: local/private Task 9 완료에는 영향이 없지만 PostgreSQL 17 공식 지침과 22-function read-only audit상 `00600` 뒤에도 21개가 `search_path=pg_catalog` 단독이다. remote/public 배포, public admin/API 활성화, public backend DB credential 사용 전에는 인간이 보안 경계를 승인해야 한다.
- 선택지 A / 장점 / 단점: 새 versioned `00700` property-only migration에서 exact 22 signatures의 `search_path`를 `pg_catalog, pg_temp`로 재설정하고 catalog/behavior/compensation을 검증한다 / 함수 본문·API·table/data를 바꾸지 않고 일관된 방어를 제공하지만 새 migration과 전체 회귀가 필요하다.
- 선택지 B / 장점 / 단점: 현재 posture를 유지하고 local/private demo만 완료한다 / 즉시 추가 migration이 없지만 remote/public 배포·public admin/API·public backend DB credential을 계속 차단해야 한다.
- 당신의 추천안: A. exact signature allowlist, property-only forward migration, matching compensation, no body rewrite/grant/data change로 제한한다.
- 답을 받지 못할 때 사용할 기본값: B. local-only 완료는 허용하고 public release 관련 경로는 차단한다. `00700`은 구현하지 않는다.
- 영향을 받는 파일·계약·데이터·배포: 새 `00700`/compensation/pgTAP·통합 회귀와 DB 보안 문서가 영향받는다. 공개 API/table/data/retention/dependency/cost는 변하지 않지만 remote/public release gate가 직접 영향받는다.

## 해결된 인터뷰 질문

Q-TOOL-001. Windows에서 patched CLI의 재현 build checkout을 어떤 방식으로 안전하게 관리할 것인가
- 결정: A / D-032 / ADR-0014. 사용자가 2026-07-18 `Q-TOOL-001: A`라고 명시했다.
- 선택: checkout만 `.tools/s/a`, `.tools/s/b`로 줄인다. source manifest에 `s/a`, `s/b`, pinned
  relative max 134자, absolute cap 248자를 고정하고 checkout cleanup·생성·Go archive
  download/extraction·network 전에 projected path를 검증한다. 현재 exact worktree 투영값은 244자다.
- 영향: 기존 PowerShell 5.1 safe-child/reparse cleanup과 exact source/toolchain/patch/hash 공급망을
  유지한다. 기존 ignored `.tools/supabase-source/...` partial tree는 자동 삭제하지 않는다. 수정
  계획 승인·Task 2C TDD/review 전 Task 3은 재개하지 않으며 API·DB schema/data·privacy·dependency·deployment는 변하지 않는다.

Q-SEC-006. stock Supabase CLI의 DB publish 요청을 project-scoped explicit IPv4 loopback으로 바꿀 것인가
- 결정: A / D-031 / ADR-0013. 사용자가 2026-07-17 `Q-SEC-006: A`라고 명시했다.
- 선택: official v2.109.1 exact source에서 local DB start HostIP만 `127.0.0.1`로 지정하고 source/tag/commit, patch, Go 1.25.11 archive, clean-build binary SHA-256을 project-local manifest로 pin한다.
- 영향: exact port gate와 stock CLI를 유지한다. 서면 설계는 승인됐으며 별도 실행계획 승인, TDD/build/actual full gate 전에는 DB runtime·schema version 승격을 시작하거나 완료로 부르지 않는다. 공개 API·migration·data·production dependency는 변하지 않는다.

Q-SEC-005. Docker Desktop의 모든 새 port publish를 loopback으로 강제하는 더 강한 전역 정책을 승인할 것인가
- 결정: A / D-030. 사용자가 2026-07-17 `Q-SEC-005: A`라고 명시했다.
- 적용 결과: `PortBindingBehavior=local-only-port-binding`을 저장하고 Docker Desktop을 재시작했다. HostIP 생략 probe는 다시 `127.0.0.1`과 `::` 두 binding이었고 explicit `127.0.0.1` control은 단일 loopback이었다. 두 probe를 제거했고 Supabase DB start/reset/status/credential/SQL은 실행하지 않았다.
- 영향: 승인된 설정은 유지하지만 DB-001 완료 근거로 사용하지 않는다. A-024/Q-SEC-006이 후속 local 완료 blocker다.

Q-SEC-004. Docker Desktop의 향후 모든 새 container 기본 port binding을 loopback으로 바꿀 것인가
- 결정: A / D-029. 사용자가 2026-07-17 `ㅇㅇ 승인할게. 계속 ㄱㄱ`라고 명시했다.
- 적용 결과: `PortBindingBehavior=default-local-port-binding`을 저장하고 Docker Desktop을 완전 재시작했다. 빈 HostIP probe의 실제 결과는 `127.0.0.1`과 `::` 두 binding이어서 exact local 기준에는 실패했다. explicit `127.0.0.1` probe는 단일 loopback이었다. 두 probe는 제거했고 DB reset/status/credential 처리는 실행하지 않았다.
- 영향: 승인된 설정은 유지하지만 DB-001 완료 근거로 사용하지 않는다. 당시 A-023/Q-SEC-005로 이관했고, 그 보정도 실패해 현재 blocker는 A-024/Q-SEC-006이다.

Q-DB-003. backend 승인 commit에서 deferred ACTIVE-question trigger를 어떤 권한으로 실행할 것인가
- 결정: A / D-028 / ADR-0012. 사용자는 문자 `A`를 직접 입력하지 않았고, 직전 추천안 뒤 `이거 끝나면 계속해서 진행해줘. 5시간 동안 루프 ㄱㄱ`라고 지시했다. 이를 추천안 A의 실행 승인으로 투명하게 해석했다.
- 왜 지금 필요한가: 승인 함수는 최소권한 SECURITY DEFINER지만 commit 시 실행되는 `app_private.validate_active_kb_question()`은 SECURITY INVOKER다. private schema 접근권한이 없는 backend 호출에서는 두 승인 통합 테스트가 실패하므로, Task 9·DB-001 완료 전에 migration 보안 경계를 인간이 결정해야 한다.
- 선택지 A / 장점 / 단점: 새 versioned `006` migration에서 이 trigger validator만 SECURITY DEFINER로 바꾸고 기존 `sejong_schema_owner`, `search_path=pg_catalog, pg_temp`(임시 스키마 마지막), 직접 EXECUTE revoke를 catalog·pgTAP으로 검증한다. 기존 deferred invariant와 원자 transaction을 보존하고 권한 상승을 함수 하나로 제한한다 / 새 migration·matching compensation·보안 회귀 테스트가 필요하다.
- 선택지 B / 장점 / 단점: `approve_kb_candidate` 안에서 관련 named constraint를 `SET CONSTRAINTS`의 IMMEDIATE mode로 실행한다. trigger 자체의 definer 표면은 늘리지 않는다 / 승인 함수가 constraint 이름과 transaction constraint mode에 결합되고 호출자 transaction 동작에 영향을 줄 수 있어 더 복잡하다.
- 당신의 추천안: A. 최소 함수 하나만 제한적으로 SECURITY DEFINER로 만들고 owner·고정 search path·revoke·동시성·원자 rollback을 모두 검증한다.
- 답을 받지 못할 때 사용할 기본값: 역사적 기본값은 DB-001 Blocked 유지였다. 현재는 A가 승인됐으며 backend에 private schema/table grant를 주거나 repository/admin-DSN 우회, 기존 migration 수정은 여전히 하지 않는다.
- 영향을 받는 파일·계약·데이터·배포: 새 `006` forward migration과 matching compensation, pgTAP·Task 9 통합 gate, DB schema/test version이 영향을 받는다. 공개 API·공식/mock 데이터·dependency·remote/public 배포는 변하지 않는다.

## 질문 규칙

- 한 번에 7개 이하
- 옵션/장단점/추천/기본값/영향 포함
- 답변 후 결정 로그·ADR·계획·버전 갱신
