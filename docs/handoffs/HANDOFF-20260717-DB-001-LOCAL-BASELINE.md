# Handoff — DB-001 Local/Private Candidate (Blocked)

- Date: 2026-07-17 KST
- Branch/commit: `codex/db-001-layered-enforcement` / evidence baseline `85067d0`;
  Task 10 blocked and uncommitted
- Current manifest: repo guidance `1.4.0`, database `0.2.0-draft`, tests
  `0.4.2-readiness-contract`, docs `2.3.14`; `0.3.0-local`은 미승격 후보
- Scope: local PostgreSQL candidate; Q-SEC-005/A-023 해결 전 runtime 사용 금지

## 구현된 후보 범위

- pinned project-local Supabase CLI `2.109.1`과 PostgreSQL-only Docker local config
- timestamp forward migration 6개와 matching disposable-local compensation 6개
- `app_private` 7 enum·8 table, forced RLS/owner-only policy, backend capability role
- privacy/event/retention, 사유 확인, 후보 작성·제출·별도 승인/반려, ACTIVE+OFFICIAL read
- deferred ACTIVE-question validator의 제한된 `00600` posture correction
- lazy typed FastAPI DB boundary와 fixed SQL 9개; public route 연결 없음
- pgTAP 282, backend integration 8/8, exact 6-stage compensation/absence/reset/replay
- 공식/mock persistent seed 0; `/health=200`, `/ready=503`

## 요구 환경

- Windows PowerShell 5.1+
- Docker Desktop `4.62.0`, Docker Server `29.2.1`; runner minimum Engine 28
- repository-pinned Node `24.12.0`, pnpm `11.13.0`, Python `3.12.13`, uv `0.11.28`
- project-local Supabase CLI `2.109.1`; local PostgreSQL `17.6`
- 원격 Git repository는 없다. 현재 local repository/worktree 또는 승인된 로컬 복사본을 사용한다.

## Setup

저장소 루트에서 Docker Desktop을 실행한 뒤 다음을 수행한다.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap_supabase.ps1
.\.tools\supabase\v2.109.1\supabase.exe --version
.\.tools\uv\uv.exe sync --project apps/api --frozen
corepack.cmd pnpm install --frozen-lockfile --ignore-scripts
```

CLI bootstrap은 official asset byte count와 SHA-256을 확인해 `.tools/`에만 설치한다. `.tools/`,
`.env`, Supabase temp/branch state와 Docker state는 commit하지 않는다. 이 Setup은 도구 준비만
설명하며 Q-SEC-005 해결 전 DB container start/reset 권한을 주지 않는다.

## 실행/테스트 명령

전체 DB gate는 start→reset→login rotation→pgTAP→6단계 compensation→absence→reset/replay→
pgTAP→backend integration 순서다.

현재는 아래 DB 명령을 실행하지 않는다. Q-SEC-004=A의 1차 전역 binding 변경은 IPv6 wildcard를
남겼다. Q-SEC-005에서 더 강한 전역 정책을 인간이 승인하고 Docker restart/recreate와 probe를
마친 뒤에만 runner를 재실행한다.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify_database.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify_database.ps1 -SkipStart
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1
apps/api/.venv/Scripts/python.exe -B scripts/validate_codex_package.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/check_secret_patterns.ps1
git diff --check
```

`-SkipStart`도 actual runtime 검증을 우회하지 않는다. `-SkipRollbackReplay`는 진단용이며 완료
gate가 아니다. 성공 기준은 actual single `127.0.0.1:54322` 뒤 [DB-001 report](../test-reports/DB-001-LOCAL-BASELINE.md)의
historical `Files=6, Tests=282`, real integration 8/8을 fresh 재검증하고 synthetic tooling/root/static
gate와 independent review까지 모두 통과하는 것이다.

API를 수동 실행할 때는 다음을 사용한다.

```powershell
.\.tools\uv\uv.exe run --directory apps/api --frozen uvicorn sejong_ai_api.main:app `
  --app-dir src --host 127.0.0.1 --port 8000 --no-access-log --ws none
