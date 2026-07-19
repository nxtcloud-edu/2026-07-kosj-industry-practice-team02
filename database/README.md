# Database

DB-001의 manifest 의미 버전은 disposable local/private `0.3.0-local`이다. pinned patched
Supabase CLI의 exact single `127.0.0.1:54322`, pgTAP 282, backend integration 8/8,
6단계 compensation/reset/replay와 final review를 통과했다. 이는 production/public readiness를
뜻하지 않는다.
A-021/Q-SEC-003이 해결되기 전에는 remote/public 배포, public admin/API, public backend DB
credential 사용이 금지된다. 답변이 없을 때의 현재 기본값은 Q-SEC-003 선택지 B이며
`00700` migration은 만들지 않는다.

## 권위와 계보

- 실행 권위: `supabase/migrations/`를 timestamp 오름차순으로 적용한다.
- 보상: `database/rollbacks/`를 timestamp 역순으로 실행하며 disposable local DB에만 쓴다.
- 논리 투영: `database/schema-v1.draft.sql`은 7 enum·8 table·5 index를 읽기 쉽게 보여주는
  참고본일 뿐 직접 실행하지 않는다.
- 공식 seed 권위: 아직 비어 있다. DATA-001 PM 승인 19/3/10 projection과 DATA-SEED written
  specification은 완료됐지만 실행계획 승인 전 release/seed/import는 금지된다.

Forward migration과 matching compensation은 각각 6개다. 적용·commit된 migration은
수정하지 않고 보정이 필요하면 새 reviewed forward migration을 추가한다. 현재 local 전체
보상 순서는 `00600 → 00500 → 00400 → 00300 → 00200 → 00100`이며, 이어
`database/verify_db001_absent.sql`로 DB-001 객체 부재를 증명한다.

## 로컬 실행과 검증 — patched repository gate만 허용

Q-SEC-004=A와 Q-SEC-005=A의 Docker Desktop 보정만으로는 IPv6 wildcard가 남았고,
Q-SEC-006=A/D-031과 Q-TOOL-001=A/D-032에서 official v2.109.1 source의 local DB HostIP만
고정한 project-local patched CLI, short checkout/path-budget, patched-only runner를 구현했다.
DB 검증은 아래 repository command만 사용한다. stock/bare `supabase db start/reset`, remote push와
다른 DB/volume 조작은 지원하지 않는다.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap_supabase.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify_database.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify_database.ps1 -SkipStart
```

첫 DB gate는 pinned Supabase CLI `2.109.1`을 runner가 고정 loopback network로 시작하고 actual
single `127.0.0.1:54322`를 검증한다. 이후에만 reset, login rotation, pgTAP, 6단계 보상,
부재 확인, reset/replay,
pgTAP, 실제 backend integration을 순서대로 수행한다. `-SkipStart`는 이미 실행 중인 local
DB를 재사용할 때만 쓴다. `-SkipRollbackReplay`는 진단 옵션이며 완료 증거가 아니다.

Docker Desktop의 `local-only-port-binding` 설정은 유지하지만 완료 근거가 아니다. 완료 근거는
patched runner가 actual container에 exact one `127.0.0.1:54322` binding을 확인한 결과다.
bare/direct `db start`로 우회하지 않는다.

필요할 때 local login만 별도로 회전하려면 관리자 DSN을 값이 노출되지 않는 process
environment의 `SEJONG_ADMIN_DATABASE_URL`에 넣고 다음을 실행한다.

```powershell
apps/api/.venv/Scripts/python.exe -B scripts/provision_local_database_login.py
```

스크립트는 ignored `apps/api/.env`의 `DATABASE_URL` 한 줄만 원자적으로 갱신하고 다른
provider 설정은 보존한다. DSN, password, status 원문을 문서·로그·shell history에 남기지
않는다.

선택적 종료는 다음과 같다. Docker volume 삭제·prune은 하지 않는다.

```powershell
.\.tools\supabase\v2.109.1\supabase.exe stop
```

## 데이터와 readiness

`supabase/seed.sql`은 현재 의도적으로 data-free다. PM은 DATA-001의 35개 disposition과 initial
19/3/10 projection을 승인했지만 DATA-SEED 실행계획 승인·release/import actual gate 전이므로
공식/mock persistent row는 0이고 `/ready=503`이 정상이다. DB migration이나 향후 seed 성공만으로
`/ready=200`으로 바꾸지 않으며 READY-001이 별도로 소유한다.

현재 근거는 [ADR-0008](../docs/adr/0008-supabase-cli-sql-migrations.md),
[ADR-0011](../docs/adr/0011-layered-database-and-backend-enforcement.md),
[ADR-0012](../docs/adr/0012-deferred-active-question-trigger-execution.md),
[승인된 설계](../docs/superpowers/specs/2026-07-16-db-001-layered-enforcement-design.md),
[차단된 실행계획](../docs/superpowers/plans/2026-07-16-db-001-layered-enforcement.md),
[local baseline candidate report](../docs/test-reports/DB-001-LOCAL-BASELINE.md)다.
