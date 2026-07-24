# Database

## 권위와 현재 상태

- 실행 권위: `supabase/migrations/`의 timestamp 순서 SQL 9개
- rollback: `database/rollbacks/`의 대응 SQL 9개
- 검증: `supabase/tests/database/`의 pgTAP 9개
- 논리 참고 projection: `database/schema-v1.draft.sql`
- 현재 schema 버전: `0.4.0-local`

시민 read는 `ACTIVE + OFFICIAL` KB와 `OFFICIAL` 기관만 반환합니다. 업무 table은
`app_private`에 두고 브라우저·`PUBLIC`·`anon`·`authenticated`가 직접 접근하지 못하게 합니다.
후보 승인, 자기 승인 차단, idempotency와 감사 metadata는 DB와 backend가 이중 검증합니다.

## fresh local 검증

Docker Desktop과 짧은 checkout 경로가 필요합니다. `.tools/`는 commit하지 않으므로 fresh
clone에서는 patched CLI를 먼저 재현합니다.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File scripts/bootstrap_patched_supabase.ps1 -Install
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File scripts/bootstrap_patched_supabase.ps1 -VerifyOnly
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File scripts/verify_database.ps1
```

`verify_database.ps1`은 pinned patched CLI, exact loopback binding, migration, pgTAP,
9단계 rollback/absence/reset/replay, local login과 backend integration을 검증합니다.
`-SkipStart`는 동일한 검증된 local stack이 이미 실행 중일 때만 사용합니다.

## 정식 seed

`supabase/config.toml`의 `[db.seed].enabled=false`는 의도된 설정입니다. migration reset만으로
공식 데이터가 준비됐다고 판단하지 않습니다.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File scripts/verify_data_seed.ps1 -ReleaseVersion 0.1.0-initial.2
```

성공 projection은 ACTIVE KB 19, 공식 기관 3, 승인 매핑 10입니다. 별도 승인 흐름이
`KB-WASTE-03`을 20번째 ACTIVE로 만들며 immutable release 파일 자체는 바꾸지 않습니다.

## 안전 경계와 종료

- stock/PATH Supabase CLI, `db push`, linked remote project, Docker volume prune은 사용하지 않습니다.
- DSN·password·status 원문을 terminal, 문서와 Git에 남기지 않습니다.
- local stack 종료:

```powershell
.\.tools\supabase\v2.109.1-sejong-loopback\supabase.exe stop
```

이 기준선은 local/private 재현 증거이며 public DB, backup 또는 production readiness가 아닙니다.