```

## 환경변수 이름(값 제외)

DB-001 관련 process/local env 이름은 다음뿐이다.

- `DATABASE_URL` — ignored `apps/api/.env`; DB gate가 local login password와 함께 회전
- `SEJONG_ADMIN_DATABASE_URL` — provisioning/compensation의 process-only local admin DSN
- `SEJONG_DB_TEST_URL` — real backend integration의 process-only local backend DSN

API 전체 예제 이름은 `apps/api/.env.example`을 따른다. 특히 `DEEPSEEK_ENABLED`,
`DEEPSEEK_SYNTHETIC_EVALUATION_MODE`, `LLM_API_KEY`, `CONTEXT_TOKEN_SECRET` 줄은 provisioning이
`.env` 전체 bytes를 읽어 원자 갱신할 때 byte-identical하게 보존한다. 해당 non-target 값은
파싱·표시·로그·별도 영구 복사하지 않으며 어떤 값도 terminal, 문서, Git에 붙여 넣지 않는다.

## DB migrate/seed/rollback

### Migrate/replay

실행 권위는 `supabase/migrations/` timestamp 순서다. empty local replay는 다음 명령이며
현재 local data를 재생성하므로 disposable DB에서만 실행한다.

```powershell
.\.tools\supabase\v2.109.1\supabase.exe db reset --local
.\.tools\supabase\v2.109.1\supabase.exe test db
```

### Seed

`supabase/seed.sql`은 data-free 주석만 있다. DATA-001의 PM 승인 목표는 2026-07-20이고,
DATA-SEED-001은 그 승인 전 시작하지 않는다. 공식/mock persistent row는 0이며 DB migration
성공만으로 `/ready=200`으로 바꾸지 않는다.

### Rollback/compensation

관리자 DSN을 값이 보이지 않는 process environment로 주입한 상태에서만 다음을 실행한다.

```powershell
apps/api/.venv/Scripts/python.exe -B scripts/run_database_sql.py `
  database/rollbacks/20260717000600_deferred_active_question_trigger_security.rollback.sql `
  database/rollbacks/20260716000500_indexes_and_read_interfaces.rollback.sql `
  database/rollbacks/20260716000400_candidate_workflow.rollback.sql `
  database/rollbacks/20260716000300_capabilities_and_functions.rollback.sql `
  database/rollbacks/20260716000200_invariants_and_lineage.rollback.sql `
  database/rollbacks/20260716000100_private_schema.rollback.sql `
  database/verify_db001_absent.sql
```

이 보상은 disposable local DB 전용이다. remote project, 실제 데이터 DB, production backup,
Docker volume에 적용하지 않는다. 이미 공유된 migration을 수정하지 말고 새 reviewed forward
migration으로 보정한다.

## Stop/recovery

정상 local stop:

```powershell
.\.tools\supabase\v2.109.1\supabase.exe stop
```

Docker volume 삭제·prune은 하지 않는다. provisioning이 DB password commit 뒤 `.env` 교체에서
실패하면 기존 env bytes는 보존되므로 원인을 고친 뒤 provisioning 또는 전체 DB gate를 다시
실행해 password를 재회전한다. login만 회전할 때는 process-only admin DSN을 준비한 뒤:

```powershell
apps/api/.venv/Scripts/python.exe -B scripts/provision_local_database_login.py
```

local schema 복구의 1차 경로는 `db reset --local` replay다. 향후 dump restore는 BACKUP-001의
승인을 받고, 서비스 개방 전 `masked_question` retention purge를 재실행한다. 현재 off-device
backup은 없고 단일 PC 손실 위험이 남는다.

## 알려진 문제와 위험

- A-021/Q-SEC-003 미해결: privileged execution graph 22개 중 `00600` validator만 exact
  `pg_catalog, pg_temp`; 나머지 21개는 public hardening 전이다.
- Q-SEC-003 무응답 기본값 B: A-023이 별도로 해결된 경우에도 local/private 범위만 허용한다.
  remote/public 배포, public admin/API, public backend DB credential과 `00700`은 차단한다.
