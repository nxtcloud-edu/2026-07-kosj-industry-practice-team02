# Handoff — DB-001 Completed Local/Private Baseline

- Date: 2026-07-18 KST
- Branch/final-code evidence HEAD: `codex/db-001-layered-enforcement` /
  `73f300b9a90ad386ece555db3dc14fe1d18e6ba6`
- Current manifest: repo guidance `1.5.0`, database `0.3.0-local`, tests
  `0.5.0-db-baseline`, docs `2.4.0`
- Scope: disposable local/private PostgreSQL baseline; production/public readiness 아님

## 구현·검증된 범위

- source/runtime hash가 분리 고정된 patched project-local Supabase CLI `2.109.1`과
  PostgreSQL-only Docker local config; DB runner에는 stock/PATH fallback 없음
- timestamp forward migration 6개와 matching disposable-local compensation 6개
- `app_private` 7 enum·8 table, forced RLS/owner-only policy, backend capability role
- privacy/event/retention, 사유 확인, 후보 작성·제출·별도 승인/반려, ACTIVE+OFFICIAL read
- deferred ACTIVE-question validator의 제한된 `00600` posture correction
- lazy typed FastAPI DB boundary와 fixed SQL 9개; public route 연결 없음
- pgTAP 282, backend integration 8/8, exact 6-stage compensation/absence/reset/replay
- actual exact one `127.0.0.1:54322`, final project/all container 0/0, volume delete 0
- bounded child process-tree timeout/termination/disposal와 descendant cleanup regression; remediation
  independent review Critical/Important/Minor 0/0/0
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
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap_patched_supabase.ps1 -VerifyOnly
.\.tools\supabase\v2.109.1-sejong-loopback\supabase.exe --version
.\.tools\uv\uv.exe sync --project apps/api --frozen
corepack.cmd pnpm install --frozen-lockfile --ignore-scripts
```

patched binary가 없는 새 PC에서는 tracked source/runtime manifest를 권위로
`scripts/bootstrap_patched_supabase.ps1 -Install`을 실행하고 다시 `-VerifyOnly` 한다. build는 exact
upstream/tag/commit, Go archive, patch, 두 clean build의 동일 hash를 강제하므로 네트워크와 긴 시간이
필요하다. `.tools/`, `.env`, Supabase temp/branch state와 Docker state는 commit하지 않는다.

## 실행/테스트 명령

전체 DB gate는 start→reset→login rotation→pgTAP→6단계 compensation→absence→reset/replay→
pgTAP→backend integration 순서다.

아래 DB gate는 pinned patched runtime의 hash와 actual binding을 먼저 검증한 뒤에만 reset과
credential 처리를 진행한다. Q-SEC-004/005 전역 보정은 IPv6 wildcard를 남겼던 역사적 대조이고,
DB 실행 권위는 D-031/D-032의 patched-only 경로다.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify_database.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify_database.ps1 -SkipStart
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1
apps/api/.venv/Scripts/python.exe -B scripts/validate_codex_package.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/check_secret_patterns.ps1
git diff --check
```

`-SkipStart`도 actual runtime 검증을 우회하지 않는다. `-SkipRollbackReplay`는 진단용이며 완료
gate가 아니다. 2026-07-18 기준 actual single `127.0.0.1:54322`, current `Files=6, Tests=282`,
real integration 8/8, 6단계 replay, root/static gate가 fresh PASS했다. 상세는
[DB-001 report](../test-reports/DB-001-LOCAL-BASELINE.md)를 따른다.

`73f300b` remediation 뒤 final-code DB runner도 102.746s에 exit 0으로 통과했다. 두 inspect
payload는 다시 exact one loopback이었고 stop exit 0, final container 0/0, volume/prune 0이었다.
focused descendant 1/1, full runner 50/50, patched 24/24와 독립 review 0/0/0도 통과했다.

