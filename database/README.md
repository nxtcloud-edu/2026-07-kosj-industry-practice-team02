# Database

DB-001의 manifest 의미 버전은 아직 `0.2.0-draft`다. 이 디렉터리의 논리 shape는
`0.3.0-local` 후보지만 Docker actual loopback/full gate 전에는 local 기준선이나
production/public readiness를 뜻하지 않는다.
A-021/Q-SEC-003이 해결되기 전에는 remote/public 배포, public admin/API, public backend DB
credential 사용이 금지된다. 답변이 없을 때의 현재 기본값은 Q-SEC-003 선택지 B이며
`00700` migration은 만들지 않는다.

## 권위와 계보

- 실행 권위: `supabase/migrations/`를 timestamp 오름차순으로 적용한다.
- 보상: `database/rollbacks/`를 timestamp 역순으로 실행하며 disposable local DB에만 쓴다.
- 논리 투영: `database/schema-v1.draft.sql`은 7 enum·8 table·5 index를 읽기 쉽게 보여주는
  참고본일 뿐 직접 실행하지 않는다.
- 공식 seed 권위: 아직 비어 있다. DATA-SEED-001은 PM 승인 DATA-001에 계속 의존한다.

Forward migration과 matching compensation은 각각 6개다. 적용·commit된 migration은
수정하지 않고 보정이 필요하면 새 reviewed forward migration을 추가한다. 현재 local 전체
보상 순서는 `00600 → 00500 → 00400 → 00300 → 00200 → 00100`이며, 이어
`database/verify_db001_absent.sql`로 DB-001 객체 부재를 증명한다.

## 로컬 실행과 검증 — 현재 DB 명령 차단

현재는 Q-SEC-004=A와 Q-SEC-005=A의 두 Docker Desktop 보정 뒤에도 IPv6 wildcard가 남아
Q-SEC-006/A-024가 해결되지 않았으므로
`verify_database.ps1`과 direct DB start/reset을 실행하지 않는다. 아래는 인간 결정과 Docker
restart/recreate 뒤 재개할 때만 쓰는 명령이다.

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

현재 host는 `default-local-port-binding`과 `local-only-port-binding` 모두 `127.0.0.1`+`::`로
판정돼 Q-SEC-006/A-024 해결 전 fail-closed 상태다. bare/direct
`db start`로 우회하지 않는다.

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

`supabase/seed.sql`은 의도적으로 data-free다. 공식/mock persistent row는 0이며 PM이
2026-07-20 목표로 공식 KB·기관 데이터를 전수 승인하기 전에는 `/ready=503`이 정상이다.
DB migration 성공만으로 `/ready=200`으로 바꾸지 않는다.

현재 근거는 [ADR-0008](../docs/adr/0008-supabase-cli-sql-migrations.md),
[ADR-0011](../docs/adr/0011-layered-database-and-backend-enforcement.md),
[ADR-0012](../docs/adr/0012-deferred-active-question-trigger-execution.md),
[승인된 설계](../docs/superpowers/specs/2026-07-16-db-001-layered-enforcement-design.md),
[차단된 실행계획](../docs/superpowers/plans/2026-07-16-db-001-layered-enforcement.md),
[local baseline candidate report](../docs/test-reports/DB-001-LOCAL-BASELINE.md)다.