- local stack은 개발용 기본 credential을 포함하고 production TLS/rate limit/admin protection이
  없다. 현재 stock CLI runtime은 wildcard로 판정됐고 runner가 reset 전에 중단했다. stack은
  중지했으며 project container count 0이다.
- 공식 seed 0, `/ready=503`, `/chat`·`/admin` public route 미구현이다.
- parent KB DELETE와 child question DELETE 동시 잠금 경로는 삭제 API가 없는 현재 P2 위험이다.
- pinned Starlette/httpx TestClient deprecation warning 1건은 non-failing이다.

## 인간이 알아야 하는 결정

- D-018/D-025/D-026/D-027/D-028과 ADR-0008/0011/0012가 local DB 경계를 고정한다.
- remote/public DB, public admin, data deletion, official seed, backup, CORS/domain, 새 production
  dependency는 이 handoff로 승인되지 않는다.
- Q-SEC-003을 A로 결정하면 별도 reviewed `00700` property-only migration 계획과 전체 replay가
  필요하다. 현재는 B가 기본이며 인간 답변을 가장하지 않는다.
- Q-SEC-004=A/D-029는 적용됐지만 HostIP 미지정 probe가 `127.0.0.1`+`::`를 생성해 불충분했다.
  Q-SEC-005/A-023은 더 강한 `local-only-port-binding` 전역 정책과 patched CLI/보류 사이의
  인간 결정이다. [Docker port publishing](https://docs.docker.com/engine/network/port-publishing/), [Docker Desktop settings](https://docs.docker.com/desktop/settings-and-maintenance/settings/)

## 다음 작업과 Acceptance Criteria

1. Q-SEC-005: 인간 결정과 safe Docker restart/recreate/exact runtime/full gate.
2. Q-SEC-005의 safe runtime/full gate와 independent reviews가 모두 통과한 뒤에만 DB-001을
   `0.3.0-local`/Done으로 승격하고 후속 DB 의존성을 해제한다.
3. DATA-001: AI/Data·Backend가 공식 KB 20·기관 3+·매핑 10~12를 작성하고 PM이 출처·확인일·
   표현·origin·승인자를 2026-07-20 목표로 전수 승인한다.
4. DATA-SEED-001: 승인 data만 versioned seed로 import하고 ACTIVE 20, office 3+, mapping 10~12,
   mock 혼입 0, 재현 import/rollback을 증명한다.
5. READY-001: DB 연결과 필수 승인 seed가 모두 있을 때만 `/ready=200`, 결손/장애는 503으로
   유지한다.
6. Public release 전에 Q-SEC-003/A-021을 인간이 결정하고 보안 회귀·배포/credential/CORS/
   backup gate를 별도로 승인한다.

## 최근 구현 노트/ADR/계획 링크

- [Main DB-001 implementation note](../implementation-notes/IMP-20260716-006-db-001-layered-enforcement.md)
- [Task 9 blocker and closeout](../implementation-notes/IMP-20260717-004-db-001-task-9-deferred-trigger-permission-blocker.md)
- [Q-DB-003 remediation](../implementation-notes/IMP-20260717-005-q-db-003-a-decision-and-deferred-trigger-remediation-plan.md)
- [A-021 audit](../implementation-notes/IMP-20260717-006-a-021-privileged-function-search-path-security-audit.md)
- [ADR-0008](../adr/0008-supabase-cli-sql-migrations.md), [ADR-0011](../adr/0011-layered-database-and-backend-enforcement.md), [ADR-0012](../adr/0012-deferred-active-question-trigger-execution.md)
- [DB-001 plan](../superpowers/plans/2026-07-16-db-001-layered-enforcement.md),
  [Task 9A plan](../superpowers/plans/2026-07-17-db-001-deferred-trigger-security-fix.md)
- [Version manifest](../../versions/manifest.json), [local report](../test-reports/DB-001-LOCAL-BASELINE.md)