최종 verification에서는 patched `-VerifyOnly` 8.528s, root gate 866.976s, package/secret PASS,
combined tooling 74/74 (`24 + 50`), JSON/diff/protected+scripts PASS와 project/all container 0/0을
확인했다. 최종 evidence authority는 234-line `.superpowers/sdd/qsec006-task-5-db-evidence.md`,
SHA-256 `9EE2AC549A983921CC928892D803E46F713E311103928A25B5E47A901764DBFB`다. Final specification과
quality documentation review도 각각 APPROVED 0/0/0이다. 이 handoff/note를 포함하는 parent
closeout commit까지 완료됐으며 실제 SHA는 Git 이력을 권위로 확인한다.

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
.\.tools\supabase\v2.109.1-sejong-loopback\supabase.exe db reset --local
.\.tools\supabase\v2.109.1-sejong-loopback\supabase.exe test db
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
.\.tools\supabase\v2.109.1-sejong-loopback\supabase.exe stop
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
- Q-SEC-003 무응답 기본값 B: D-031 구현이 완료돼도 local/private 범위만 허용한다.
  remote/public 배포, public admin/API, public backend DB credential과 `00700`은 차단한다.
- local stack은 개발용 기본 credential을 포함하고 production TLS/rate limit/admin protection이
  없다. patched runtime의 fresh actual gate는 loopback-only였고 정상 stop 뒤 project/all container
  count 0/0이다. 이는 공개 exposure를 승인하지 않는다.
- 공식 seed 0, `/ready=503`, `/chat`·`/admin` public route 미구현이다.
- parent KB DELETE와 child question DELETE 동시 잠금 경로는 삭제 API가 없는 현재 P2 위험이다.
- pinned Starlette/httpx TestClient deprecation warning 1건은 non-failing이다.

## 인간이 알아야 하는 결정

- D-018/D-025/D-026/D-027/D-028/D-029/D-030/D-031/D-032와
  ADR-0008/0011/0012/0013/0014가 local DB 경계를 고정한다.
- remote/public DB, public admin, data deletion, official seed, backup, CORS/domain, 새 production
  dependency는 이 handoff로 승인되지 않는다.
- Q-SEC-003을 A로 결정하면 별도 reviewed `00700` property-only migration 계획과 전체 replay가
  필요하다. 현재는 B가 기본이며 인간 답변을 가장하지 않는다.
- Q-SEC-004=A/D-029와 Q-SEC-005=A/D-030은 불충분했다. Q-SEC-006=A/D-031과
  Q-TOOL-001=A/D-032는 checksum-pinned patched CLI/short workspace를 구현·검증해 local gate를
  닫았다. tracked source manifest hash는
  `c293e5ac32bae030eadf383d8d9511dc16eac834e51e996273ae8b7e39616657`, patch는
  `109c096480e8185d761e9ce8fba10e93efc55190c42eab978f769a6993833f7d`, runtime은
  `751068e73834c5da58ac7c5287a1d66a82ad356f508637b0478d6531cdb3941c`다. [Docker port publishing](https://docs.docker.com/engine/network/port-publishing/), [Docker Desktop settings](https://docs.docker.com/desktop/settings-and-maintenance/settings/)

## 다음 작업과 Acceptance Criteria

1. DATA-001: AI/Data·Backend가 공식 KB 20·기관 3+·매핑 10~12를 작성하고 PM이 출처·확인일·
   표현·origin·승인자를 2026-07-20 목표로 전수 승인한다.
2. DATA-SEED-001: 승인 data만 versioned seed로 import하고 ACTIVE 20, office 3+, mapping 10~12,
   mock 혼입 0, 재현 import/rollback을 증명한다.
3. READY-001: DB 연결과 필수 승인 seed가 모두 있을 때만 `/ready=200`, 결손/장애는 503으로
   유지한다.
4. Public release 전에 Q-SEC-003/A-021을 인간이 결정하고 보안 회귀·배포/credential/CORS/
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
